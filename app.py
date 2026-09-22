from Monitering.face_logger import log_face_state
from Monitering.face_monitoring import detect_face
import os
from flask import Flask, render_template, request, redirect, url_for, session, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from database import init_db, get_db
from cemara import capture_photo
from questions import EXAM_QUESTIONS, QUESTION_KEY_MAP
import uuid
from datetime import datetime

LOGIN_TEMPLATE = "login.html"
REGISTER_TEMPLATE = "register.html"

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'examguard_super_secret_key_2026')
upload_folder = "static/uploads"


@app.route("/capture-photo", methods=["POST"])
def capture_candidate_photo():
    photo = request.files.get("photo")
    if not photo:
        return {
            "success": "False",
            "message": "photo not received"
        }, 400
    image_data = photo.read()
    photo_path = capture_photo(image_data)
    if not photo_path:
        return {
            "success": "False",
            "message": "could not process photo"
        }, 400
    session["capture_photo"] = photo_path
    return {
        "success": "True",
        "message": "photo captured successfully",
        "photo_path": photo_path
    }, 200


@app.route('/', methods=['GET'])
def home():
    return render_template(REGISTER_TEMPLATE)


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = (request.form.get('username') or request.form.get('name') or '').strip()
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '').strip()
        # Photo is captured and uploaded via fetch to /capture-photo which saves path in session
        photo_path = session.get('capture_photo') or request.form.get('photo_path', '').strip()

        if not username or not email or not password:
            return render_template(REGISTER_TEMPLATE, error="Please fill in all required fields.")

        if not photo_path:
            return render_template(REGISTER_TEMPLATE, error="Please capture your photo.")

        connection = get_db()
        cursor = connection.cursor()
        
        # Check if email is already registered
        cursor.execute("SELECT id FROM candidates WHERE email = ?", (email,))
        if cursor.fetchone():
            connection.close()
            return render_template(REGISTER_TEMPLATE, error="An account with this email already exists.")

        cursor.execute(
            """
            INSERT INTO candidates(name, email, password, photo)
            VALUES(?, ?, ?, ?)
            """,
            (username, email, generate_password_hash(password), photo_path)
        )
        connection.commit()
        connection.close()
        
        # Clear the photo path from session after successful registration
        session.pop('capture_photo', None)

        return render_template(REGISTER_TEMPLATE, success=True, username=username)

    return redirect(url_for('login'))


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == "POST":
        email = request.form.get('email')
        password = request.form.get('password')

        if not email or not password:
            return render_template(LOGIN_TEMPLATE, error="Please enter both email and password.")

        connection = get_db()
        cursor = connection.cursor()
        cursor.execute(
            """
            SELECT * FROM candidates 
            WHERE email = ?
            """,
            (email,)
        )
        candidate = cursor.fetchone()
        connection.close()

        if candidate and check_password_hash(candidate[3], password):
            session['candidate_id'] = candidate[0]
            session['candidate_name'] = candidate[1]
            return redirect(url_for('dashboard'))
        else:
            return render_template(LOGIN_TEMPLATE, error="Invalid username or password. Please verify and try again.")

    return render_template(LOGIN_TEMPLATE)


@app.route("/dashboard", methods=["GET"])
def dashboard():
    if 'candidate_id' not in session:
        return render_template(LOGIN_TEMPLATE, error="Please login first.")
       
    candidate_id = session['candidate_id']
    candidate = None
    recent_attempts = []

    try:
        connection = get_db()
        cursor = connection.cursor()
        cursor.execute("SELECT id, name, email, photo, created_at FROM candidates WHERE id = ?", (candidate_id,))
        cand_row = cursor.fetchone()
        if cand_row:
            candidate = dict(cand_row)

        cursor.execute("""
            SELECT session_id, COUNT(*) as answered_count, SUM(is_correct) as correct_count, MAX(submitted_at) as last_time
            FROM exam_answers
            WHERE candidate_id = ?
            GROUP BY session_id
            ORDER BY last_time DESC
            LIMIT 5
        """, (candidate_id,))
        rows = cursor.fetchall()
        for r in rows:
            recent_attempts.append(dict(r))

        connection.close()
    except Exception as e:
        print(f"Error fetching dashboard candidate data: {e}")

    candidate_name = candidate['name'] if candidate and candidate.get('name') else session.get('candidate_name', 'Candidate')
    candidate_email = candidate['email'] if candidate and candidate.get('email') else ''
    candidate_photo = candidate['photo'] if candidate and candidate.get('photo') else ''
    candidate_joined = candidate['created_at'] if candidate and candidate.get('created_at') else None

    return render_template(
        "dashboard.html",
        success=True,
        candidate=candidate,
        candidate_name=candidate_name,
        candidate_email=candidate_email,
        candidate_photo=candidate_photo,
        candidate_joined=candidate_joined,
        total_questions=len(EXAM_QUESTIONS),
        exam_duration_mins=30,
        recent_attempts=recent_attempts
    )




# ----------------------------------------
# EXAMINATION ROUTES
# ----------------------------------------



@app.route("/start-exam")
def start_exam():
    # ----------------------------------------
    # CHECK LOGIN
    # ----------------------------------------
    if "candidate_id" not in session:
        return redirect(url_for('login'))

    # ----------------------------------------
    # CREATE UNIQUE EXAM SESSION
    # ----------------------------------------
    exam_session_id = str(uuid.uuid4())
    session["exam_session_id"] = exam_session_id
    session["exam_answers"] = {}

    # ----------------------------------------
    # OPEN EXAM PAGE
    # ----------------------------------------
    return render_template(
        "exam.html",
        candidate_name=session.get("candidate_name", "Candidate"),
        exam_session_id=exam_session_id,
        questions=EXAM_QUESTIONS,
        total_questions=len(EXAM_QUESTIONS)
    )


@app.route("/save-answer", methods=["POST"])
def save_answer():
    if "candidate_id" not in session:
        return {"success": False, "message": "Candidate is not logged in"}, 401
    exam_session_id = session.get("exam_session_id")
    if not exam_session_id:
        return {"success": False, "message": "Exam not started"}, 400

    data = request.get_json() or {}
    question_id = data.get("question_id")
    selected_option = data.get("selected_option")

    if question_id is None or selected_option is None:
        return {"success": False, "message": "Missing question_id or selected_option"}, 400

    answers = session.get("exam_answers", {})
    answers[str(question_id)] = selected_option
    session["exam_answers"] = answers

    # Save to database
    try:
        connection = get_db()
        is_corr = 1 if selected_option == QUESTION_KEY_MAP.get(int(question_id)) else 0
        connection.execute("""
            INSERT INTO exam_answers (candidate_id, session_id, question_id, selected_option, is_correct, submitted_at)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            session["candidate_id"],
            exam_session_id,
            int(question_id),
            selected_option,
            is_corr,
            datetime.now().isoformat()
        ))
        connection.commit()
        connection.close()
    except Exception:
        pass

    return {
        "success": True,
        "message": f"Question {question_id} answer saved",
        "question_id": question_id,
        "selected_option": selected_option
    }, 200


@app.route("/submit-exam", methods=["POST"])
def submit_exam():
    if "candidate_id" not in session:
        return {"success": False, "message": "Candidate is not logged in"}, 401
    exam_session_id = session.get("exam_session_id")
    if not exam_session_id:
        return {"success": False, "message": "Exam not started"}, 400

    data = request.get_json() or {}
    answers = data.get("answers") or session.get("exam_answers", {})

    score = 0
    for q in EXAM_QUESTIONS:
        qid_str = str(q["id"])
        if answers.get(qid_str) == q["correct"]:
            score += 1

    try:
        connection = get_db()
        connection.execute("""
            INSERT INTO browser_events (candidate_id, session_id, event_type, event_time, details)
            VALUES (?, ?, ?, ?, ?)
        """, (
            session["candidate_id"],
            exam_session_id,
            "exam_completed",
            datetime.now().isoformat(),
            f"Exam submitted. Score: {score}/{len(EXAM_QUESTIONS)}"
        ))
        connection.commit()
        connection.close()
    except Exception:
        pass

    return {
        "success": True,
        "message": "Examination submitted successfully",
        "score": score,
        "total": len(EXAM_QUESTIONS),
        "percentage": round((score / len(EXAM_QUESTIONS)) * 100, 1)
    }, 200


# ----------------------------------------
# MONITOR FACE
# ----------------------------------------
@app.route("/monitor-face", methods=["POST"])
def monitor_face():

    # ----------------------------------------
    # CHECK LOGIN
    # ----------------------------------------
    if "candidate_id" not in session:

        return {
            "success": False,
            "message": "Candidate is not logged in"
        }, 401


    candidate_id = session["candidate_id"]


    # ----------------------------------------
    # GET EXAM SESSION
    # ----------------------------------------
    exam_session_id = session.get(
        "exam_session_id"
    )


    if not exam_session_id:

        return {
            "success": False,
            "message": "Exam not started"
        }, 400


    # ----------------------------------------
    # GET IMAGE FROM BROWSER
    # ----------------------------------------
    image = request.files.get(
        "image"
    )


    if not image:

        return {
            "success": False,
            "message": "No image received"
        }, 400


    # ----------------------------------------
    # READ IMAGE
    # ----------------------------------------
    image_data = image.read()


    # ----------------------------------------
    # DETECT FACE
    # ----------------------------------------
    face_present, processed_image = detect_face(
        image_data
    )


    # ----------------------------------------
    # DETERMINE FACE STATE
    # ----------------------------------------
    if face_present:

        current_state = "face_detected"

    else:

        current_state = "face_absent"


    # ----------------------------------------
    # LOG FACE STATE
    # ----------------------------------------
    log_face_state(
        candidate_id,
        exam_session_id,
        current_state
    )


    # ----------------------------------------
    # RETURN RESULT
    # ----------------------------------------
    return {
        "success": True,
        "state": current_state
    }, 200


@app.route("/log-browser-event", methods=["POST"])
def log_browser_event():
    if "candidate_id" not in session:
    
            return {
                "success": False,
                "message": "Candidate is not logged in"
            }, 401
    
    
    candidate_id = session["candidate_id"]

    exam_session_id = session.get("exam_session_id")
    if not exam_session_id:
        return {
            "success": False,
            "message": "Exam not started"
        }, 400
    data = request.get_json() or {}
    event_type = data.get("event") or data.get("event_type")
    if not event_type:
        return {
            "success": False,
            "message": "No event data received"
        }, 400
    details = data.get("details", "")
    connection=get_db()
    try:

        # Insert browser event
        connection.execute("""
            INSERT INTO browser_events
            (
                candidate_id,
                session_id,
                event_type,
                event_time,
                details
            )
            VALUES (?, ?, ?, ?, ?)
        """, (
            candidate_id,
            exam_session_id,
            event_type,
            datetime.now().isoformat(),
            details
        ))


        # Save changes
        connection.commit()


    except Exception as e:

        connection.rollback()

        return {
            "success": False,
            "message": str(e)
        }, 500


    finally:

        connection.close()


    return {
        "success": True,
        "message": "Browser event saved"
    }



@app.route("/logout", methods=["GET"])
def logout():
    session.clear()
    return redirect(url_for('login'))


if __name__ == '__main__':
    init_db()
    app.run(debug=True)
