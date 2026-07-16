"""
Interprice Backend - Main Application
"""

from flask import Flask, jsonify, request
import os

app = Flask(__name__)

PORT = int(os.environ.get('PORT', 8000))

@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({"status": "ok", "message": "Backend is running"}), 200

@app.route('/api/v1/data', methods=['GET'])
def get_data():
    return jsonify({"message": "Social media data endpoint"}), 200

@app.route('/api/v1/stats', methods=['GET'])
def get_stats():
    return jsonify({
        "totalData": 0,
        "scrapers": 0,
        "lastUpdate": "2024-01-01"
    }), 200

@app.route('/', methods=['GET'])
def index():
    return jsonify({
        "app": "Interprice Backend",
        "description": "Social media data collection centre",
        "version": "1.0.0",
        "status": "active"
    }), 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=PORT, debug=False)