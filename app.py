from cmath import log
from flask import Flask, flash, redirect, render_template, request, session, url_for
from flask_session import Session
from flask_mysqldb import MySQL
from tempfile import mkdtemp
from werkzeug.security import check_password_hash, generate_password_hash
from datetime import datetime
from functools import wraps
from datetime import datetime
import re
import json

from app_config import data, roles

# Flask instance
app = Flask(__name__)

# Ensure templates are auto-reloaded
app.config['TEMPLATES_AUTO_RELOAD'] = data['TEMPLATES_AUTO_RELOAD']

# flask-mysqldb
app.config['MYSQL_HOST'] = data['MYSQL_HOST']
app.config['MYSQL_USER'] = data['MYSQL_USER']
app.config['MYSQL_PASSWORD'] = data['MYSQL_PASSWORD']
app.config['MYSQL_DB'] = data['MYSQL_DB']
app.config['MYSQL_CURSORCLASS'] = data['MYSQL_CURSORCLASS']
mysql = MySQL(app)

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
app.config['SECRET_KEY'] = data['SECRET_KEY']
Session(app)


# Function decorator to request the user to be logged in
def login_required(f):
    """
    Decorate routes to require login.
    https://flask.palletsprojects.com/en/1.1.x/patterns/viewdecorators/
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get("user_id") is None:
            return redirect("/login")
        return f(*args, **kwargs)
    return decorated_function


# Making sure responses are not cached
@app.after_request
def after_request(response):
    """Ensure responses aren't cached"""
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response


@app.route("/grades", methods=["POST"])
@login_required
def grades():
    """Grading each student's activities"""

    # User is not a teacher
    if session['role'] == 'student':
        return redirect(url_for('index'))
    else:
        
        # User reached before grading a student
        if not request.form.get("activity_grade"):
            with mysql.connection.cursor() as cursor:
                
                # Retrieving students per activity
                cursor.execute(
                    """
                    SELECT
                        users.id,
                        users.fullname,
                        students_activities.submitted,
                        students_activities.grade
                    FROM users
                    INNER JOIN students_activities ON students_activities.student_id=users.id
                    WHERE students_activities.subject_id = %s AND students_activities.activity_id = %s
                    """, [request.form.get("subject_id"), request.form.get("activity_id")])
                students = cursor.fetchall()
                return render_template("teacher_grades.html", students=students, activity_id=request.form.get("activity_id"))
        
        # User graded a student
        else:
            with mysql.connection.cursor() as cursor:
                
                # Updating student's grade on activity
                cursor.execute(
                    """
                    UPDATE students_activities SET grade = %s WHERE student_id = %s AND activity_id = %s
                    """, [
                        request.form.get("activity_grade"),
                        request.form.get("student_id"),
                        request.form.get("activity_id"),
                    ])
                mysql.connection.commit()
                return redirect(url_for('subjects'))


# Main route / Home page
@app.route("/")
@login_required
def index():
    """Home page"""

    # User logged in is an admin
    if session["role"] == "admin":
        with mysql.connection.cursor() as cursor:
            
            # Retrieves all subjects and activities registered
            cursor.execute('SELECT subjects.id, subjects.name, activities.id, activities.title, activities.description, activities.due_date FROM subjects JOIN activities ON subjects.id=activities.subject_id ORDER BY subjects.id')
            
            data = list(cursor.fetchall())
            
            # Formating due dates as strings
            for d in data:
                d['due_date'] = d['due_date'].strftime("%Y/%m/%d %H:%M:%S")

            return render_template("index_admin.html", data=data)
    
    # User logged in is a teacher
    elif session["role"] == "teacher":
        with mysql.connection.cursor() as cursor:
            
            # Retrieving teacher's subjects and activities
            cursor.execute(
                '''
                SELECT subjects.id, subjects.name, activities.id, activities.title, activities.description, activities.due_date
                FROM subjects
                INNER JOIN activities ON subjects.id=activities.subject_id
                WHERE subjects.teacher_id=%s
                ''',
                [session['user_id']])
            
            data = list(cursor.fetchall())
            
            return render_template('index_teacher.html', data=data)
    
    # User logged in is a student
    elif session["role"] == "student":
        with mysql.connection.cursor() as cursor:
            
            # Retrieving data of the subjects and activities assigned to the student
            cursor.execute(
                """
                SELECT subjects.id, subjects.name, activities.title, activities.description, activities.due_date
                FROM subjects
                INNER JOIN activities ON subjects.id=activities.subject_id
                INNER JOIN students_subjects ON subjects.id=students_subjects.subject_id
                WHERE students_subjects.student_id=%s
                """,
            [session['user_id']])

            data = list(cursor.fetchall())

            # Formatting due dates as strings
            for d in data:
                d['due_date'] = d['due_date'].strftime("%Y/%m/%d %H:%M:%S")

            return render_template('index_student.html', data=data)


# Login route
@app.route("/login", methods=["POST", "GET"])
def login():
    """"Log user in"""
    
    # Forget any user_id
    session.clear()

    # User reached via POST
    if request.method == "POST":
        
        # Ensure username was submitted
        if not request.form.get("username"):
            flash('You must provide a username', 'error')
            return render_template("login.html")

        # Ensure password was submitted
        elif not request.form.get("password"):
            flash('You must provide a password', 'error')
            return render_template("login.html")
        
        # Query database for username
        with mysql.connection.cursor() as cursor:
            cursor = mysql.connection.cursor()
            cursor.execute('SELECT * FROM users WHERE username = %s', [request.form.get("username")])
            query = list(cursor.fetchall())
            user_data = query[0]
            user_data['creation_date'] = user_data['creation_date'].strftime("%Y/%m/%d %H:%M:%S")
            
            # Ensure username exists and password is correct
            if len(query) != 1 or not check_password_hash(user_data['password'], request.form.get("password")):
                flash('Invalid username and/or password', 'error')
                return render_template("login.html")

            # Remember which user has logged in
            session["user_id"] = user_data['id']
            session["username"] = user_data['username']
            session["fullname"] = user_data['fullname']
            session["role"] = user_data['role']
            session["creation_date"] = user_data['creation_date']

            # Redirect user to homepage
            flash('You were successfully logged in', 'success')
            return redirect(url_for('index'))
    
    # User reached via GET
    else:
        return render_template("login.html")


# Logout route
@app.route("/logout")
@login_required
def logout():
    """Log user out"""

    # Forget any user_id
    session.clear()

    # Redirect user to login form
    flash('You were successfully logged out', 'success')
    return render_template("login.html")


# Register a new user
@app.route("/register", methods=["POST", "GET"])
def register():
    """Register user"""

    # User reached via POST
    if request.method == "POST":
        
        # User did not provide the requested information
        if not request.form.get("username") or not request.form.get("password") or not request.form.get("confirmation"):
            flash('please provide complete information', 'error')
            return render_template('register.html')
        else:
            try:
                if not bool(re.search("^(?=.*?[A-Z])(?=.*?[a-z])(?=.*?[0-9])(?=.*?[#?!@$%^&*-]).{8,}$", str(request.form.get("password")))):
                    flash('invalid password', 'error')
                    return render_template('register.html')
                
                # Storing provided information
                username = request.form.get("username")
                password = request.form.get("password")
                email = request.form.get("email")
                fullname = request.form.get("fullname")
                role = request.form.get("role")
                confirmation = request.form.get("confirmation")

                # User did not select a valid role from the list
                if role not in roles:
                    flash('select a valid role')
                    return render_template('register.html')

                # User did not confirm provided password
                if password != confirmation:
                    flash('please confirm password', 'error')
                    return render_template('register.html')
                else:
                    # Storing new user in the database
                    cursor = mysql.connection.cursor()
                    cursor.execute('INSERT INTO users (username, password, email, fullname, role) VALUES (%s, %s, %s, %s, %s)', [username, generate_password_hash(password), email, fullname, role])
                    mysql.connection.commit()
                    flash('You were successfully registered', 'success')
                    return render_template('login.html')
            
            # Username already in use
            except Exception as e:
                print(e)
                flash('username is not available', 'error')
                return render_template('register.html')
    
    # User reached via GET
    else:
        return render_template("register.html")


# Register a new subject
@app.route("/registration", methods=["POST", "GET"])
@login_required
def registration():
    """Registration of subjects for teachers and students"""

    # User reached via POST
    if request.method == "POST":
        user_id = session['user_id']
        subject_id = request.form.get("subject_id")

        # User is a teacher
        if session['role'] == 'teacher':
            teacher_id = session['user_id']
            subject_id = request.form.get('subject_id')

            with mysql.connection.cursor() as cursor:
                
                # Assigning subject to teacher
                cursor.execute('UPDATE subjects SET teacher_id = %s WHERE id = %s',[teacher_id, subject_id])
                mysql.connection.commit()

                return redirect(url_for('registration'))
        
        # User is a student
        elif session['role'] == 'student':
            with mysql.connection.cursor() as cursor:
                
                # Assigning subject to student
                cursor.execute(
                    """
                    INSERT INTO students_subjects(student_id, subject_id)
                    VALUES (%s, %s)
                    """, [session["user_id"], request.form.get("subject_id")])
                mysql.connection.commit()

                # Retrieving assigned subject's activities
                cursor.execute('SELECT * FROM activities WHERE subject_id = %s', [request.form.get("subject_id")])

                activities = list(cursor.fetchall())

                # Assigning activities to student
                for a in activities:
                    print(a)
                    cursor.execute(
                        """
                        INSERT INTO students_activities(student_id, activity_id, subject_id)
                        VALUES (%s, %s, %s)
                        """, [session['user_id'], a['id'], request.form.get("subject_id")])
                    mysql.connection.commit()
                    print(f"activity_id: {a['id']} - DONE")
                
                return redirect(url_for('subjects'))
    
    # User reached via GET
    else:
        
        # User is a teacher
        if session["role"] == 'teacher':
            with mysql.connection.cursor() as cursor:
                
                # Retrieving data of the subjects assigned to the teacher 
                cursor.execute('''
                    SELECT subjects.*, users.fullname
                    FROM subjects
                    INNER JOIN users ON subjects.teacher_id=users.id
                    ORDER BY subjects.teacher_id
                ''')
                
                subjects = list(cursor.fetchall())

                return render_template('teacher_registration.html', subjects=subjects)
        
        # User is a student
        else:
            with mysql.connection.cursor() as cursor:
                
                # Retrieving subjects assigned to the student
                cursor.execute(
                """
                    SELECT
                        users.id,
                        users.fullname,
                        subjects.id,
                        subjects.name
                    FROM subjects
                    INNER JOIN users ON subjects.teacher_id=users.id
                    WHERE subjects.id NOT IN (
                        SELECT subject_id FROM students_subjects WHERE student_id = %s
                    );
                """, [session['user_id']])
                
                data = list(cursor.fetchall())

                return render_template('student_registration.html', data=data)


# Review subjects assigned to the user
@app.route("/subjects", methods=["POST", "GET"])
@login_required
def subjects():
    """"Accessing the user's assigned subjects"""
    
    # User reached via POST
    if request.method == "POST":

        # User is a student
        if session['role'] == 'student':
            
            # Redirecting student to the same page in case they did not select a subject to review
            if request.form.get("subject_id") is None:
                return redirect(url_for('subjects'))
            
            with mysql.connection.cursor() as cursor:
                
                # Retrieving subjects assigned to the student
                cursor.execute(
                    """
                        SELECT subjects.id, subjects.name, students_subjects.grade, users.fullname
                        FROM subjects
                        INNER JOIN users ON subjects.teacher_id=users.id
                        INNER JOIN students_subjects ON subjects.id=students_subjects.subject_id
                        WHERE subjects.id=%s AND students_subjects.student_id=%s
                    """, [request.form.get("subject_id"), session["user_id"]])
                subject = cursor.fetchall()[0]
                data = json.loads((request.form.get("data")).replace("'", '"'))

                # Retrieving data of the activities assigned to the student
                cursor.execute(
                    """
                    SELECT
                        activities.id,
                        activities.title,
                        activities.description,
                        activities.due_date,
                        students_activities.submitted,
                        students_activities.grade
                    FROM students_activities
                    INNER JOIN activities
                    ON students_activities.activity_id=activities.id
                    WHERE students_activities.student_id = %s
                    AND students_activities.subject_id = %s;
                    """, [session["user_id"], request.form.get("subject_id")])
                activities = list(cursor.fetchall())
                
                # Formatting due dates as strings
                for a in activities:
                    a['due_date'] = a['due_date'].strftime("%Y/%m/%d %H:%M:%S")

                return render_template('student_subjects.html', data=data, subject=subject, activities=activities)
        
        # User is a teacher
        elif session['role'] == 'teacher':
            
            # Redirecting student to the same page in case they did not select a subject to review
            if request.form.get("subject_id") is None:
                return redirect(url_for('subjects'))
            
            with mysql.connection.cursor() as cursor:
                
                # Retrieving subjects assigned to the student
                cursor.execute(
                    """
                    SELECT users.id, users.fullname, subjects.id, subjects.name, activities.id, activities.title, activities.description, activities.due_date
                    FROM users
                    INNER JOIN subjects ON users.id=subjects.teacher_id
                    INNER JOIN activities ON subjects.id=activities.subject_id
                    WHERE subject_id = %s AND teacher_id=%s
                    """, [request.form.get("subject_id"), session["user_id"]])
                activities = cursor.fetchall()
                
                for a in activities:
                    a['due_date'] = a['due_date'].strftime("%Y/%m/%d %H:%M:%S")
                
                data = json.loads((request.form.get("data")).replace("'", '"'))

                return render_template('teacher_subjects.html', data=data, activities=activities)
    
    # User reacherd via GET
    else:

        # User is a student
        if session['role'] == 'student':
            with mysql.connection.cursor() as cursor:
                
                # Retrieving subjects assigned to the student
                cursor.execute(
                """
                    SELECT subjects.id, subjects.name, users.fullname, students_subjects.grade
                    FROM subjects
                    INNER JOIN users ON subjects.teacher_id=users.id
                    INNER JOIN students_subjects ON subjects.id=students_subjects.subject_id
                    WHERE students_subjects.student_id=%s
                """, [session['user_id']])
                
                data = list(cursor.fetchall())

                return render_template('student_subjects.html', data=data)
        
        # User is a teacher
        elif session['role'] == 'teacher':
            with mysql.connection.cursor() as cursor:
                
                # Retrieving subjects assigned to the teacher
                cursor.execute('SELECT * FROM subjects WHERE teacher_id = %s', [session['user_id']])
                
                data = list(cursor.fetchall())

                return render_template('teacher_subjects.html', data=data)


@app.route("/submit", methods=["POST"])
@login_required
def submit():
    """Submitting an activity"""

    # User is not a student
    if session['role'] == 'teacher':
        return redirect(url_for('index'))
    
    # User is a student
    else:
        with mysql.connection.cursor() as cursor:
            
            # Update activity to submitted
            cursor.execute(
                """
                UPDATE students_activities
                SET submitted = 1
                WHERE student_id = %s AND activity_id = %s AND subject_id = %s
                """, [session['user_id'], request.form.get("activity_id"), request.form.get("subject_id")])
            mysql.connection.commit()

            flash('Activity submitted', 'success')
            return redirect(url_for('subjects'))