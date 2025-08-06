#!/usr/bin/env python3
import os
import sys
from app import app
from models import db, Role, User, Category, Product, Warehouse, Supplier, Inventory, PurchaseOrder, PurchaseOrderItem, StockMovement, NotificationLog

def update_database_schema():
    """Drop and recreate all tables with updated schema"""
    with app.app_context():
        try:
            print("🗑️  Dropping all existing tables...")
            db.drop_all()
            print("✅ All tables dropped successfully!")
            
            print("🏗️  Creating all tables with new schema...")
            db.create_all()
            print("✅ All tables created successfully!")
            
            # Create default roles
            print("🎭 Creating default roles...")
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
            print("✅ Roles created successfully!")
            
            # Create admin user
            admin_role = Role.query.filter_by(name='Admin').first()
            print("👤 Creating admin user...")
            
            admin_user = User(
                username='admin',
                email='admin@inventory.com',
                first_name='System',
                last_name='Administrator',
                role_id=admin_role.id,
                is_active=True
            )
            admin_user.set_password('Admin123!')
            
            db.session.add(admin_user)
            db.session.commit()
            print("✅ Admin user created successfully!")
            
            # Create sample categories
            print("📂 Creating sample categories...")
            categories = [
                Category(name="Electronics", description="Electronic products and devices"),
                Category(name="Clothing", description="Apparel and fashion items"),
                Category(name="Books", description="Books and educational materials"),
                Category(name="Home & Garden", description="Home improvement and garden supplies"),
                Category(name="Sports", description="Sports and fitness equipment"),
            ]
            
            for category in categories:
                db.session.add(category)
            
            db.session.commit()
            print("✅ Sample categories created!")
            
            # Create sample warehouses
            print("🏢 Creating sample warehouses...")
            warehouses = [
                Warehouse(
                    name="Main Warehouse",
                    location="New York",
                    address="123 Main St, New York, NY 10001",
                    contact_info={
                        "manager": "John Smith",
                        "phone": "+1-555-0123",
                        "email": "john.smith@company.com"
                    },
                    is_active=True
                ),
                Warehouse(
                    name="West Coast Distribution",
                    location="Los Angeles",
                    address="456 West Ave, Los Angeles, CA 90001",
                    contact_info={
                        "manager": "Sarah Johnson",
                        "phone": "+1-555-0456",
                        "email": "sarah.johnson@company.com"
                    },
                    is_active=True
                ),
            ]
            
            for warehouse in warehouses:
                db.session.add(warehouse)
            
            db.session.commit()
            print("✅ Sample warehouses created!")
            
            # Create sample suppliers
            print("🏭 Creating sample suppliers...")
            suppliers = [
                Supplier(
                    name="Tech Solutions Inc",
                    contact_person="Mike Wilson",
                    email="mike@techsolutions.com",
                    phone="+1-555-0789",
                    address="789 Tech Plaza, Silicon Valley, CA 94000",
                    tax_id="TAX123456",
                    payment_terms="Net 30",
                    is_active=True
                ),
                Supplier(
                    name="Global Supplies Co",
                    contact_person="Lisa Chen",
                    email="lisa@globalsupplies.com",
                    phone="+1-555-0321",
                    address="321 Supply St, Chicago, IL 60000",
                    tax_id="TAX654321",
                    payment_terms="Net 45",
                    is_active=True
                ),
            ]
            
            for supplier in suppliers:
                db.session.add(supplier)
            
            db.session.commit()
            print("✅ Sample suppliers created!")
            
            # Create sample products with barcodes
            print("📦 Creating sample products...")
            electronics_category = Category.query.filter_by(name="Electronics").first()
            clothing_category = Category.query.filter_by(name="Clothing").first()
            
            products = [
                Product(
                    name="Laptop Computer",
                    description="High-performance laptop for business use",
                    sku="LAPTOP001",
                    barcode="1234567890123",
                    category_id=electronics_category.id,
                    unit_price=999.99,
                    specifications={"brand": "TechBrand", "model": "Pro15", "ram": "16GB", "storage": "512GB SSD"},
                    is_active=True
                ),
                Product(
                    name="Wireless Mouse",
                    description="Ergonomic wireless mouse",
                    sku="MOUSE001",
                    barcode="1234567890124",
                    category_id=electronics_category.id,
                    unit_price=29.99,
                    specifications={"brand": "TechBrand", "type": "Wireless", "dpi": "1600"},
                    is_active=True
                ),
                Product(
                    name="Cotton T-Shirt",
                    description="Comfortable cotton t-shirt",
                    sku="TSHIRT001",
                    barcode="1234567890125",
                    category_id=clothing_category.id,
                    unit_price=19.99,
                    specifications={"material": "100% Cotton", "sizes": ["S", "M", "L", "XL"]},
                    is_active=True
                ),
            ]
            
            for product in products:
                db.session.add(product)
            
            db.session.commit()
            print("✅ Sample products created!")
            
            # Create sample inventory
            print("📊 Creating sample inventory...")
            main_warehouse = Warehouse.query.filter_by(name="Main Warehouse").first()
            west_warehouse = Warehouse.query.filter_by(name="West Coast Distribution").first()
            
            laptop = Product.query.filter_by(sku="LAPTOP001").first()
            mouse = Product.query.filter_by(sku="MOUSE001").first()
            tshirt = Product.query.filter_by(sku="TSHIRT001").first()
            
            inventory_items = [
                Inventory(product_id=laptop.id, warehouse_id=main_warehouse.id, quantity=50, reorder_level=10, max_stock_level=200),
                Inventory(product_id=laptop.id, warehouse_id=west_warehouse.id, quantity=30, reorder_level=10, max_stock_level=150),
                Inventory(product_id=mouse.id, warehouse_id=main_warehouse.id, quantity=200, reorder_level=50, max_stock_level=500),
                Inventory(product_id=mouse.id, warehouse_id=west_warehouse.id, quantity=150, reorder_level=50, max_stock_level=400),
                Inventory(product_id=tshirt.id, warehouse_id=main_warehouse.id, quantity=5, reorder_level=20, max_stock_level=300),  # Low stock
                Inventory(product_id=tshirt.id, warehouse_id=west_warehouse.id, quantity=100, reorder_level=20, max_stock_level=250),
            ]
            
            for item in inventory_items:
                db.session.add(item)
            
            db.session.commit()
            print("✅ Sample inventory created!")
            
            print("\n🎉 Database schema updated successfully!")
            print("\n📝 Login credentials:")
            print("   Username: admin")
            print("   Password: Admin123!")
            print("\n✨ Sample data includes:")
            print("   - 5 Categories")
            print("   - 2 Warehouses")
            print("   - 2 Suppliers")
            print("   - 3 Products (with barcodes)")
            print("   - 6 Inventory items")
            print("   - 1 Low stock alert (T-Shirt in Main Warehouse)")
            
        except Exception as e:
            print(f"❌ Error updating database schema: {str(e)}")
            db.session.rollback()
            return False
            
        return True

if __name__ == '__main__':
    print("🚀 Updating database schema...")
    success = update_database_schema()
    if success:
        print("\n✅ Schema update completed successfully!")
    else:
        print("\n❌ Schema update failed!")
        sys.exit(1) 