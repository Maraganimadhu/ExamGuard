from face_logger import log_face_state
from face_monitoring import detect_face
import os
from flask import Flask, render_template, request, redirect, url_for, session
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from database import init_db, get_db
from cemara import capture_photo
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

    return redirect(login)


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
       
    return render_template("dashboard.html", success=True, candidate_name=session.get('candidate_name'))




@app.route("/start-exam")
def start_exam():

    # ----------------------------------------
    # CHECK LOGIN
    # ----------------------------------------
    if "candidate_id" not in session:

        return {
            "success": False,
            "message": "Candidate is not logged in"
        }, 401


    # ----------------------------------------
    # CREATE UNIQUE EXAM SESSION
    # ----------------------------------------
    exam_session_id = str(
        uuid.uuid4()
    )


    # Store exam session ID
    session["exam_session_id"] = exam_session_id


    # ----------------------------------------
    # OPEN EXAM PAGE
    # ----------------------------------------
    return render_template(
        "exam.html",
        candidate_name=session.get("candidate_name", "Candidate"),
        exam_session_id=exam_session_id
    )


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
