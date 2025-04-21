from flask import Blueprint, request, render_template, jsonify

from data_services import database
from services.services_middleware import session_required

auth_bp = Blueprint('auth', __name__)


# Route to Login
@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'GET':
        return render_template('login.html')
    
    email = request.json.get('email', '').strip()
    passwd = request.json.get('password', '').strip()

    if email != '' and passwd != '':
        serv_res = database.user_sign_in_service(email, passwd)
        if serv_res['data'] is None:
            return jsonify(serv_res)
        
        user_id = serv_res['data']['user_id']
        serv_res = database.create_session_service(user_id)
        return jsonify(serv_res)
        
    return jsonify({"data": None, "message": "Credentials cannot be empty"})


# Route to Logout
@auth_bp.route('/logout', methods=['POST'])
@session_required
def logout():
    serv_res = database.delete_session_service(request.session_data['token'])
    return render_template('logout.html')


# Create new user
@auth_bp.route('/sign-up', methods=['GET', 'POST'])
def sign_up():
    if request.method == 'GET':
        return render_template('signup.html')

    email = request.json.get('email', '').strip()
    passwd = request.json.get('password', '').strip()

    if email != '' and passwd != '':
        serv_res = database.user_sign_up_service(email, passwd)
        if serv_res['data'] is None:
            return jsonify(serv_res)
        
        user_id = serv_res['data']['user_id']
        serv_res = database.create_session_service(user_id)
        return jsonify(serv_res)

    return jsonify({"data": None, "message": "Credentials cannot be empty"})


# Route to Get User
@auth_bp.route('/get-user', methods=['GET'])
@session_required
def get_user():
    serv_res = database.get_user_service(request.session_data['user_id'])
    return jsonify(serv_res)
