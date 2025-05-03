from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_cors import CORS
import psycopg2
from psycopg2.extras import RealDictCursor
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Needed for session and flash messages
CORS(app)

# Database configuration
DATABASE_CONFIG = {
    'dbname': 'project',
    'user': 'postgres',
    'password': '3101',
    'host': 'localhost',
    'port': '5432'
}

def get_db_connection():
    return psycopg2.connect(**DATABASE_CONFIG, cursor_factory=RealDictCursor)

# Home route
@app.route('/')
def index():
    return render_template('main.html')

# Admin Signup
@app.route('/admin/signup', methods=['GET', 'POST'])
def admin_signup():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        confirm_password = request.form['confirm_password']
        
        if password == confirm_password:
            hashed_password = generate_password_hash(password)  # Hash the password
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute('INSERT INTO admin (username, password) VALUES (%s, %s)', (username, hashed_password))
            conn.commit()
            cursor.close()
            conn.close()
            flash('Admin account created successfully!', 'success')
            return redirect(url_for('admin_login'))
        else:
            flash('Passwords do not match!', 'error')
    return render_template('admin_signup.html')


       
@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM admin WHERE username = %s', (username,))
        admin = cursor.fetchone()
        cursor.close()
        conn.close()
        
        if admin and check_password_hash(admin['password'], password):  # Using hash comparison
            session['admin_id'] = admin['id']  # Store the admin's ID in the session
            session['admin_username'] = admin['username']  # You can also store the username if needed
            return redirect(url_for('admin_dashboard'))
        else:
            flash('Invalid credentials, please try again.', 'error')
            return redirect(url_for('admin_login'))

    return render_template('admin_login.html')


# Student Login
@app.route('/student/login', methods=['GET', 'POST'])
def student_login():
    if request.method == 'POST':
        roll_no = request.form['roll_no']
        dob = request.form['dob']

        try:
            conn = get_db_connection()
            cur = conn.cursor()
            cur.execute("SELECT * FROM students WHERE student_roll_number = %s AND dob = %s", (roll_no, dob))
            student = cur.fetchone()
            print(f"Student fetched: {student}")  # Debugging line
            cur.close()
            conn.close()

            if student:
                # Use student_roll_number in the session instead of id
                session['student_roll_number'] = student['student_roll_number'] # Debugging line
                return redirect(url_for('student_results'))
            else:
                flash('Invalid roll number or date of birth!', 'error')
        except Exception as e:
            flash(f'Error: {e}', 'error')

    return render_template('student_login.html')



@app.route('/admin')
def admin_dashboard():
    if 'admin_id' not in session:
        flash('Please log in to access the dashboard.', 'error')
        return redirect(url_for('admin_login'))
    return render_template('admin_dashboard.html')

@app.route('/admin/school_registration', methods=['GET', 'POST'])
def school_registration():
    if 'admin_id' not in session:
        return redirect(url_for('admin_login'))
    
    if request.method == 'POST':
        school_id = request.form['school_id']
        school_name = request.form['school_name']
        city = request.form['city']
        
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('INSERT INTO school (school_id, school_name, city) VALUES (%s, %s, %s)',
                       (school_id, school_name, city))
        conn.commit()
        cursor.close()
        conn.close()
        flash('School successfully added!', 'success')
        return redirect(url_for('admin_dashboard'))
    
    return render_template('school_registration.html')

# Examiner Registration
@app.route('/admin/examiner_registration', methods=['GET', 'POST'])
def examiner_registration():
    if 'admin_id' not in session:
        return redirect(url_for('admin_login'))
    
    if request.method == 'POST':
        examiner_id = request.form['examiner_id']
        examiner_name = request.form['examiner_name']
        mentorship_status = request.form['mentorship_status']
        mentorship_start_date = request.form['mentorship_start_date']
        
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('INSERT INTO examiner (examiner_id, examiner_name, mentorship_status, mentorship_start_date) VALUES (%s, %s, %s, %s)',
                       (examiner_id, examiner_name, mentorship_status, mentorship_start_date))
        conn.commit()
        cursor.close()
        conn.close()
        flash('Examiner successfully added!', 'success')
        return redirect(url_for('admin_dashboard'))
    
    return render_template('examiner_registration.html')

# Student Registration


@app.route('/admin/student_registration', methods=['GET', 'POST'])
def student_registration():
    school_id = None  # Default value for GET request
    schools = []  # This will store the list of schools

    # Fetch school details from the database
    try:
        conn = get_db_connection()  # Use get_db_connection to connect to DB
        cur = conn.cursor()

        # Fetch all schools (id and name)
        cur.execute("SELECT school_id, school_name FROM school")  # Ensure correct table name 'school'
        schools = cur.fetchall()  # Fetch all rows of the query

        cur.close()
        conn.close()
    except psycopg2.Error as e:
        flash(f"Error: {e}", 'error')
        return redirect(url_for('admin_dashboard'))

    # Handle POST request to register student
    if request.method == 'POST':
        student_roll_number = request.form['student_roll_number']
        student_name = request.form['student_name']
        dob = request.form['dob']
        school_id = request.form['school_id']  # Get the selected school ID
        contact_numbers = request.form.getlist('contact_no[]')  # Get the contact numbers

        # Check if school_id is empty and handle appropriately
        if not school_id:
            flash('Please select a valid school', 'error')
            return redirect(url_for('student_registration'))

        # Insert student and contact information into the database
        try:
            conn = get_db_connection()  # Use get_db_connection to connect to DB
            cur = conn.cursor()

            # Insert the student data into the students table
            cur.execute("INSERT INTO students (student_roll_number, student_name, dob, school_id) VALUES (%s, %s, %s, %s)",
                        (student_roll_number, student_name, dob, school_id))

            # Insert the contact numbers
            for contact in contact_numbers:
                cur.execute("INSERT INTO contacts (student_roll_number, contact_number) VALUES (%s, %s)",
                            (student_roll_number, contact))

            conn.commit()  # Commit the transaction
            cur.close()
            conn.close()

            flash('Student registered successfully!', 'success')
            return redirect(url_for('admin_dashboard'))  # Redirect to admin dashboard after successful registration

        except psycopg2.Error as e:
            flash(f"Error: {e}", 'error')
            return redirect(url_for('student_registration'))  # If any error happens, stay on the form page

    # Return the student registration page with the list of schools and the selected school_id
    return render_template('student_registration.html', schools=schools, school_id=school_id)

@app.route('/admin/view_schools')
def view_schools():
    if 'admin_id' not in session:
        return redirect(url_for('admin_login'))
    
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM school')
    schools = cursor.fetchall()
    cursor.close()
    conn.close()
    
    return render_template('view_schools.html', schools=schools)



# View Students
@app.route('/admin/view_students')
def view_students():
    if 'admin_id' not in session:
        return redirect(url_for('admin_login'))
    
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM students')
    students = cursor.fetchall()
    cursor.close()
    conn.close()
    
    return render_template('view_students.html', students=students)

@app.route('/admin/view_examiners')
def view_examiners():
    if 'admin_id' not in session:
        return redirect(url_for('admin_login'))

    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # Query to fetch examiner details along with their qualifications and contact numbers
        cursor.execute('''
            SELECT e.examiner_id, e.examiner_name, e.mentorship_status, e.mentorship_start_date,
                   eq.qualifications, ec.contact_no
            FROM examiner e
            LEFT JOIN examiner_qualifications eq ON e.examiner_id = eq.examiner_id
            LEFT JOIN examiner_contact ec ON e.examiner_id = ec.examiner_id
        ''')

        examiners = cursor.fetchall()
        cursor.close()
        conn.close()

        return render_template('view_examiners.html', examiners=examiners)
    
    except psycopg2.Error as e:
        flash(f"Error: {e}", 'error')
        return redirect(url_for('admin_dashboard'))


# Update Marks
@app.route('/admin/update_marks', methods=['GET', 'POST'])
def update_marks():
    if 'admin_id' not in session:
        return redirect(url_for('admin_login'))
    
    if request.method == 'POST':
        student_roll_number = request.form['student_roll_number']
        subject = request.form['subject']
        marks_assigned = request.form['marks_assigned']
        
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('UPDATE answer_sheet SET marks_assigned = %s WHERE student_roll_number = %s AND subject = %s',
                       (marks_assigned, student_roll_number, subject))
        conn.commit()
        cursor.close()
        conn.close()
        flash('Marks successfully updated!', 'success')
        return redirect(url_for('admin_dashboard'))
    
    return render_template('update_marks.html')

# View Marks
@app.route('/admin/view_marks')
def view_marks():
    if 'admin_id' not in session:
        return redirect(url_for('admin_login'))
    
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM answer_sheet')
    marks = cursor.fetchall()
    cursor.close()
    conn.close()
    
    return render_template('view_marks.html', marks=marks)

@app.route('/student/results')
def student_results():
    # Check if the student is logged in
    if 'student_roll_number' not in session:
        flash('Please log in to view your results.', 'error')
        return redirect(url_for('student_login'))

    student_roll_number = session['student_roll_number']

    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # Query to fetch the student's marks directly using roll number
        cursor.execute('''
            SELECT subject, marks_assigned
            FROM answer_sheet
            WHERE student_roll_number = %s
        ''', (student_roll_number,))

        marks = cursor.fetchall()
        cursor.close()
        conn.close()

        # If no marks found, redirect to login with an error message
        if not marks:
            flash('No results found for your roll number.', 'error')
            return redirect(url_for('student_login'))

        # Render the results page with the marks
        return render_template('student_results.html', marks=marks, roll_number=student_roll_number)

    except psycopg2.Error as e:
        # Handle database errors gracefully
        flash(f"Error fetching results: {e}", 'error')
        return redirect(url_for('student_login'))



@app.route('/logout')
def logout():
    session.pop('admin', None)
    return redirect(url_for('index'))


       


if __name__ == '__main__':
    app.run(debug=True)
