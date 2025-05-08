from flask import Blueprint, request, jsonify
from database import SessionLocal
from models import User, Couple
import uuid

couple_bp = Blueprint('couple', __name__)
db = SessionLocal()

@couple_bp.route('/create-couple', methods=['POST'])
def create_couple():
    data = request.get_json(force=True)
    user1_id = data.get('user1_id')
    user2_id = data.get('user2_id')

    if not all([user1_id, user2_id]):
        return jsonify({'error': 'Both user IDs are required'}), 400
    if user1_id == user2_id:
        return jsonify({'error': 'Cannot create couple with same user'}), 400

    # Check both users exist
    user1 = db.query(User).filter_by(id=user1_id).first()
    user2 = db.query(User).filter_by(id=user2_id).first()
    if not user1 or not user2:
        return jsonify({'error': 'One or both users not found'}), 404

    # Check if either is already in a couple
    existing = db.query(Couple).filter(
        (Couple.user1_id.in_([user1_id, user2_id])) | 
        (Couple.user2_id.in_([user1_id, user2_id]))
    ).first()

    if existing:
        return jsonify({'error': 'One or both users are already in a couple'}), 409

    # Create couple
    new_couple = Couple(user1_id=user1_id, user2_id=user2_id)
    db.add(new_couple)
    db.commit()
    db.refresh(new_couple)

    return jsonify({
        'message': 'Couple created successfully',
        'couple_id': str(new_couple.id),
        'user1_id': str(user1_id),
        'user2_id': str(user2_id)
    })
