from flask import Flask
from flask_cors import CORS
from mongoengine import connect
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

# Initialize Flask app
app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('JWT_SECRET', 'your_jwt_secret_key_here')

# Enable CORS
CORS(app)

# MongoDB connection
mongodb_uri = os.getenv('MONGODB_URI', 'mongodb://localhost:27017/soccer_slot_manager')
connect(host=mongodb_uri)
print('✅ MongoDB connected successfully')

# Import routes
from routes import auth, users, slots, stats

# Register blueprints
app.register_blueprint(auth.bp, url_prefix='/api/auth')
app.register_blueprint(users.bp, url_prefix='/api/users')
app.register_blueprint(slots.bp, url_prefix='/api/slots')
app.register_blueprint(stats.bp, url_prefix='/api/stats')

# Health check
@app.route('/api/health', methods=['GET'])
def health_check():
    return {'status': 'ok', 'message': 'Server is running'}, 200

# Error handlers
@app.errorhandler(404)
def not_found(error):
    return {'error': 'Not found'}, 404

@app.errorhandler(500)
def internal_error(error):
    return {'error': 'Internal server error'}, 500

if __name__ == '__main__':
    port = int(os.getenv('PORT', 5000))
    print(f'🚀 Server is running on port {port}')
    app.run(host='0.0.0.0', port=port, debug=True)
