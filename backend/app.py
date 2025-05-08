import sys
import os
from flask import Flask, request, render_template, redirect, session,  send_from_directory
from auth import auth_bp
from location import location_bp
from couple import couple_bp
from database import SessionLocal
from models import User, Couple, LastMet
from datetime import datetime

sys.path.append(os.path.dirname(__file__))

app = Flask(__name__)
app.secret_key = 'your_super_secret_key'  # Required for session management

# Register blueprints
app.register_blueprint(auth_bp, url_prefix='/api')
app.register_blueprint(location_bp)
app.register_blueprint(couple_bp, url_prefix='/api')


# ---------------------- ROOT ----------------------
@app.route('/')
def home():
    return redirect('/register')


# ---------------------- LOGIN ----------------------
@app.route('/login', methods=['GET', 'POST'])
def login_page():
    db = SessionLocal()

    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        user = db.query(User).filter_by(email=email).first()

        if user and password == user.password_hash:  # no hash check for dev
            session['user_id'] = str(user.id)

            # If already paired, go to dashboard
            existing = db.query(Couple).filter(
                (Couple.user1_id == user.id) | (Couple.user2_id == user.id)
            ).first()
            return redirect('/dashboard' if existing else '/connect')

        return render_template('login.html', message='Invalid email or password')

    return render_template('login.html')


# ---------------------- REGISTER ----------------------
@app.route('/register', methods=['GET', 'POST'])
def register_page():
    db = SessionLocal()

    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        password = request.form['password']

        if db.query(User).filter_by(email=email).first():
            return render_template('register.html', message='User already exists')

        user = User(name=name, email=email, password_hash=password)
        db.add(user)
        db.commit()

        session['user_id'] = str(user.id)
        return redirect('/connect')

    return render_template('register.html')


# ---------------------- CONNECT ----------------------
@app.route('/connect', methods=['GET', 'POST'])
def connect_partner():
    db = SessionLocal()
    user1_id = session.get('user_id')

    if not user1_id:
        return redirect('/login')

    existing = db.query(Couple).filter(
        (Couple.user1_id == user1_id) | (Couple.user2_id == user1_id)
    ).first()
    if existing:
        return redirect('/dashboard')

    message = None
    success = False

    if request.method == 'POST':
        user2_id = request.form.get('partner_id')

        if user1_id == user2_id:
            message = "Cannot pair with yourself"
        else:
            user2 = db.query(User).filter_by(id=user2_id).first()
            already_paired = db.query(Couple).filter(
                (Couple.user1_id == user2_id) | (Couple.user2_id == user2_id)
            ).first()

            if not user2:
                message = "Partner not found"
            elif already_paired:
                message = "Partner already connected" 
            else:
                couple = Couple(user1_id=user1_id, user2_id=user2_id)
                db.add(couple)
                db.commit()
                return redirect('/dashboard')

    return render_template('connect.html', message=message, success=success, current_user_id=user1_id)



# ---------------------- DASHBOARD ----------------------
@app.route('/dashboard')
def dashboard():
    db = SessionLocal()
    user_id = session.get('user_id')
    if not user_id:
        return redirect('/login')

    couple = db.query(Couple).filter(
        (Couple.user1_id == user_id) | (Couple.user2_id == user_id)
    ).first()

    if not couple:
        return redirect('/connect')

    partner_id = couple.user2_id if str(couple.user1_id) == str(user_id) else couple.user1_id
    partner = db.query(User).filter_by(id=partner_id).first()

    # Days since last met (optional)
    days_since_met = None
    if couple.last_met and couple.last_met.last_met_date:
        days_since_met = (datetime.utcnow().date() - couple.last_met.last_met_date).days

    return render_template('dashboard.html', partner=partner, days_since_met=days_since_met, distance_km=couple.last_distance_km)


@app.route('/manifest.json')
def manifest():
    return send_from_directory('static', 'manifest.json')


# ---------------------- RUN ----------------------
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 5000)))
