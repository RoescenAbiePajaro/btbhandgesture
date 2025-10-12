from flask import Flask, request, jsonify
from flask_cors import CORS
from pymongo import MongoClient
from datetime import datetime
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

app = Flask(__name__)
CORS(app)

# Configuration
MONGODB_URI = os.getenv('MONGODB_URI')

# MongoDB Connection
try:
    client = MongoClient(MONGODB_URI)
    db = client.get_database()
    print('✅ Connected to MongoDB')
except Exception as e:
    print(f'MongoDB connection error: {e}')

# Collections
clicks_collection = db['clicks']

# =====================
# ⚙️ TEST ENDPOINT
# =====================
@app.route('/api/test', methods=['GET'])
def test():
    return jsonify({'message': 'Click tracking server is running'})

# =====================
# 📊 CLICK TRACKING ENDPOINTS
# =====================
@app.route('/api/clicks', methods=['POST'])
def log_click():
    """Log a click event"""
    try:
        data = request.get_json()
        button = data.get('button')
        page = data.get('page')

        if not button or not page:
            return jsonify({'message': 'Button and page are required'}), 400

        click_data = {
            'button': button,
            'page': page,
            'timestamp': datetime.utcnow()
        }

        clicks_collection.insert_one(click_data)
        return jsonify({'message': 'Click logged successfully'}), 201
    except Exception as e:
        print(f'Error logging click: {e}')
        return jsonify({'message': 'Server error logging click'}), 500

@app.route('/api/clicks', methods=['GET'])
def get_clicks():
    """Get paginated click logs"""
    try:
        page = int(request.args.get('page', 1))
        limit = int(request.args.get('limit', 10))
        skip = (page - 1) * limit

        # Get clicks with pagination
        clicks_cursor = clicks_collection.find().sort('timestamp', -1).skip(skip).limit(limit)
        clicks = list(clicks_cursor)
        
        # Convert ObjectId to string and format timestamp
        for click in clicks:
            click['_id'] = str(click['_id'])
            click['timestamp'] = click['timestamp'].isoformat()

        total = clicks_collection.count_documents({})

        return jsonify({'clicks': clicks, 'total': total})
    except Exception as e:
        print(f'Error fetching click logs: {e}')
        return jsonify({'message': 'Server error fetching click logs'}), 500

@app.route('/api/clicks/<click_id>', methods=['DELETE'])
def delete_click(click_id):
    """Delete a single click log"""
    try:
        from bson.objectid import ObjectId
        
        result = clicks_collection.delete_one({'_id': ObjectId(click_id)})
        if result.deleted_count == 0:
            return jsonify({'message': 'Click log not found'}), 404
        
        return jsonify({'message': 'Click log deleted successfully'})
    except Exception as e:
        print(f'Error deleting click log: {e}')
        return jsonify({'message': 'Server error deleting click log'}), 500

@app.route('/api/clicks', methods=['DELETE'])
def delete_all_clicks():
    """Delete all click logs"""
    try:
        result = clicks_collection.delete_many({})
        return jsonify({'message': f'All click logs deleted successfully ({result.deleted_count} removed)'})
    except Exception as e:
        print(f'Error deleting all click logs: {e}')
        return jsonify({'message': 'Server error deleting all click logs'}), 500

if __name__ == '__main__':
    port = int(os.getenv('PORT', 5000))
    app.run(debug=True, port=port)