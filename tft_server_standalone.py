

from flask import Flask, jsonify, request
from flask_cors import CORS
import requests
import cv2
import numpy as np
import time
import threading

try:
    import mediapipe as mp
    mp_pose = mp.solutions.pose
    pose = mp_pose.Pose(
        static_image_mode=False,
        model_complexity=0,
        smooth_landmarks=True,
        min_detection_confidence=0.5,
        min_tracking_confidence=0.5
    )
    mp_drawing = mp.solutions.drawing_utils
    MEDIAPIPE_AVAILABLE = True
except Exception as e:
    print(f'⚠️ MediaPipe unavailable: {e}')
    MEDIAPIPE_AVAILABLE = False

app = Flask(__name__)
CORS(app)

# ═══════════════════════════════════════════════════════════════
# Configuration - Point to your existing server
# ═══════════════════════════════════════════════════════════════
EXISTING_SERVER_URL = "http://localhost:5000"  # Your original server.py

# ═══════════════════════════════════════════════════════════════
# Cache latest data
# ═══════════════════════════════════════════════════════════════
latest_dashboard_data = {
    "analysis": {"exercise": "STANDING", "form_score": 0, "angles": {}, "feedback": "Waiting..."},
    "sensors": {"heart_rate": 0, "spo2": 0, "stress": 0},
    "timestamp": None
}

# ═══════════════════════════════════════════════════════════════
# Health Check
# ═══════════════════════════════════════════════════════════════
@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint"""
    return jsonify({
        'status': 'ok',
        'service': 'formcheck-tft-server',
        'version': 'standalone',
        'existing_server': EXISTING_SERVER_URL
    }), 200


# ═══════════════════════════════════════════════════════════════
# Proxy to Existing Server + TFT Endpoints
# ═══════════════════════════════════════════════════════════════

@app.route('/api/tft/dashboard', methods=['GET'])
def tft_dashboard():
    """
    Get dashboard data for TFT display
    Proxies to existing server or generates from cache
    """
    try:
        # Try to fetch from existing server first
        response = requests.get(
            f"{EXISTING_SERVER_URL}/api/tft/dashboard",
            timeout=2
        )
        if response.status_code == 200:
            return response.json(), 200
    except:
        pass
    
    # Fallback: return cached data
    return jsonify(latest_dashboard_data), 200


@app.route('/api/tft/snapshot', methods=['GET'])
def tft_snapshot():
    """
    Get compressed snapshot for TFT
    Proxies to existing server
    """
    try:
        response = requests.get(
            f"{EXISTING_SERVER_URL}/api/tft/snapshot",
            timeout=5
        )
        if response.status_code == 200:
            return response.json(), 200
    except:
        pass
    
    return jsonify({"error": "Cannot fetch snapshot"}), 503


@app.route('/api/tft/camera-status', methods=['GET'])
def tft_camera_status():
    """
    Get camera status
    Proxies to existing server
    """
    try:
        response = requests.get(
            f"{EXISTING_SERVER_URL}/api/camera/status",
            timeout=2
        )
        if response.status_code == 200:
            return response.json(), 200
    except:
        pass
    
    return jsonify({"status": "unknown"}), 503


@app.route('/api/tft/latest-vitals', methods=['GET'])
def tft_latest_vitals():
    """
    Get latest smartwatch vitals
    Token required (same as your existing server)
    """
    token = request.args.get('token') or request.headers.get('Authorization', '').replace('Bearer ', '')
    
    try:
        headers = {'Authorization': f'Bearer {token}'} if token else {}
        response = requests.get(
            f"{EXISTING_SERVER_URL}/api/devices/smartwatch/latest",
            headers=headers,
            timeout=2
        )
        if response.status_code == 200:
            return response.json(), 200
    except:
        pass
    
    return jsonify({"available": False}), 200


# ═══════════════════════════════════════════════════════════════
# Direct TFT Endpoints (if existing server unavailable)
# ═══════════════════════════════════════════════════════════════

@app.route('/api/tft/set-camera', methods=['POST'])
def set_camera_url():
    """
    Cache camera URL for direct access
    (if running without existing server)
    """
    data = request.json or {}
    camera_url = data.get('url')
    
    if not camera_url:
        return jsonify({'error': 'Missing url'}), 400
    
    # Store in global config
    global EXISTING_SERVER_URL
    # Could store camera URL for direct streaming if needed
    
    return jsonify({'status': 'ok', 'url': camera_url}), 200


# ═══════════════════════════════════════════════════════════════
# Utility: Test Connection to Existing Server
# ═══════════════════════════════════════════════════════════════

@app.route('/api/tft/diagnostics', methods=['GET'])
def diagnostics():
    """
    Check if existing server is reachable
    Useful for troubleshooting
    """
    status = {
        'tft_server': 'running',
        'existing_server': 'unknown',
        'mediapipe': 'available' if MEDIAPIPE_AVAILABLE else 'unavailable'
    }
    
    try:
        response = requests.get(f"{EXISTING_SERVER_URL}/health", timeout=2)
        if response.status_code == 200:
            status['existing_server'] = 'reachable'
            status['existing_server_status'] = response.json()
        else:
            status['existing_server'] = 'unreachable'
    except Exception as e:
        status['existing_server'] = f'error: {str(e)}'
    
    return jsonify(status), 200


if __name__ == '__main__':
    print('''
    ╔════════════════════════════════════════════╗
    ║   FormCheck - TFT Display Server           ║
    ║   (Standalone - Does NOT replace server.py)║
    ╚════════════════════════════════════════════╝
    ''')
    
    print(f"Proxying to existing server: {EXISTING_SERVER_URL}")
    print("TFT Endpoints:")
    print("  GET /api/tft/dashboard")
    print("  GET /api/tft/snapshot")
    print("  GET /api/tft/camera-status")
    print("  GET /api/tft/latest-vitals")
    print("  GET /api/tft/diagnostics")
    print("\nRunning on http://0.0.0.0:5001")
    print("(Your existing server runs on port 5000)\n")
    
    app.run(host='0.0.0.0', port=5001, debug=False, threaded=True)
