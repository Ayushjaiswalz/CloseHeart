from flask import Blueprint, request, jsonify, session
from database import SessionLocal
from models import Location, User, Couple, LastMet
from uuid import UUID
from datetime import date
import os
import requests
from dotenv import load_dotenv

load_dotenv()

location_bp = Blueprint('location', __name__)
ORS_API_KEY = os.getenv("ORS_API_KEY")

# ------------------- Update User Location -------------------
@location_bp.route('/api/update-location', methods=['POST'])
def update_location():
    db = SessionLocal()
    user_id = session.get('user_id')

    if not user_id:
        return jsonify({"error": "Unauthorized"}), 401

    try:
        user_uuid = UUID(user_id)
    except:
        return jsonify({"error": "Invalid or missing user_id"}), 400

    try:
        data = request.get_json()
        latitude = data.get('latitude')
        longitude = data.get('longitude')

        if latitude is None or longitude is None:
            return jsonify({"error": "Latitude and longitude required"}), 400

        # Save or update location
        location = db.query(Location).filter_by(user_id=user_uuid).first()
        if location:
            location.latitude = latitude
            location.longitude = longitude
        else:
            location = Location(user_id=user_uuid, latitude=latitude, longitude=longitude)
            db.add(location)

        db.commit()
        return jsonify({"message": "Location updated successfully!"}), 200

    except Exception as e:
        db.rollback()
        return jsonify({"error": "Internal server error", "details": str(e)}), 500

# ------------------- Calculate Road Distance -------------------
def calculate_road_distance(lat1, lon1, lat2, lon2):
    url = "https://api.openrouteservice.org/v2/directions/driving-car"
    headers = {
        'Authorization': ORS_API_KEY,
        'Content-Type': 'application/json'
    }
    body = {
        "coordinates": [[lon1, lat1], [lon2, lat2]]
    }

    try:
        response = requests.post(url, json=body, headers=headers)
        data = response.json()

        if "routes" in data and data["routes"]:
            dist_meters = data["routes"][0]["summary"]["distance"]
            return round(dist_meters / 1000, 2)  # Convert to km
        else:
            return None
    except Exception as e:
        print("ORS error:", e)
        return None

# ------------------- Get Live Distance -------------------
@location_bp.route('/api/live-distance', methods=['GET'])
def live_distance():
    db = SessionLocal()
    user_id = session.get('user_id')

    if not user_id:
        return jsonify({"error": "Unauthorized"}), 401

    # Get couple info
    couple = db.query(Couple).filter(
        (Couple.user1_id == user_id) | (Couple.user2_id == user_id)
    ).first()
    if not couple:
        return jsonify({"error": "Not in a couple"}), 404

    # Get partner ID
    partner_id = couple.user2_id if str(couple.user1_id) == str(user_id) else couple.user1_id

    user_loc = db.query(Location).filter_by(user_id=user_id).first()
    partner_loc = db.query(Location).filter_by(user_id=partner_id).first()

    if not user_loc or not partner_loc:
        return jsonify({"error": "Missing location data"}), 400

    # ✅ Calculate road distance
    dist = calculate_road_distance(
        user_loc.latitude, user_loc.longitude,
        partner_loc.latitude, partner_loc.longitude
    )

    if dist is None:
        return jsonify({"error": "Failed to calculate distance"}), 500

    couple.last_distance_km = dist

    # ✅ If distance = 0, set/update last_met_date
    if dist == 0:
        existing = db.query(LastMet).filter_by(couple_id=couple.id).first()
        if existing:
            existing.last_met_date = date.today()
        else:
            last_met = LastMet(couple_id=couple.id, last_met_date=date.today())
            db.add(last_met)

    db.commit()

    return jsonify({
        "distance": dist,
        "user_location": {
            "latitude": user_loc.latitude,
            "longitude": user_loc.longitude
        },
        "partner_location": {
            "latitude": partner_loc.latitude,
            "longitude": partner_loc.longitude
        }
    })
