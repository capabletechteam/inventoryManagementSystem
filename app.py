from flask import Flask, render_template, request, redirect, url_for, session, flash
import json
import bcrypt
import os
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Change this to a secure key in production

DATA_DIR = 'data'
USERS_FILE = os.path.join(DATA_DIR, 'users.json')
EQUIPMENT_FILE = os.path.join(DATA_DIR, 'equipment.json')

# Ensure data directory exists
os.makedirs(DATA_DIR, exist_ok=True)

def load_json(filepath):
    if not os.path.exists(filepath):
        return {}
    with open(filepath, 'r') as file:
        return json.load(file)

def save_json(filepath, data):
    with open(filepath, 'w') as file:
        json.dump(data, file, indent=4)

# Load users
def get_users():
    return load_json(USERS_FILE)

def save_users(users):
    save_json(USERS_FILE, users)

# Load equipment
def get_equipment():
    return load_json(EQUIPMENT_FILE)

def save_equipment(equipment):
    save_json(EQUIPMENT_FILE, equipment)

@app.route('/')
def home():
    if 'user' not in session:
        return redirect(url_for('login'))
    equipment = get_equipment()
    return render_template('index.html', equipment=equipment)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password'].encode('utf-8')
        users = get_users()

        if username in users and bcrypt.checkpw(password, users[username]['password'].encode('utf-8')):
            session['user'] = username
            flash('Login successful!', 'success')
            return redirect(url_for('home'))
        else:
            flash('Invalid credentials!', 'danger')
    
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('user', None)
    flash('Logged out successfully.', 'info')
    return redirect(url_for('login'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == ['POST']:
        username = request.form['username']
        password = bcrypt.hashpw(request.form['password'].encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        users = get_users()
        
        if username in users:
            flash('Username already exists!', 'danger')
        else:
            users[username] = {'password': password}
            save_users(users)
            flash('Registration successful! You can now log in.', 'success')
            return redirect(url_for('login'))
    
    return render_template('register.html')

@app.route('/add_equipment', methods=['POST'])
def add_equipment():
    barcode = request.form['barcode']
    name = request.form['name']
    category = request.form['category']
    stock = int(request.form['stock'])
    location = request.form['location']
    equipment = get_equipment()
    equipment[barcode] = {'name': name, 'category': category, 'stock': stock, 'location': location}
    save_equipment(equipment)
    flash('Equipment added successfully!', 'success')
    return redirect(url_for('home'))

@app.route('/edit_equipment/<barcode>', methods=['POST'])
def edit_equipment(barcode):
    equipment = get_equipment()
    if barcode in equipment:
        equipment[barcode]['name'] = request.form['name']
        equipment[barcode]['category'] = request.form['category']
        equipment[barcode]['stock'] = int(request.form['stock'])
        equipment[barcode]['location'] = request.form['location']
        save_equipment(equipment)
        flash('Equipment updated successfully!', 'success')
    else:
        flash('Equipment not found!', 'danger')
    return redirect(url_for('home'))

@app.route('/delete_equipment/<barcode>', methods=['POST'])
def delete_equipment(barcode):
    equipment = get_equipment()
    if barcode in equipment:
        del equipment[barcode]
        save_equipment(equipment)
        flash('Equipment deleted successfully!', 'success')
    else:
        flash('Equipment not found!', 'danger')
    return redirect(url_for('home'))

@app.route('/sign_in_out', methods=['POST'])
def sign_in_out():
    barcode = request.form['barcode']
    person_signed_out_to = request.form['person_signed_out_to']
    person_signed_out_by = session['user']
    location = request.form['location']
    equipment = get_equipment()
    if barcode in equipment:
        sign_in_out_history = load_json(os.path.join(DATA_DIR, 'sign_in_out_history.json'))
        if not isinstance(sign_in_out_history, list):
            sign_in_out_history = []
        sign_in_out_history.append({
            'date': datetime.now().strftime('%Y-%m-%d'),
            'time': datetime.now().strftime('%H:%M:%S'),
            'barcode': barcode,
            'person_signed_out_to': person_signed_out_to,
            'person_signed_out_by': person_signed_out_by,
            'location': location
        })
        save_json(os.path.join(DATA_DIR, 'sign_in_out_history.json'), sign_in_out_history)
        flash('Equipment signed in/out successfully!', 'success')
    else:
        flash('Equipment not found!', 'danger')
    return redirect(url_for('home'))

@app.context_processor
def inject_statistics():
    equipment = get_equipment()
    total_equipment = len(equipment)
    total_stock = sum(item['stock'] for item in equipment.values())
    sign_in_out_history = load_json(os.path.join(DATA_DIR, 'sign_in_out_history.json'))
    if not isinstance(sign_in_out_history, list):
        sign_in_out_history = []
    return dict(total_equipment=total_equipment, total_stock=total_stock, sign_in_out_history=sign_in_out_history)

if __name__ == '__main__':
    app.run(debug=True)
