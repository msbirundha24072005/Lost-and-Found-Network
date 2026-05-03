from flask import Flask, render_template, jsonify, request, send_from_directory, session, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import os
import qrcode
import io
import base64
from mock_blockchain import blockchain

app = Flask(__name__)
app.secret_key = 'lost-found-secret-key'
app.template_folder = '../frontend/templates'

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///lost_and_found.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# ========== DATABASE MODELS ==========
class Report(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    report_type = db.Column(db.String(10))
    item_name = db.Column(db.String(100))
    description = db.Column(db.Text)
    location = db.Column(db.String(200))
    vehicle_id = db.Column(db.String(50))
    timestamp = db.Column(db.DateTime, default=datetime.now)
    contact_info = db.Column(db.String(100))
    status = db.Column(db.String(20), default='pending')
    
    def to_dict(self):
        return {
            'id': self.id,
            'type': self.report_type,
            'item_name': self.item_name,
            'description': self.description,
            'location': self.location,
            'vehicle_id': self.vehicle_id,
            'timestamp': self.timestamp.strftime("%Y-%m-%d %H:%M:%S"),
            'contact_info': self.contact_info,
            'status': self.status
        }

class Vehicle(db.Model):
    id = db.Column(db.String(50), primary_key=True)
    vehicle_type = db.Column(db.String(50))
    route_number = db.Column(db.String(50))

# ========== QR CODE FUNCTIONS ==========
def generate_qr_code(data):
    qr = qrcode.make(data)
    img_bytes = io.BytesIO()
    qr.save(img_bytes)
    img_bytes.seek(0)
    img_base64 = base64.b64encode(img_bytes.getvalue()).decode('utf-8')
    return img_base64

# ========== PAGE ROUTES ==========

@app.route('/')
def home():
    # Home page public - no login required
    print("🏠 Home page accessed")
    return render_template('index.html')

@app.route('/admin')
def admin_page():
    print("🔍 Admin page accessed. Session logged_in:", session.get('logged_in'))
    if not session.get('logged_in'):
        print("⛔ Not logged in, redirecting to login")
        return redirect(url_for('login'))
    print("✅ Logged in, showing admin page")
    return render_template('admin.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        print(f"🔐 Login attempt: username={username}")
        
        if username == 'admin' and password == 'admin123':
            session['logged_in'] = True
            print(f"✅ Login successful! Session set to: {session.get('logged_in')}")
            return redirect(url_for('admin_page'))
        else:
            print("❌ Login failed - invalid credentials")
            return render_template('login.html', error="Invalid credentials")
    
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    print("👋 Logged out, session cleared")
    return redirect(url_for('login'))

@app.route('/clear-session')
def clear_session():
    session.clear()
    return "Session cleared! <a href='/'>Go Home</a>"

@app.route('/map')
def map_page():
    return render_template('map.html')

@app.route('/scan/<vehicle_id>')
def scan_qr_page(vehicle_id):
    vehicle = Vehicle.query.get(vehicle_id)
    if not vehicle:
        vehicle = {'id': vehicle_id, 'vehicle_type': 'bus', 'route_number': 'Unknown'}
    return render_template('scan.html', 
                         vehicle_id=vehicle_id,
                         vehicle_type=getattr(vehicle, 'vehicle_type', 'bus'),
                         route_number=getattr(vehicle, 'route_number', 'Unknown'))

# ========== API ROUTES ==========
@app.route('/api/reports', methods=['GET'])
def get_reports():
    reports = Report.query.all()
    return jsonify([report.to_dict() for report in reports])

@app.route('/api/report/<int:report_id>', methods=['GET'])
def get_report(report_id):
    report = Report.query.get(report_id)
    if report:
        return jsonify(report.to_dict())
    return jsonify({'error': 'Not found'}), 404

@app.route('/api/blockchain/add', methods=['POST'])
def add_to_blockchain():
    try:
        data = request.json
        new_report = Report(
            report_type=data.get('type'),
            item_name=data.get('item_name'),
            description=data.get('description'),
            location=data.get('location'),
            vehicle_id=data.get('vehicle_id'),
            contact_info=data.get('contact_info', '')
        )
        db.session.add(new_report)
        db.session.commit()
        
        blockchain_data = {
            "report_id": new_report.id,
            "type": new_report.report_type,
            "item_name": new_report.item_name,
            "vehicle_id": new_report.vehicle_id,
            "timestamp": str(new_report.timestamp)
        }
        
        blockchain_result = blockchain.add_report(blockchain_data)
        
        return jsonify({
            'success': True,
            'message': 'Report added to blockchain!',
            'report_id': new_report.id,
            'blockchain': blockchain_result
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400

@app.route('/api/blockchain/chain')
def get_blockchain():
    return jsonify({
        "chain": blockchain.get_chain(),
        "length": len(blockchain.get_chain()),
        "valid": blockchain.is_chain_valid()
    })

@app.route('/api/match', methods=['GET'])
def find_matches():
    reports = Report.query.filter_by(status='pending').all()
    matches = []
    
    lost_reports = [r for r in reports if r.report_type == 'lost']
    found_reports = [r for r in reports if r.report_type == 'found']
    
    for lost in lost_reports:
        for found in found_reports:
            score = 0
            if lost.item_name and found.item_name:
                if lost.item_name.lower() == found.item_name.lower():
                    score += 0.5
            if lost.location and found.location:
                if lost.location.lower() == found.location.lower():
                    score += 0.3
            if lost.vehicle_id == found.vehicle_id:
                score += 0.2
            if score > 0.5:
                matches.append({
                    'lost_report': lost.to_dict(),
                    'found_report': found.to_dict(),
                    'match_score': round(score, 2)
                })
    
    return jsonify({'matches': matches})

@app.route('/api/vehicle/<vehicle_id>/qr')
def get_vehicle_qr(vehicle_id):
    vehicle = Vehicle.query.get(vehicle_id)
    if not vehicle:
        vehicle = Vehicle(id=vehicle_id, vehicle_type='bus', route_number='Route 101')
        db.session.add(vehicle)
        db.session.commit()
    
    qr_data = f"http://127.0.0.1:5000/scan/{vehicle.id}"
    qr_base64 = generate_qr_code(qr_data)
    
    return jsonify({
        'vehicle_id': vehicle.id,
        'type': vehicle.vehicle_type,
        'route': vehicle.route_number,
        'qr_image': f"data:image/png;base64,{qr_base64}",
        'scan_url': f"/scan/{vehicle.id}"
    })

@app.route('/api/admin/report/<int:report_id>/status', methods=['POST'])
def update_report_status(report_id):
    data = request.json
    report = Report.query.get(report_id)
    if report:
        report.status = data.get('status', report.status)
        db.session.commit()
        return jsonify({'success': True})
    return jsonify({'success': False}), 404

# ========== INITIALIZE DATABASE ==========
with app.app_context():
    db.create_all()
    if Vehicle.query.count() == 0:
        vehicles = [
            {'id': 'BUS001', 'type': 'bus', 'route': 'Route 101'},
            {'id': 'BUS002', 'type': 'bus', 'route': 'Route 202'},
            {'id': 'TRAIN001', 'type': 'train', 'route': 'Blue Line'},
            {'id': 'METRO001', 'type': 'metro', 'route': 'Line 1'}
        ]
        for v in vehicles:
            db.session.add(Vehicle(id=v['id'], vehicle_type=v['type'], route_number=v['route']))
        db.session.commit()
        print("✅ Sample vehicles added")

if __name__ == '__main__':
    print("\n" + "="*50)
    print("🚍 DECENTRALIZED LOST & FOUND SYSTEM")
    print("="*50)
    print("🌐 Home:  http://127.0.0.1:5000")
    print("🗺️  Map:   http://127.0.0.1:5000/map")
    print("👑 Admin: http://127.0.0.1:5000/admin")
    print("="*50 + "\n")
    app.run(debug=True, port=5000)