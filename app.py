from werkzeug.security import check_password_hash
from flask import session
from flask import Flask, render_template, request  # This line imports the Flask class and the request object from the flask module. The Flask class is used to create a Flask application instance, while the request object is used to handle incoming HTTP requests.
from database import init_db ,get_db
from werkzeug.security import generate_password_hash

app = Flask(__name__)
app.secret_key = 'examguard_secret_key_change_in_production'

@app.route('/')   #   @ is decorator in python. It is used to associate the home() function with the root URL.
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
        print("Registration successful")

        return render_template('register.html', success=True, username=username)

    return render_template('register.html')


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
            print("Login successful")
            return render_template("dashboard.html", success=True, email=candidate[2], username=candidate[1])
        else:
            error_message = "Invalid username or password. Please verify and try again."
            print(error_message)
            return render_template("login.html", success=False, error=error_message)
        
    return render_template('login.html')
    
@app.route("/dashboard")
def dashboard():
    if 'candidate_id' not in session:
        return render_template("login.html", error="Please log in first to access the dashboard.")
    return render_template("dashboard.html")

@app.route("/logout")
def logout():
    session.clear()
    return render_template("login.html")


if __name__ == '__main__':
    init_db()
    app.run(debug=True)  # This line checks if the script is being run directly (not imported as a module). If it is, it starts the Flask development server with debug mode enabled, which provides detailed error messages and auto-reloads the server on code changes.

    


