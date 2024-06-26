from flask import Flask, jsonify, request
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity, get_jwt
from functools import wraps
from models.users import Users
from werkzeug.security import generate_password_hash, check_password_hash
import logging

# Mock user database
users = {
    'user1': {'password': generate_password_hash('password1'), 'role': 'passenger'},
    'user2': {'password': generate_password_hash('password2'), 'role': 'business manager'},
    'user3': {'password': generate_password_hash('password3'), 'role': 'Intasend admin'}
}

def auth_routes(app, db):
    # Create logger
    logger = logging.getLogger(__name__)

    # Register route for passengers
    @app.route('/apis/v1/register/passenger', methods=['POST'])
    def register_passenger():
        try:
            data = request.json
            logger.info(f'Received registration request: {data}')  # Log received data
            # Check if required fields are present in the request
            if 'first_name' not in data or 'last_name' not in data or 'email' not in data or 'phone_number' not in data or 'password' not in data:
                logger.error('Missing required fields')  # Log error
                return jsonify({'message': 'Missing required fields'}), 400
            
            # Check if user with the provided email already exists
            existing_user = Users.query.filter_by(email=data['email']).first()
            if existing_user:
                logger.info('User with this email already exists')  # Log message
                return jsonify({'message': 'User with this email already exists'}), 409
            
            # Generate a hashed password
            password_hash = generate_password_hash(data['password'])
            # Create a new user instance for the passenger
            passenger = Users(
                first_name=data['first_name'],
                last_name=data['last_name'],
                email=data['email'],
                phone_number=data['phone_number'],
                password_hash=password_hash
            )
            # Add the user to the database
            db.session.add(passenger)
            db.session.commit()
            logger.info('Passenger registered successfully')  # Log success
            return jsonify({'message': 'Passenger registered successfully'}), 201
        except Exception as e:
            logger.error(f'Error processing registration request: {e}')  # Log error with exception
            return jsonify({'message': 'An error occurred while processing your request'}), 500

    # User login endpoint
    @app.route('/apis/v1/user/login', methods=['POST'])
    def login():
        try:
            data = request.json
            # Check if the login request contains a username or phone number
            if 'username' in data:
                user = Users.query.filter_by(username=data['username']).first()
            elif 'phone_number' in data:
                user = Users.query.filter_by(phone_number=data['phone_number']).first()
            else:
                return jsonify({'message': 'Missing username or phone number'}), 400
            # Verify password and return access token if login successful
            if user and check_password_hash(user.password_hash, data['password']):
                access_token = create_access_token(identity=user.id)
                return jsonify({'access_token': access_token}), 200
            else:
                return jsonify({'message': 'Invalid credentials'}), 401
        except Exception as e:
            return jsonify({'message': 'An error occurred while processing your request'}), 500

    # Protected routes by role
def role_required(required_role):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            jwt_data = get_jwt()
            if 'role' not in jwt_data:
                return jsonify({'message': 'JWT token does not contain role information'}), 401
            if jwt_data['role'] != required_role:
                return jsonify({'message': 'Insufficient permissions'}), 403
            return func(*args, **kwargs)
        return wrapper
    return decorator

    @app.route('/apis/v1/passenger/dashboard')
    @jwt_required()
    @role_required('passenger')
    def passenger_dashboard():
        # Serve passenger dashboard data
        current_user = get_jwt_identity()
        return jsonify({'message': f'Passenger dashboard data for {current_user}'}), 200

    @app.route('/apis/v1/manager/dashboard')
    @jwt_required()
    @role_required('business manager')
    def manager_dashboard():
        # Serve manager dashboard data
        current_user = get_jwt_identity()
        return jsonify({'message': f'Manager dashboard data for {current_user}'}), 200

    @app.route('/apis/v1/admin/dashboard')
    @jwt_required()
    @role_required('Intasend admin')
    def admin_dashboard():
        # Serve admin dashboard data
        current_user = get_jwt_identity()
        return jsonify({'message': f'Admin dashboard data for {current_user}'}), 200