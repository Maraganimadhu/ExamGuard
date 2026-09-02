import os
from flask import Flask, render_template, request, redirect, url_for, session
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from database import init_db, get_db
from cemara import capture_photo

LOGIN_TEMPLATE = "login.html"


app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'examguard_super_secret_key_2026')
upload_folder = "static/uploads"




@app.route("/capture-photo", methods=["POST"])
def captureCandidatePhoto():
    photo=request.files.get("photo")
    if not photo:
        return {
            "success":"False",
            "message":"photo not recevied"
            
        },400
    image_data=photo.read()
    photo_path=capture_photo(image_data)
    if not photo_path:
        return {
            "success":"False",
            "message":"coud't process photo"
        },400
    session["capture_photo"]=photo_path
    return {
        "success":"True",
        "message":"photo captured successfully",
        "photo_path":photo_path
    },200


    
    #return render_template("camera.html")


@app.route('/')
def home():
    return render_template(LOGIN_TEMPLATE)


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '').strip()
        photo = request.files.get('candidate_photo')

        if not username or not email or not password:
            return render_template('register.html', error="Please fill in all required fields.")

        if not photo or photo.filename == '':
            return render_template('register.html', error="Please upload your photo.")

        os.makedirs(upload_folder, exist_ok=True)
        filename = secure_filename(photo.filename)
        photo_path = os.path.join(upload_folder, filename)
        photo.save(photo_path)

        connection = get_db()
        cursor = connection.cursor()
        
        # Check if email is already registered
        cursor.execute("SELECT id FROM candidates WHERE email = ?", (email,))
        if cursor.fetchone():
            connection.close()
            return render_template('register.html', error="An account with this email already exists.")

        cursor.execute(
            """
            INSERT INTO candidates(name, email, password, photo)
            VALUES(?, ?, ?, ?)
            """,
            (username, email, generate_password_hash(password), photo_path)
        )
        connection.commit()
        connection.close()
        print("Registration successful for:", username)

        return render_template(REGISTER, success=True, username=username)

    return render_template(REGISTER)


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == "POST":
        email = (request.form.get('email'))
        password = (request.form.get('password'))

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
            return redirect(url_for('dashboard'))
        else:
            return render_template(LOGIN_TEMPLATE, error="Invalid username or password. Please verify and try again.")

    return render_template(LOGIN_TEMPLATE)


@app.route("/dashboard")
def dashboard():
    if 'candidate_id' not in session:
        return render_template(LOGIN_TEMPLATE, error="Please login first.")
       
    return render_template("dashboard.html", success=True, candidate_name=session.get('candidate_name'))


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for('login'))

# 




if __name__ == '__main__':
    init_db()
    app.run(debug=True)  # This line checks if the script is being run directly (not imported as a module). If it is, it starts the Flask development server with debug mode enabled, which provides detailed error messages and auto-reloads the server on code changes.

    


