from flask import Flask, render_template, request, redirect, url_for, session, jsonify
import mysql.connector
from mysql.connector import Error
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = 'your_secret_key'

# MySQL database connection
def get_db_connection():
    try:
        connection = mysql.connector.connect(
            host='localhost',
            user='Root',  # Replace with actual username
            password='yes',  # Replace with actual password
            database='farmshare'  # Ensure this database exists
        )
        if connection.is_connected():
            return connection
        else:
            return None
    except Error as e:
        print(f"Error while connecting to MySQL: {e}")
        return None
    

# When creating a new user, hash the password before storing
def create_user(fullname, email, password):
    hashed_password = generate_password_hash(password, method='pbkdf2:sha256')
    connection = get_db_connection()
    if connection is None:
        return "Database connection failed", 500

    try:
        cursor = connection.cursor()
        cursor.execute('INSERT INTO users (fullname, email, password) VALUES (%s, %s, %s)', (fullname, email, hashed_password))
        connection.commit()
        return "User created successfully", 201
    except Error as e:
        return f"Error: {e}", 500
    finally:
        cursor.close()
        connection.close()

@app.route('/')
def index():
    if 'user_id' not in session:
        return redirect(url_for('login'))  # If not logged in, redirect to login page
    
    # If logged in, proceed to load the equipment list, etc.
    connection = get_db_connection()
    if connection is None:
        return "Database connection failed", 500

    try:
        cursor = connection.cursor(dictionary=True)
        cursor.execute('SELECT * FROM equipment')
        equipment_list = cursor.fetchall()
    except Error as e:
        return f"Error: {e}", 500
    finally:
        cursor.close()
        connection.close()

    return render_template('index.html', equipment_list=equipment_list, fullname=session.get('fullname'))

@app.route('/post_equipment', methods=['GET', 'POST'])
def post_equipment():
    if request.method == 'POST':
        name = request.form['name']
        price = request.form['price']
        owner = request.form['owner']
        location = request.form['location']

        connection = get_db_connection()
        if connection is None:
            return "Database connection failed", 500
        
        try:
            cursor = connection.cursor()
            cursor.execute('INSERT INTO equipment (name, price, owner, location) VALUES (%s, %s, %s, %s)', 
                           (name, price, owner, location))
            connection.commit()
        except Error as e:
            return f"Error: {e}", 500
        finally:
            cursor.close()
            connection.close()

        return redirect(url_for('index'))

    return render_template('post_equipment.html')

@app.route('/request/<equipment_name>')
def request_equipment(equipment_name):
    connection = get_db_connection()
    if connection is None:
        return "Database connection failed", 500
    
    try:
        cursor = connection.cursor(dictionary=True)
        cursor.execute('SELECT * FROM equipment WHERE name = %s', (equipment_name,))
        equipment = cursor.fetchone()
    except Error as e:
        return f"Error: {e}", 500
    finally:
        cursor.close()
        connection.close()

    if equipment:
        return render_template('rent.html', equipment=equipment)
    else:
        return "Equipment not found", 404

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        connection = get_db_connection()
        if connection is None:
            return "Database connection failed", 500

        try:
            cursor = connection.cursor(dictionary=True)
            # Debug: print email to ensure correct retrieval
            print(f"Trying to log in with email: {email}")

            query = 'SELECT * FROM users WHERE email = %s'
            cursor.execute(query, (email,))
            user = cursor.fetchone()  # Fetch one user if it exists

            # Debug: print user details
            print(f"User fetched from DB: {user}")
            
        except Error as e:
            return f"Error: {e}", 500
        finally:
            cursor.close()
            connection.close()

        # Check if the user exists and verify password
        if user:
            # Debug: print hashed password in DB
            print(f"Hashed password from DB: {user['password']}")
            if check_password_hash(user['password'], password):
                print(f"Password matched for {email}")

                # If password is correct, log user in
                session['user_id'] = user['id']
                session['fullname'] = user['fullname']
                return redirect(url_for('index'))
            else:
                print(f"Password did NOT match for {email}")
                return "Invalid credentials", 401
        else:
            print(f"No user found with email: {email}")
            return "Invalid credentials", 401

    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        fullname = request.form['fullname']
        email = request.form['email']
        password = request.form['password']
        confirm_password = request.form['confirm_password']
        
        if password != confirm_password:
            return "Passwords do not match", 400

        print(f"Registering user: {fullname}, {email}")  # Debugging line
        
        message, status_code = create_user(fullname, email, password)
        if status_code == 201:
            return redirect(url_for('index'))  # Redirect to the index page
        else:
            return message, status_code

    return render_template('register.html')

@app.route('/join_chat', methods=['POST'])
def join_chat():
    join_message = request.form.get('message')
    user_id = session.get('user_id')
    fullname = session.get('fullname')

    if not join_message or not user_id or not fullname:
        return "Incomplete message or user info", 400

    connection = get_db_connection()
    if connection is None:
        return "Database connection failed", 500

    try:
        cursor = connection.cursor()
        cursor.execute('INSERT INTO chat_messages (user_id, fullname, message) VALUES (%s, %s, %s)', 
                       (user_id, fullname, join_message))
        connection.commit()
    except Error as e:
        return f"Error: {e}", 500
    finally:
        cursor.close()
        connection.close()

    return redirect(url_for('chatroom'))

@app.route('/chatroom', methods=['GET', 'POST'])
def chatroom():
    connection = get_db_connection()
    if connection is None:
        return "Database connection failed", 500

    if request.method == 'POST':
        message = request.form.get('message')
        user_id = session.get('user_id')
        fullname = session.get('fullname')
        
        if not message or not user_id or not fullname:
            return "Incomplete message or user info", 400
        
        try:
            cursor = connection.cursor()
            cursor.execute('INSERT INTO chat_messages (user_id, fullname, message) VALUES (%s, %s, %s)', 
                           (user_id, fullname, message))
            connection.commit()
        except Error as e:
            return f"Error: {e}", 500
        finally:
            cursor.close()

    try:
        cursor = connection.cursor(dictionary=True)
        cursor.execute('SELECT fullname, message, created_at FROM chat_messages ORDER BY created_at DESC')
        chat_messages = cursor.fetchall()
    except Error as e:
        return f"Error: {e}", 500
    finally:
        cursor.close()
        connection.close()

    return render_template('chatroom.html', chat_messages=chat_messages)

@app.route('/weather')
def weather():
    # Replace with actual weather data integration
    weather_data = {
        "location": "Springfield",
        "temperature": "72°F",
        "conditions": "Clear"
    }
    return render_template('weather.html', weather_data=weather_data)
@app.route('/profile')
def profile():
    # Your profile view logic here
    return render_template('profile.html')


if __name__ == "__main__":
    app.run(debug=True)
