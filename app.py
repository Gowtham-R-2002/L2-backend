from flask import Flask, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from flask_migrate import Migrate
from flask_socketio import SocketIO
from flask_jwt_extended import JWTManager
from flask_mail import Mail
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Initialize Flask app
app = Flask(__name__)

# Configuration
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', 'mysql+pymysql://root:root@localhost:3309/inventory_db?ssl_disabled=true&allowPublicKeyRetrieval=true')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# JWT Configuration
app.config['JWT_SECRET_KEY'] = os.getenv('JWT_SECRET_KEY', app.config['SECRET_KEY'])
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = False  # Set to False for development, use timedelta in production

# Email Configuration
app.config['MAIL_SERVER'] = os.getenv('MAIL_SERVER', 'smtp.gmail.com')
app.config['MAIL_PORT'] = int(os.getenv('MAIL_PORT', 587))
app.config['MAIL_USE_TLS'] = os.getenv('MAIL_USE_TLS', 'True').lower() == 'true'
app.config['MAIL_USERNAME'] = os.getenv('MAIL_USERNAME')
app.config['MAIL_PASSWORD'] = os.getenv('MAIL_PASSWORD')
app.config['MAIL_DEFAULT_SENDER'] = os.getenv('MAIL_DEFAULT_SENDER', app.config['MAIL_USERNAME'])

# Import db from models
from models import db

# Initialize extensions
db.init_app(app)
migrate = Migrate(app, db)
cors = CORS(app)
socketio = SocketIO(app, cors_allowed_origins="*")
jwt = JWTManager(app)
mail = Mail(app)

# Import blueprints
from routes.auth import auth_bp
from routes.users import users_bp
from routes.products import products_bp
from routes.categories import categories_bp
from routes.warehouses import warehouses_bp
from routes.suppliers import suppliers_bp
from routes.inventory import inventory_bp
from routes.purchase_orders import purchase_orders_bp
from routes.reports import reports_bp
from routes.csv_routes import csv_bp
from routes.barcode import barcode_bp

# Register blueprints
app.register_blueprint(auth_bp, url_prefix='/api/auth')
app.register_blueprint(users_bp, url_prefix='/api/users')
app.register_blueprint(products_bp, url_prefix='/api/products')
app.register_blueprint(categories_bp, url_prefix='/api/categories')
app.register_blueprint(warehouses_bp, url_prefix='/api/warehouses')
app.register_blueprint(suppliers_bp, url_prefix='/api/suppliers')
app.register_blueprint(inventory_bp, url_prefix='/api/inventory')
app.register_blueprint(purchase_orders_bp, url_prefix='/api/purchase-orders')
app.register_blueprint(reports_bp, url_prefix='/api/reports')
app.register_blueprint(csv_bp, url_prefix='/api/csv')
app.register_blueprint(barcode_bp, url_prefix='/api/barcode')

@app.route('/')
def index():
    return jsonify({
        'message': 'E-commerce Inventory Management System API',
        'version': '1.0.0',
        'status': 'active'
    })

@app.route('/api/health')
def health_check():
    try:
        # Test database connection
        db.session.execute('SELECT 1')
        return jsonify({'status': 'healthy', 'database': 'connected'})
    except Exception as e:
        return jsonify({'status': 'unhealthy', 'error': str(e)}), 500

if __name__ == '__main__':
    # Create tables on startup
    with app.app_context():
        db.create_all()
    
    socketio.run(app, debug=True, host='0.0.0.0') 
