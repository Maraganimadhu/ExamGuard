import os
from werkzeug.security import check_password_hash, generate_password_hash
from flask import Flask, render_template, request, session
from database import init_db, get_db

LOGIN_TEMPLATE = "login.html"
DASHBOARD_TEMPLATE = "dashboard.html"
REGISTER_TEMPLATE = "register.html"

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'examguard_secret_key_change_in_production')


@app.route('/', methods=['GET'])
def home():
    return "WELCOME TO EXAM_GUARD!"


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')

        connection = get_db()
        connection.execute(
            """
            INSERT INTO candidates(name, email, password)
            VALUES (?, ?, ?)
            """,
            (username, email, generate_password_hash(password))
        )
        connection.commit()
        connection.close()

        return render_template(REGISTER_TEMPLATE, success=True, username=username)

    return render_template(REGISTER_TEMPLATE)


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == "POST":
        email = request.form.get('email')
        password = request.form.get('password')

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
            return render_template(DASHBOARD_TEMPLATE, success=True, email=candidate[2], username=candidate[1])
        else:
            error_message = "Invalid username or password. Please verify and try again."
            return render_template(LOGIN_TEMPLATE, success=False, error=error_message)
        
    return render_template(LOGIN_TEMPLATE)


@app.route("/dashboard", methods=["GET"])
def dashboard():
    if 'candidate_id' not in session:
        return render_template(LOGIN_TEMPLATE, error="Please log in first to access the dashboard.")
    return render_template(DASHBOARD_TEMPLATE)


@app.route("/logout", methods=["GET"])
def logout():
    session.clear()
    return render_template(LOGIN_TEMPLATE)


if __name__ == '__main__':
    init_db()
    debug_mode = os.environ.get('FLASK_DEBUG', 'False').lower() in ('true', '1')
    app.run(debug=debug_mode)
