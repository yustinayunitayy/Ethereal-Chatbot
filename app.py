from flask import Flask, render_template, request, redirect, url_for, session
import mysql.connector
from mysql.connector import errorcode
from main.chatbot import chatbot_response
import speech_recognition as sr

app = Flask(__name__)
app.secret_key = 'your_secret_key'

config = {
    'user': 'root',
    'password': '',
    'host': 'localhost',
    'database': 'projectai',
    'raise_on_warnings': True
}

def get_db_connection():
    try:
        conn = mysql.connector.connect(**config)
        return conn
    except mysql.connector.Error as err:
        print(f"Error connecting to MySQL: {err}")
        return None

conn = get_db_connection()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/panda')
def panda():
    return render_template('panda.html')

@app.route('/contact', methods=['GET', 'POST'])
def contact():
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        phone = request.form.get('phone')
        message = request.form.get('message')

        if not (name and email and phone and message):
            return 'Please fill in all fields.', 400

        conn = get_db_connection()
        if conn is None:
            return 'Error connecting to database', 500

        try:
            cursor = conn.cursor()
            cursor.execute('INSERT INTO messages (name, email, phone, message) VALUES (%s, %s, %s, %s)', (name, email, phone, message))
            conn.commit()
            cursor.close()
            conn.close()
            return 'Message successfully sent! Thank you for sending us a message, we will reach you out'

        except mysql.connector.Error as err:
            print(f"Error inserting into database: {err}")
            conn.rollback()
            return 'Error sending the message, please try again.', 500

    return render_template('contact.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        if not (username and password):
            return "Please fill in all fields.", 400
        
        cursor = conn.cursor(dictionary=True)
        cursor.execute('SELECT * FROM users WHERE username = %s AND password = %s', (username, password))
        user = cursor.fetchone()
        cursor.close()

        if user:
            session['username'] = user['username']
            return "Welcome to Ethereal~!"
        else:
            return "User not found. Please check your username and password."
    
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        name = request.form['name']
        email = request.form['email']
        phone = request.form['phone']
        password = request.form['password']
        
        if not (username and name and email and phone and password):
            return "Please fill in all fields.", 400
        
        if '@' not in email or '.' not in email.split('@')[1]:
            return "Please enter a valid email address.", 400
        
        if not (phone.isdigit() and len(phone) >= 10 and len(phone) <= 14):
            return "Please enter a valid phone number with 10-14 digits.", 400
        
        if not (any(c.isalpha() for c in password) and any(c.isdigit() for c in password) and len(password) >= 8):
            return "Password must contain at least 8 characters, including both letters and numbers.", 400

        cursor = conn.cursor()
        try:
            cursor.execute('SELECT * FROM users WHERE username = %s', (username,))
            if cursor.fetchone():
                return "Username already exists. Please choose a different username.", 400
            
            cursor.execute('SELECT * FROM users WHERE email = %s', (email,))
            if cursor.fetchone():
                return "Email already exists. Please use a different email address.", 400
            
            cursor.execute('SELECT * FROM users WHERE phone = %s', (phone,))
            if cursor.fetchone():
                return "Phone number already exists. Please use a different phone number.", 400

            # Insert new user into database
            cursor.execute('INSERT INTO users (username, name, email, phone, password) VALUES (%s, %s, %s, %s, %s)', (username, name, email, phone, password))
            conn.commit()
            return "Registration complete! Please log in to your account."
        
        except mysql.connector.Error as err:
            print(f"Error executing SQL: {err}")
            conn.rollback()
            return "Registration failed. Please try again later.", 500
        finally:
            cursor.close()

    return render_template('register.html')

@app.route('/chatbot', methods=['GET', 'POST'])
def chatbot():
    if 'username' in session:
        if request.method == 'POST':
            user_message = request.form.get('message')
            username = session['username']

            print(f"Fetching user ID for username: {username}")  # Debug log

            # Fetch user ID based on username
            conn = get_db_connection()
            if conn is None:
                print("Database connection failed.")  # Debug log
                return 'Error connecting to database', 500

            try:
                cursor = conn.cursor(dictionary=True)
                cursor.execute('SELECT user_id FROM users WHERE username = %s', (username,))
                user = cursor.fetchone()
                print(f"Database query executed. Fetched user: {user}")  # Debug log
                cursor.close()
                conn.close()

                if user:
                    user_id = user['user_id']
                    print(f"User ID fetched: {user_id}")  # Debug log
                    bot_response = chatbot_response(user_message, user_id)
                    return bot_response
                else:
                    print("User not found.")  # Debug log
                    return 'User not found.', 404
            except mysql.connector.Error as err:
                print(f"Error fetching user ID: {err}")  # Debug log
                return 'Error fetching user ID', 500
        else:
            return render_template('chatbot.html')
    else:
        return redirect(url_for('login'))

@app.route('/speech_to_text', methods=['POST'])
def speech_to_text():
    recognizer = sr.Recognizer()
    with sr.Microphone() as source:
        audio = recognizer.listen(source)
        try:
            text = recognizer.recognize_google(audio)
            return text
        except sr.UnknownValueError:
            return "Sorry, I could not understand the audio."
        except sr.RequestError:
            return "Sorry, the service is down."

def get_chatbot_response(message):
    return f"Ethereal says: {message}"

@app.route('/admin', methods=['GET', 'POST'])
def admin():
    if 'admin_username' in session:
        conn = get_db_connection()
        if conn is None:
            return 'Error connecting to database', 500

        try:
            cursor = conn.cursor(dictionary=True)
            
            cursor.execute('''
                SELECT alerts.*, users.name, users.phone 
                FROM alerts 
                JOIN users ON alerts.user_id = users.user_id
            ''')
            alerts = cursor.fetchall()

            # Optionally, handle other admin functionalities here

            cursor.close()
            conn.close()

            return render_template('admin.html', alerts=alerts)
        except mysql.connector.Error as err:
            print(f"Error fetching alerts: {err}")
            return 'Error fetching alerts', 500
    else:
        return redirect(url_for('loginadmin'))

@app.route('/loginadmin', methods=['GET', 'POST'])
def loginadmin():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        if not (username and password):
            return "Please fill in all fields.", 400
        
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute('SELECT * FROM admin WHERE admin_uname = %s AND admin_pass = %s', (username, password))
        user = cursor.fetchone()
        cursor.close()
        conn.close()

        if user:
            session['admin_username'] = user['admin_uname']
            return "Welcome Admin"
        else:
            return "Admin username or password is incorrect.", 400
    
    return render_template('loginadmin.html')

@app.route('/feedbackmsg')
def feedbackmsg():
    if 'admin_username' in session:
        conn = get_db_connection()
        if conn is None:
            return 'Error connecting to database', 500

        try:
            cursor = conn.cursor(dictionary=True)
            cursor.execute('SELECT * FROM messages')
            messages = cursor.fetchall()
            cursor.close()
            conn.close()

            return render_template('admfeedback.html', messages=messages)
        except mysql.connector.Error as err:
            print(f"Error fetching feedback messages: {err}")
            return 'Error fetching feedback messages', 500
    else:
        return redirect(url_for('loginadmin'))

@app.route('/userdata')
def userdata():
    if 'admin_username' in session:
        conn = get_db_connection()
        if conn is None:
            return 'Error connecting to database', 500

        try:
            cursor = conn.cursor(dictionary=True)
            cursor.execute('SELECT user_id, name, email, phone FROM users')
            users = cursor.fetchall()
            cursor.close()
            conn.close()

            return render_template('admuserdata.html', users=users)
        except mysql.connector.Error as err:
            print(f"Error fetching user data: {err}")
            return 'Error fetching user data', 500
    else:
        return redirect(url_for('loginadmin'))


@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True)
