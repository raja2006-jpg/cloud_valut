from flask import Flask, render_template, request, redirect, url_for, session, flash, send_from_directory
from flask_sqlalchemy import SQLAlchemy
import os
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Replace with a secure key

# Base directory and database config
basedir = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'database', 'users.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# File upload settings
UPLOAD_FOLDER = os.path.join(basedir, 'static', 'uploads')
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Initialize database
db = SQLAlchemy(app)

# User Model
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))
    email = db.Column(db.String(100), unique=True)
    password = db.Column(db.String(100))

# File Model
class File(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(200))
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))

# Home Page
@app.route('/')
def index():
    if 'user_id' in session:
        files = File.query.filter_by(user_id=session['user_id']).all()
        return render_template('index.html', files=files, user=session['name'])
    return render_template('index.html', files=None, user=None)

# Register
@app.route('/register', methods=['POST'])
def register():
    name = request.form['name']
    email = request.form['email']
    password = request.form['password']
    
    if User.query.filter_by(email=email).first():
        flash("Email already registered.")
        return redirect(url_for('index'))

    new_user = User(name=name, email=email, password=password)
    db.session.add(new_user)
    db.session.commit()
    flash("Registration successful. Please login.")
    return redirect(url_for('index'))

# Login
@app.route('/login', methods=['POST'])
def login():
    email = request.form['email']
    password = request.form['password']
    user = User.query.filter_by(email=email, password=password).first()
    if user:
        session['user_id'] = user.id
        session['name'] = user.name
        flash("Login successful.")
    else:
        flash("Invalid credentials.")
    return redirect(url_for('index'))

# Logout
@app.route('/logout')
def logout():
    session.clear()
    flash("Logged out successfully.")
    return redirect(url_for('index'))

# Upload
@app.route('/upload', methods=['POST'])
def upload():
    if 'user_id' not in session:
        flash("Please login to upload.")
        return redirect(url_for('index'))

    file = request.files['file']
    if file:
        filename = secure_filename(file.filename)
        user_folder = os.path.join(app.config['UPLOAD_FOLDER'], str(session['user_id']))
        os.makedirs(user_folder, exist_ok=True)
        file.save(os.path.join(user_folder, filename))

        new_file = File(filename=filename, user_id=session['user_id'])
        db.session.add(new_file)
        db.session.commit()
        flash("File uploaded successfully.")

    return redirect(url_for('index'))

# Serve Uploaded Files
@app.route('/uploads/<int:user_id>/<filename>')
def uploaded_file(user_id, filename):
    return send_from_directory(os.path.join(app.config['UPLOAD_FOLDER'], str(user_id)), filename)

# Run the Flask app
if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
