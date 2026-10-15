import base64
from datetime import datetime
import os
import sqlite3
import uuid

from flask import Flask, redirect, render_template, request, session, url_for, jsonify
from werkzeug.security import generate_password_hash, check_password_hash

from database import init_db, get_db
from camera import save_captured_photo, capture_photo
from monitoring.face_monitor import detect_face, close_open_face_event
from monitoring.face_logger import log_face_state
from monitoring import event_detector
from monitoring.integrity_score import compute_integrity_score
from monitoring.incident_logger import create_incident
from monitoring.alert_manager import create_alert, create_risk_alert
from monitoring.ai_repor_manager import save_ai_report, get_ai_report
from monitoring.evidence_manager import save_evidence, verify_evidence as check_evidence_integrity
from monitoring.reviewer_manager import get_session_summary
from ai.integrity_agent import generate_real_integrity_report
from questions import EXAM_QUESTIONS, QUESTION_KEY_MAP


LOGIN_TEMPLATE = "login.html"
REGISTER_TEMPLATE = "register.html"

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "examguard-secret-key")

# Initialize database tables
init_db()


# ------------------------------------------------
# HOME
# ------------------------------------------------
@app.route("/")
def home():
    if "candidate_id" in session:
        return redirect(url_for("dashboard"))
    return redirect(url_for("register"))


# ------------------------------------------------
# CAPTURE PHOTO (webcam AJAX call from register.html)
# ------------------------------------------------
@app.route("/capture-photo", methods=["POST"])
def capture_candidate_photo():
    photo = request.files.get("photo")

    if not photo:
        return {"success": False, "message": "No photo received"}, 400

    image_data = photo.read()
    photo_path = save_captured_photo(image_data)

    if not photo_path:
        return {"success": False, "message": "Could not process photo"}, 400

    session["captured_photo"] = photo_path
    session["capture_photo"] = photo_path

    return {
        "success": True,
        "message": "Photo captured successfully",
        "photo_path": photo_path,
    }, 200


# ------------------------------------------------
# REGISTER
# ------------------------------------------------
@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        name = (request.form.get("name") or request.form.get("username") or "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")

        if not name or not email or not password:
            return render_template(
                REGISTER_TEMPLATE,
                error="Please fill in every field."
            )

        # Photo must already be captured via /capture-photo (webcam AJAX flow)
        photo_path = (
            session.get("captured_photo")
            or session.get("capture_photo")
            or request.form.get("photo_path", "").strip()
        )

        if not photo_path:
            return render_template(
                REGISTER_TEMPLATE,
                error="Please capture your photo before registering."
            )

        hashed_password = generate_password_hash(password)
        connection = get_db()

        try:
            connection.execute("""
                INSERT INTO candidates (name, email, password, photo, created_at)
                VALUES (?, ?, ?, ?, ?)
            """, (name, email, hashed_password, photo_path, datetime.now().isoformat()))

            connection.commit()

            session.pop("captured_photo", None)
            session.pop("capture_photo", None)

            return redirect(url_for("login", registered=1))

        except sqlite3.IntegrityError:
            connection.rollback()
            return render_template(
                REGISTER_TEMPLATE,
                error="An account with this email already exists."
            )

        except Exception as e:
            connection.rollback()
            return render_template(
                REGISTER_TEMPLATE,
                error=f"Registration failed: {e}"
            )

        finally:
            connection.close()

    return render_template(REGISTER_TEMPLATE)


# ------------------------------------------------
# LOGIN
# ------------------------------------------------
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")

        if not email or not password:
            return render_template(LOGIN_TEMPLATE, error="Please enter both email and password.")

        connection = get_db()

        try:
            candidate = connection.execute("""
                SELECT * FROM candidates WHERE email = ?
            """, (email,)).fetchone()

            if candidate and check_password_hash(candidate["password"], password):
                session["candidate_id"] = candidate["id"]
                session["candidate_name"] = candidate["name"]
                return redirect(url_for("dashboard"))

            return render_template(LOGIN_TEMPLATE, error="Invalid email or password.")

        finally:
            connection.close()

    registered = request.args.get("registered")
    return render_template(LOGIN_TEMPLATE, registered=registered)


# ------------------------------------------------
# DASHBOARD
# ------------------------------------------------
@app.route("/dashboard")
def dashboard():
    if "candidate_id" not in session:
        return redirect(url_for("login"))

    candidate_id = session["candidate_id"]
    connection = get_db()

    try:
        candidate = connection.execute("""
            SELECT * FROM candidates WHERE id = ?
        """, (candidate_id,)).fetchone()

        if not candidate:
            session.clear()
            return redirect(url_for("login"))

        recent_sessions = connection.execute("""
            SELECT session_id, status, started_at, submitted_at
            FROM exam_sessions
            WHERE candidate_id = ?
            ORDER BY started_at DESC
            LIMIT 5
        """, (candidate_id,)).fetchall()

        recent_attempts = []
        try:
            attempt_rows = connection.execute("""
                SELECT session_id, COUNT(*) as answered_count, SUM(is_correct) as correct_count, MAX(submitted_at) as last_time
                FROM exam_answers
                WHERE candidate_id = ?
                GROUP BY session_id
                ORDER BY last_time DESC
                LIMIT 5
            """, (candidate_id,)).fetchall()
            for r in attempt_rows:
                recent_attempts.append(dict(r))
        except Exception:
            pass

        return render_template(
            "dashboard.html",
            candidate=candidate,
            candidate_name=candidate["name"],
            candidate_email=candidate["email"],
            candidate_photo=candidate["photo"],
            candidate_joined=candidate["created_at"],
            total_questions=len(EXAM_QUESTIONS),
            exam_duration_mins=30,
            recent_sessions=recent_sessions,
            recent_attempts=recent_attempts,
        )

    finally:
        connection.close()


# ------------------------------------------------
# LOGOUT
# ------------------------------------------------
@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


# ------------------------------------------------
# START EXAM
# ------------------------------------------------
@app.route("/start-exam", methods=["GET", "POST"])
def start_exam():
    if "candidate_id" not in session:
        return redirect(url_for("login"))

    candidate_id = session["candidate_id"]
    connection = get_db()

    try:
        row = connection.execute("""
            SELECT session_id FROM exam_sessions
            WHERE candidate_id = ? AND status IN ('in_progress', 'paused')
            ORDER BY started_at DESC LIMIT 1
        """, (candidate_id,)).fetchone()

        if row:
            exam_session_id = row["session_id"]
        else:
            exam_session_id = str(uuid.uuid4())
            connection.execute("""
                INSERT INTO exam_sessions (candidate_id, session_id, status, started_at)
                VALUES (?, ?, 'in_progress', ?)
            """, (candidate_id, exam_session_id, datetime.now().isoformat()))
            connection.commit()

        session["exam_session_id"] = exam_session_id
        session["exam_answers"] = session.get("exam_answers", {})

    finally:
        connection.close()

    return render_template(
        "exam.html",
        candidate_name=session.get("candidate_name"),
        exam_session_id=exam_session_id,
        questions=EXAM_QUESTIONS,
        total_questions=len(EXAM_QUESTIONS),
    )


# ------------------------------------------------
# SAVE ANSWER
# ------------------------------------------------
@app.route("/save-answer", methods=["POST"])
def save_answer():
    if "candidate_id" not in session:
        return {"success": False, "message": "Candidate is not logged in"}, 401

    exam_session_id = session.get("exam_session_id")
    if not exam_session_id:
        return {"success": False, "message": "Exam not started"}, 400

    data = request.get_json(silent=True) or {}
    question_id = data.get("question_id")
    selected_option = data.get("selected_option")

    if question_id is None or selected_option is None:
        return {"success": False, "message": "Missing question_id or selected_option"}, 400

    answers = session.get("exam_answers", {})
    answers[str(question_id)] = selected_option
    session["exam_answers"] = answers

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
            datetime.now().isoformat(),
        ))
        connection.commit()
        connection.close()
    except Exception as e:
        print(f"Error saving exam answer: {e}")

    return {
        "success": True,
        "message": f"Question {question_id} answer saved",
        "question_id": question_id,
        "selected_option": selected_option,
    }, 200


# ------------------------------------------------
# PAUSE / RESUME EXAM (session lifecycle)
# ------------------------------------------------
@app.route("/pause-exam", methods=["POST"])
def pause_exam():
    if "candidate_id" not in session or "exam_session_id" not in session:
        return {"success": False, "message": "No active exam session"}, 400

    connection = get_db()
    try:
        connection.execute("""
            UPDATE exam_sessions
            SET status = 'paused', paused_at = ?
            WHERE session_id = ?
        """, (datetime.now().isoformat(), session["exam_session_id"]))
        connection.commit()
    finally:
        connection.close()

    return {"success": True, "message": "Exam paused"}


@app.route("/resume-exam", methods=["POST"])
def resume_exam():
    if "candidate_id" not in session or "exam_session_id" not in session:
        return {"success": False, "message": "No active exam session"}, 400

    connection = get_db()
    try:
        connection.execute("""
            UPDATE exam_sessions
            SET status = 'in_progress', resumed_at = ?
            WHERE session_id = ?
        """, (datetime.now().isoformat(), session["exam_session_id"]))
        connection.commit()
    finally:
        connection.close()

    return {"success": True, "message": "Exam resumed"}


# ------------------------------------------------
# SUBMIT EXAM
# ------------------------------------------------
@app.route("/submit-exam", methods=["POST"])
def submit_exam():
    # --------------------------------------------------
    # 1. Check candidate login and active exam session
    # --------------------------------------------------
    if "candidate_id" not in session or "exam_session_id" not in session:
        return {
            "success": False,
            "message": "No active exam session"
        }, 400

    candidate_id = session["candidate_id"]
    exam_session_id = session["exam_session_id"]

    # --------------------------------------------------
    # 2. Score candidate's exam answers
    # --------------------------------------------------
    data = request.get_json(silent=True) or {}
    answers = data.get("answers") or session.get("exam_answers", {})

    score = 0
    for q in EXAM_QUESTIONS:
        qid_str = str(q["id"])
        if answers.get(qid_str) == q["correct"]:
            score += 1

    total_questions = len(EXAM_QUESTIONS)
    percentage = round((score / total_questions) * 100, 1) if total_questions > 0 else 0.0

    # --------------------------------------------------
    # 3. Record exam submission time & event
    # --------------------------------------------------
    submitted_at = datetime.now().isoformat()
    connection = get_db()

    try:
        connection.execute("""
            UPDATE exam_sessions
            SET
                status = 'submitted',
                submitted_at = ?
            WHERE session_id = ?
            AND candidate_id = ?
        """, (
            submitted_at,
            exam_session_id,
            candidate_id
        ))

        connection.execute("""
            INSERT INTO browser_events
                (candidate_id, session_id, event_type, event_time, details)
            VALUES (?, ?, ?, ?, ?)
        """, (
            candidate_id,
            exam_session_id,
            "exam_completed",
            submitted_at,
            f"Exam submitted. Score: {score}/{total_questions}"
        ))

        connection.commit()

    except Exception as e:
        connection.rollback()
        return {
            "success": False,
            "message": str(e)
        }, 500

    finally:
        connection.close()

    # --------------------------------------------------
    # 4. Close the final open face event
    # --------------------------------------------------
    close_open_face_event(
        candidate_id,
        exam_session_id
    )

    # --------------------------------------------------
    # 5. Calculate final integrity score
    # --------------------------------------------------
    result = compute_integrity_score(
        candidate_id,
        exam_session_id
    )

    # --------------------------------------------------
    # 6. Connect alert to integrity score
    # --------------------------------------------------
    create_risk_alert(
        candidate_id=candidate_id,
        session_id=exam_session_id,
        risk_level=result["risk_level"],
        integrity_score=result["integrity_score"]
    )

    # --------------------------------------------------
    # 7. Generate integrity report using AI agent
    # --------------------------------------------------
    try:
        report = generate_real_integrity_report(
            candidate_id,
            exam_session_id
        )

        save_report_result = save_ai_report(
            candidate_id=candidate_id,
            session_id=exam_session_id,
            report=report
        )

        print("AI-Generated Integrity Report:")
        print(report)
        print("Report saved in database with ID:", save_report_result.get("id"))
    except Exception as ai_err:
        print(f"Notice: AI report generation skipped or encountered an error: {ai_err}")

    # --------------------------------------------------
    # 8. Remove active exam session
    # --------------------------------------------------
    session.pop("exam_session_id", None)
    session.pop("exam_answers", None)

    # --------------------------------------------------
    # 9. Return final result
    # --------------------------------------------------
    return {
        "success": True,
        "message": "Exam submitted successfully",
        "score": score,
        "total": total_questions,
        "percentage": percentage,
        "integrity_score": result["integrity_score"],
        "face_presence_ratio": result["face_presence_ratio"],
        "event_penalty": result["event_penalty"],
        "risk_level": result["risk_level"],
        "redirect": url_for("dashboard")
    }


# ------------------------------------------------
# FACE MONITORING (webcam frame -> OpenCV Haar Cascade)
# ------------------------------------------------
@app.route("/monitor-face", methods=["POST"])
def monitor_face():
    if "candidate_id" not in session:
        return {"success": False, "message": "Candidate not logged in"}, 401

    candidate_id = session["candidate_id"]
    exam_session_id = session.get("exam_session_id")

    if not exam_session_id:
        return {"success": False, "message": "Exam session not started"}, 400

    image = request.files.get("frame") or request.files.get("image")

    if not image:
        return {"success": False, "message": "No frame received"}, 400

    image_data = image.read()

    detect_res = detect_face(image_data)
    face_present = detect_res[0] if isinstance(detect_res, tuple) else bool(detect_res)
    current_state = "face_detected" if face_present else "face_absent"

    log_face_state(candidate_id, exam_session_id, current_state)

    return {"success": True, "state": current_state}


# ------------------------------------------------
# BROWSER EVENT LOGGING + RULE-BASED DETECTION
# ------------------------------------------------
@app.route("/log-browser-event", methods=["POST"])
def log_browser_event():
    if "candidate_id" not in session:
        return {"success": False, "message": "Candidate not logged in"}, 401

    candidate_id = session["candidate_id"]
    exam_session_id = session.get("exam_session_id")

    if not exam_session_id:
        return {"success": False, "message": "Exam session not started"}, 400

    data = request.get_json(silent=True)

    if not data:
        return {"success": False, "message": "No event data received"}, 400

    event_type = data.get("event_type") or data.get("event")
    details = data.get("details", "")

    if not event_type:
        return {"success": False, "message": "Event type is required"}, 400

    connection = get_db()
    screenshot_required = False

    try:
        connection.execute("""
            INSERT INTO browser_events
                (candidate_id, session_id, event_type, event_time, details)
            VALUES (?, ?, ?, ?, ?)
        """, (
            candidate_id,
            exam_session_id,
            event_type,
            datetime.now().isoformat(),
            details,
        ))

        connection.commit()

        print("================================")
        print("BROWSER EVENT RECEIVED")
        print("candidate_id:", candidate_id)
        print("session_id:", exam_session_id)
        print("event_type:", event_type)
        print("details:", details)
        print("================================")

        # Run the rule-based suspicious event detection engine
        rule_results = event_detector.evaluate_browser_event(
            connection, candidate_id, exam_session_id, event_type
        )

        print("rule_results:", rule_results)

        if rule_results:
            create_incident(
                candidate_id=candidate_id,
                session_id=exam_session_id,
                event_type=rule_results["event_type"],
                description=rule_results["reason"],
                severity=rule_results["severity"]
            )
            create_alert(
                candidate_id=candidate_id,
                session_id=exam_session_id,
                alert_type=rule_results["event_type"],
                message=rule_results["reason"],
                severity=rule_results["severity"]
            )
            screenshot_required = True

    except Exception as e:
        connection.rollback()
        return {"success": False, "message": str(e)}, 500

    finally:
        connection.close()

    return {
        "success": True,
        "message": "Browser event saved",
        "screenshot_required": screenshot_required
    }


# ------------------------------------------------
# UPLOAD EVIDENCE (Screenshot on suspicious alert)
# ------------------------------------------------
@app.route("/upload-evidence", methods=["POST"])
def upload_evidence():
    if "candidate_id" not in session or "exam_session_id" not in session:
        return {
            "success": False,
            "message": "No active exam session"
        }, 400

    data = request.get_json(silent=True)
    if not data:
        return {
            "success": False,
            "message": "No evidence data received"
        }, 400

    image_data = data.get("image")
    if not image_data:
        return {
            "success": False,
            "message": "Screenshot is required"
        }, 400

    try:
        if "," in image_data:
            image_data = image_data.split(",", 1)[1]

        file_data = base64.b64decode(image_data)
        if not file_data:
            return {
                "success": False,
                "message": "Screenshot data is empty"
            }, 400

        result = save_evidence(
            candidate_id=session["candidate_id"],
            session_id=session["exam_session_id"],
            evidence_type="screenshot",
            filename="suspicious_event.jpg",
            mime_type="image/jpeg",
            file_data=file_data
        )

        return {
            "success": True,
            "message": "Screenshot evidence saved",
            "sha256_hash": result["sha256_hash"]
        }

    except Exception as e:
        return {
            "success": False,
            "message": str(e)
        }, 500


# ------------------------------------------------
# VERIFY EVIDENCE
# ------------------------------------------------
@app.route("/verify-evidence/<int:evidence_id>", methods=["GET"])
def verify_evidence(evidence_id):
    if "candidate_id" not in session and "reviewer_id" not in session:
        return {"success": False, "message": "Authentication required"}, 401

    results = check_evidence_integrity(evidence_id)
    if not results.get("success") or results.get("message") == "Evidence is invalid":
        return {
            "success": False,
            "message": "Evidence is invalid"
        }, 400

    return {
        "success": True,
        "message": "Evidence is valid",
        "evidence_id": results["evidence_id"],
        "stored_hash": results["stored_hash"],
        "calculated_hash": results["calculated_hash"]
    }, 200


# ------------------------------------------------
# AI INTEGRITY REPORT
# ------------------------------------------------
@app.route("/ai-report/<int:candidate_id>/<session_id>", methods=["GET"])
def ai_report(candidate_id, session_id):
    result = get_ai_report(
        candidate_id,
        session_id
    )

    if result is None:
        return {
            "success": False,
            "message": "AI report not found"
        }, 404

    return {
        "success": True,
        "report": result
    }


# ------------------------------------------------
# REVIEWER SESSION SUMMARY
# ------------------------------------------------
@app.route("/reviewer/session/<int:candidate_id>/<session_id>")
def reviewer_session(candidate_id, session_id):
    # Reviewer or candidate verification
    if (
        "reviewer_id" not in session
        and "candidate_id" not in session
        and not request.args.get("reviewer")
    ):
        return {
            "success": False,
            "message": "Reviewer login required"
        }, 401

    summary = get_session_summary(
        candidate_id,
        session_id
    )

    if summary is None:
        return {
            "success": False,
            "message": "Session summary not found"
        }, 404

    return render_template(
        "reviewer_session.html",
        summary=summary
    )


# ------------------------------------------------
# RUN FLASK
# ------------------------------------------------
if __name__ == "__main__":
    app.run(debug=True)
