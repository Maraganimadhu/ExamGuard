from werkzeug.security import check_password_hash
from flask import session
from flask import Flask, render_template, request  # This line imports the Flask class and the request object from the flask module. The Flask class is used to create a Flask application instance, while the request object is used to handle incoming HTTP requests.
from database import init_db ,get_db
from werkzeug.security import generate_password_hash

app =Flask(__name__)
# it's create flask application instance and assign it to the variable app. The __name__ argument is used to determine the root path of the application, which is necessary for locating resources such as templates and static files.

@app.route('/')   #   @ is decerator in python. It is used to modify the function below it. In this case, it is used to associate the home() function with the root URL of the application.
def home():
    return "WELCOME TO EXAM_GUARD!"  # This function returns the string "Hello, World!" when the root URL is accessed.



@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        # print("name:", username)
        # print("email:", email)
        # print("password:", password)

        connection=get_db()
        connection.execute(
            """
            INSERT INTO candidates(name,email,password)
            values(?,?,?)""",(username,email,generate_password_hash(password))
            )
        connection.commit()
        connection.close()
        print("registstion successful")

        return render_template('register.html', success=True, username=username)

    return render_template('register.html')



@app.route('/login', methods=['GET','POST'])
def login():
    if request.method=="POST":
        email=request.form.get('email')
        password=request.form.get('password')

        connection=get_db()
        cursor=connection.cursor()
        cursor.execute("""
        SELECT 
        * from 
        candidates 
        where email=? """,(email,))
        user=cursor.fetchone()
        # print(cursor)
        if user and check_password_hash(user[3],password):
            # print("scussful to login")
            session['candidate_id']=user[0]
            return render_template("dashboard.html",success=True,email=email)
        else:
            # print(" try again")
            return render_template("login.html",success=False,error="Invalid")
        
    return render_template('login.html')
    
@app.route("/dashboard")
def dashboard():
    return "welcome to dashboard"






if __name__ == '__main__':
    init_db()
    app.run(debug=True)  # This line checks if the script is being run directly (not imported as a module). If it is, it starts the Flask development server with debug mode enabled, which provides detailed error messages and auto-reloads the server on code changes.

    


