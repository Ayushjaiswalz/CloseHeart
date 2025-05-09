from flask import Blueprint, request, jsonify
from database import SessionLocal
from models import User
import bcrypt

auth_bp = Blueprint('auth', __name__)
db = SessionLocal()

@auth_bp.route('/register', methods=['POST'])
def register():
    if request.content_type == 'application/json':
        data = request.get_json(force=True)
        name = data.get('name')
        email = data.get('email')
        password = data.get('password')
    else:
        name = request.form.get('name')
        email = request.form.get('email')
        password = request.form.get('password')

    if not all([name, email, password]):
        return jsonify({'error': 'Name, email, and password are required'}), 400

    # Check if user already exists
    existing_user = db.query(User).filter_by(email=email).first()
    if existing_user:
        return jsonify({'error': 'User already exists'}), 409

    # Hash the password
    # password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    password_hash = password 

    # Create user
    new_user = User(name=name, email=email, password_hash=password_hash)
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    return jsonify({'message': 'User registered successfully', 'user_id': str(new_user.id)})


@auth_bp.route('/login', methods=['POST'])
def login():
    if request.content_type == 'application/json':
        data = request.get_json(force=True)
        email = data.get('email')
        password = data.get('password')
    else:
        email = request.form.get('email')
        password = request.form.get('password')

    if not all([email, password]):
        return jsonify({'error': 'Email and password are required'}), 400

    # Fetch user
    user = db.query(User).filter_by(email=email).first()
    # if not user or not bcrypt.checkpw(password.encode('utf-8'), user.password_hash.encode('utf-8')):
    #     return jsonify({'error': 'Invalid email or password'}), 401
    
    if not user or password != user.password_hash:
        return jsonify({'error': 'Invalid email or password'}), 401

    return jsonify({'message': 'Login successful', 'user_id': str(user.id)})
