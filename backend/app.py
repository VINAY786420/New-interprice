"""
Interprice Backend - Main Application with Database & Authentication
"""

from flask import Flask, jsonify, request
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
import os
from datetime import datetime
import json

# Import modules
from models import db, User, SocialAccount, Post, Analytics
from auth import generate_token, decode_token, token_required
from scrapers import SocialMediaScraper

app = Flask(__name__)

# Configuration
DATABASE_URL = os.environ.get('DATABASE_URL', 'sqlite:///interprice.db')
app.config['SQLALCHEMY_DATABASE_URI'] = DATABASE_URL
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['JSON_SORT_KEYS'] = False

# Initialize extensions
db.init_app(app)

# CORS Configuration
CORS(app, resources={
    r"/*": {
        "origins": ["*"],
        "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        "allow_headers": ["Content-Type", "Authorization"],
        "supports_credentials": True
    }
})

PORT = int(os.environ.get('PORT', 8000))

# Create tables
with app.app_context():
    db.create_all()

# ==================== HEALTH & INFO ====================

@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({
        "status": "ok",
        "message": "Backend is running",
        "timestamp": datetime.utcnow().isoformat()
    }), 200

@app.route('/', methods=['GET'])
def index():
    return jsonify({
        "app": "Interprice Backend",
        "description": "Social media data collection centre",
        "version": "2.0.0",
        "status": "active",
        "features": ["User Authentication", "Social Media Scraping", "Real-time Analytics"]
    }), 200

# ==================== AUTHENTICATION ====================

@app.route('/api/v1/auth/signup', methods=['POST'])
def signup():
    """User registration"""
    try:
        data = request.get_json()
        
        # Validation
        if not data or not data.get('email') or not data.get('password') or not data.get('username'):
            return jsonify({'error': 'Missing required fields'}), 400
        
        # Check if user exists
        if User.query.filter_by(email=data['email']).first():
            return jsonify({'error': 'Email already registered'}), 409
        
        if User.query.filter_by(username=data['username']).first():
            return jsonify({'error': 'Username already taken'}), 409
        
        # Create user
        user = User(
            email=data['email'],
            username=data['username'],
            full_name=data.get('full_name', '')
        )
        user.set_password(data['password'])
        
        db.session.add(user)
        db.session.commit()
        
        # Generate token
        token = generate_token(user.id)
        
        return jsonify({
            'message': 'User created successfully',
            'user': user.to_dict(),
            'token': token
        }), 201
    
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@app.route('/api/v1/auth/login', methods=['POST'])
def login():
    """User login"""
    try:
        data = request.get_json()
        
        if not data or not data.get('email') or not data.get('password'):
            return jsonify({'error': 'Missing email or password'}), 400
        
        user = User.query.filter_by(email=data['email']).first()
        
        if not user or not user.check_password(data['password']):
            return jsonify({'error': 'Invalid credentials'}), 401
        
        token = generate_token(user.id)
        
        return jsonify({
            'message': 'Login successful',
            'user': user.to_dict(),
            'token': token
        }), 200
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/v1/auth/me', methods=['GET'])
@token_required
def get_current_user():
    """Get current user info"""
    try:
        user = User.query.get(request.user_id)
        
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        return jsonify(user.to_dict()), 200
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ==================== SOCIAL ACCOUNTS ====================

@app.route('/api/v1/accounts', methods=['GET'])
@token_required
def get_accounts():
    """Get user's social accounts"""
    try:
        accounts = SocialAccount.query.filter_by(user_id=request.user_id).all()
        return jsonify([acc.to_dict() for acc in accounts]), 200
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/v1/accounts', methods=['POST'])
@token_required
def add_account():
    """Add new social account"""
    try:
        data = request.get_json()
        
        if not data or not data.get('platform') or not data.get('account_username'):
            return jsonify({'error': 'Missing required fields'}), 400
        
        # Check if account already exists
        existing = SocialAccount.query.filter_by(
            user_id=request.user_id,
            platform=data['platform'],
            account_username=data['account_username']
        ).first()
        
        if existing:
            return jsonify({'error': 'Account already added'}), 409
        
        account = SocialAccount(
            user_id=request.user_id,
            platform=data['platform'],
            account_username=data['account_username']
        )
        
        db.session.add(account)
        db.session.commit()
        
        # Trigger scraping
        scrape_result = SocialMediaScraper.scrape(data['platform'], data['account_username'])
        
        return jsonify({
            'message': 'Account added successfully',
            'account': account.to_dict(),
            'scrape_status': scrape_result
        }), 201
    
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

# ==================== POSTS ====================

@app.route('/api/v1/posts', methods=['GET'])
@token_required
def get_posts():
    """Get user's posts"""
    try:
        platform = request.args.get('platform')
        limit = request.args.get('limit', 20, type=int)
        
        query = Post.query.filter_by(user_id=request.user_id)
        
        if platform:
            query = query.filter_by(platform=platform)
        
        posts = query.order_by(Post.posted_at.desc()).limit(limit).all()
        
        return jsonify([post.to_dict() for post in posts]), 200
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ==================== ANALYTICS ====================

@app.route('/api/v1/analytics', methods=['GET'])
@token_required
def get_analytics():
    """Get user analytics"""
    try:
        analytics = Analytics.query.filter_by(user_id=request.user_id).order_by(
            Analytics.date.desc()
        ).limit(30).all()
        
        return jsonify([a.to_dict() for a in analytics]), 200
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/v1/analytics/summary', methods=['GET'])
@token_required
def get_analytics_summary():
    """Get analytics summary"""
    try:
        latest_analytics = Analytics.query.filter_by(user_id=request.user_id).order_by(
            Analytics.date.desc()
        ).first()
        
        accounts = SocialAccount.query.filter_by(user_id=request.user_id).all()
        posts = Post.query.filter_by(user_id=request.user_id).all()
        
        summary = {
            'total_accounts': len(accounts),
            'total_posts': len(posts),
            'total_followers': sum(acc.followers_count for acc in accounts),
            'total_engagement': sum(p.likes_count + p.comments_count + p.shares_count for p in posts),
            'latest_analytics': latest_analytics.to_dict() if latest_analytics else None,
            'platforms': {}
        }
        
        for platform in ['instagram', 'twitter', 'facebook', 'linkedin', 'youtube']:
            platform_accounts = [acc for acc in accounts if acc.platform == platform]
            platform_posts = [p for p in posts if p.platform == platform]
            
            summary['platforms'][platform] = {
                'accounts': len(platform_accounts),
                'followers': sum(acc.followers_count for acc in platform_accounts),
                'posts': len(platform_posts),
                'engagement': sum(p.likes_count + p.comments_count + p.shares_count for p in platform_posts)
            }
        
        return jsonify(summary), 200
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ==================== DATA ENDPOINTS ====================

@app.route('/api/v1/data', methods=['GET'])
def get_data():
    return jsonify({"message": "Social media data endpoint"}), 200

@app.route('/api/v1/stats', methods=['GET'])
def get_stats():
    return jsonify({
        "totalData": Post.query.count(),
        "scrapers": len(['instagram', 'twitter', 'facebook', 'linkedin', 'youtube']),
        "lastUpdate": datetime.utcnow().isoformat()
    }), 200

# ==================== ERROR HANDLERS ====================

@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Resource not found'}), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({'error': 'Internal server error'}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=PORT, debug=False)
