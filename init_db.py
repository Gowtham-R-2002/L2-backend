"""
Database initialization script for the inventory management system.
Run this script to create the database and tables.
"""

import pymysql
from app import app
from models import db, Role, User, Category, Product, Warehouse, Supplier, Inventory, PurchaseOrder, PurchaseOrderItem, StockMovement

def create_database():
    """Create the MySQL database if it doesn't exist"""
    try:
        # Connect to MySQL without specifying database
        connection = pymysql.connect(
            host='localhost',
            user='root',
            password='root',
            port=3309,  # Your MySQL port
            ssl_disabled=True,
            autocommit=True
        )
        
        with connection.cursor() as cursor:
            # Create database if it doesn't exist
            cursor.execute("CREATE DATABASE IF NOT EXISTS inventory_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci")
            print("Database 'inventory_db' created or already exists.")
        
        connection.close()
        
    except Exception as e:
        print(f"Error creating database: {e}")
        return False
    
    return True

def create_tables():
    """Create all tables"""
    try:
        with app.app_context():
            # Create all tables
            db.create_all()
            print("All tables created successfully.")
            
            # Add some sample data
            create_sample_data()
        
    except Exception as e:
        print(f"Error creating tables: {e}")
        return False
    
    return True

def create_sample_data():
    """Create some sample data for testing"""
    try:
        # Check if data already exists
        if Category.query.first():
            print("Sample data already exists. Skipping...")
            return
        
        # Create default roles
        roles = [
            Role(
                name="Admin",
                description="Full system access with all permissions",
                permissions={
                    "products": ["create", "read", "update", "delete"],
                    "inventory": ["create", "read", "update", "delete"],
                    "warehouses": ["create", "read", "update", "delete"],
                    "suppliers": ["create", "read", "update", "delete"],
                    "purchase_orders": ["create", "read", "update", "delete"],
                    "reports": ["read"],
                    "users": ["create", "read", "update", "delete"],
                    "system": ["backup", "restore", "settings"]
                }
            ),
            Role(
                name="User",
                description="Standard user access with limited permissions",
                permissions={
                    "products": ["read"],
                    "inventory": ["read", "update"],
                    "warehouses": ["read"],
                    "suppliers": ["read"],
                    "purchase_orders": ["create", "read"],
                    "reports": ["read"]
                }
            ),
            Role(
                name="Manager",
                description="Manager access with most permissions except user management",
                permissions={
                    "products": ["create", "read", "update", "delete"],
                    "inventory": ["create", "read", "update", "delete"],
                    "warehouses": ["create", "read", "update"],
                    "suppliers": ["create", "read", "update", "delete"],
                    "purchase_orders": ["create", "read", "update", "delete"],
                    "reports": ["read"]
                }
            )
        ]
        
        for role in roles:
            db.session.add(role)
        
        db.session.commit()
        
        # Create default admin user
        admin_role = Role.query.filter_by(name='Admin').first()
        admin_user = User(
            username='admin',
            email='admin@inventory.com',
            first_name='System',
            last_name='Administrator',
            role_id=admin_role.id
        )
        admin_user.set_password('Admin123!')  # Change this in production
        
        db.session.add(admin_user)
        db.session.commit()
        
        # Create sample categories
        categories = [
            Category(name="Electronics", description="Electronic devices and components"),
            Category(name="Clothing", description="Apparel and accessories"),
            Category(name="Books", description="Books and publications"),
            Category(name="Home & Garden", description="Home improvement and gardening supplies")
        ]
        
        for category in categories:
            db.session.add(category)
        
        # Create sample warehouses
        warehouses = [
            Warehouse(
                name="Main Warehouse",
                location="New York",
                address="123 Main St, New York, NY",
                contact_info={"phone": "555-0123", "manager": "John Doe"}
            ),
            Warehouse(
                name="West Coast Warehouse",
                location="Los Angeles",
                address="456 West Ave, Los Angeles, CA",
                contact_info={"phone": "555-0456", "manager": "Jane Smith"}
            )
        ]
        
        for warehouse in warehouses:
            db.session.add(warehouse)
        
        # Create sample suppliers
        suppliers = [
            Supplier(
                name="Tech Supplies Inc",
                contact_person="Mike Johnson",
                email="mike@techsupplies.com",
                phone="555-1111",
                address="789 Tech Blvd, Silicon Valley, CA"
            ),
            Supplier(
                name="Fashion Wholesale",
                contact_person="Sarah Wilson",
                email="sarah@fashionwholesale.com",
                phone="555-2222",
                address="321 Fashion Ave, New York, NY"
            )
        ]
        
        for supplier in suppliers:
            db.session.add(supplier)
        
        db.session.commit()
        
        # Create sample products
        products = [
            Product(
                name="Laptop Computer",
                description="High-performance laptop for business use",
                sku="LAPTOP001",
                category_id=1,
                unit_price=999.99,
                specifications={"brand": "TechBrand", "model": "Pro15", "memory": "16GB", "storage": "512GB SSD"}
            ),
            Product(
                name="Wireless Mouse",
                description="Ergonomic wireless mouse",
                sku="MOUSE001",
                category_id=1,
                unit_price=29.99,
                specifications={"brand": "TechBrand", "type": "wireless", "color": "black"}
            ),
            Product(
                name="Cotton T-Shirt",
                description="Comfortable cotton t-shirt",
                sku="TSHIRT001",
                category_id=2,
                unit_price=19.99,
                specifications={"material": "100% cotton", "sizes": ["S", "M", "L", "XL"]}
            )
        ]
        
        for product in products:
            db.session.add(product)
        
        db.session.commit()
        
        # Create sample inventory
        inventory_items = [
            Inventory(product_id=1, warehouse_id=1, quantity=50, reorder_level=10, max_stock_level=100),
            Inventory(product_id=1, warehouse_id=2, quantity=30, reorder_level=10, max_stock_level=100),
            Inventory(product_id=2, warehouse_id=1, quantity=200, reorder_level=50, max_stock_level=500),
            Inventory(product_id=2, warehouse_id=2, quantity=150, reorder_level=50, max_stock_level=500),
            Inventory(product_id=3, warehouse_id=1, quantity=100, reorder_level=25, max_stock_level=300),
            Inventory(product_id=3, warehouse_id=2, quantity=75, reorder_level=25, max_stock_level=300)
        ]
        
        for item in inventory_items:
            db.session.add(item)
        
        db.session.commit()
        print("Sample data created successfully.")
        
    except Exception as e:
        db.session.rollback()
        print(f"Error creating sample data: {e}")

if __name__ == "__main__":
    print("Initializing database...")
    
    # Create database
    if create_database():
        print("Database created successfully.")
    else:
        print("Failed to create database. Exiting.")
        exit(1)
    
    # Create tables and sample data
    if create_tables():
        print("Tables created successfully.")
        print("Database initialization complete!")
    else:
        print("Failed to create tables.")
        exit(1) 