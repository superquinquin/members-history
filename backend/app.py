from flask import Flask, jsonify, request
from flask_cors import CORS
from dotenv import load_dotenv
import os
from odoo_client import OdooClient

load_dotenv()

app = Flask(__name__)
CORS(app)

odoo = OdooClient()

@app.route('/api/health', methods=['GET'])
def health():
    return jsonify({'status': 'ok'})

@app.route('/api/odoo/test-connection', methods=['GET'])
def test_odoo_connection():
    try:
        authenticated = odoo.authenticate()
        if authenticated:
            return jsonify({
                'status': 'connected',
                'odoo_url': odoo.url,
                'odoo_db': odoo.db,
                'authenticated': True,
                'uid': odoo.uid
            })
        else:
            return jsonify({
                'status': 'failed',
                'error': 'Authentication failed',
                'authenticated': False
            }), 500
    except Exception as e:
        print(f"Error testing Odoo connection: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'status': 'failed',
            'error': str(e),
            'authenticated': False
        }), 500

@app.route('/api/members/search', methods=['GET'])
def search_members():
    name = request.args.get('name', '')
    if not name:
        return jsonify({'error': 'Name parameter is required'}), 400
    
    try:
        members = odoo.search_members_by_name(name)
        print(f"Processing {len(members)} members")
        result = []
        for member in members:
            print(f"Member data: {member}")
            address_parts = [
                member.get('street'),
                member.get('street2'),
                member.get('zip'),
                member.get('city')
            ]
            address = ', '.join(filter(None, address_parts))
            
            image = member.get('image_small') or member.get('image_medium') or member.get('image')
            result.append({
                'id': member.get('id'),
                'name': member.get('name'),
                'address': address if address else None,
                'phone': member.get('phone') or member.get('mobile') or None,
                'image': image if image else None,
                'raw': member
            })
        
        return jsonify({'members': result})
    except Exception as e:
        print(f"Error searching members: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

@app.route('/api/member/<int:member_id>/history', methods=['GET'])
def get_member_history(member_id):
    try:
        purchases = odoo.get_member_purchase_history(member_id)
        events = []
        for purchase in purchases:
            events.append({
                'type': 'purchase',
                'id': purchase.get('id'),
                'date': purchase.get('date_order'),
                'reference': purchase.get('pos_reference') or purchase.get('name')
            })
        
        return jsonify({
            'member_id': member_id,
            'events': events
        })
    except Exception as e:
        print(f"Error fetching member history: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    port = int(os.getenv('FLASK_PORT', 5001))
    app.run(debug=True, port=port)
