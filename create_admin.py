#!/usr/bin/env python3
import os
import sys
from app import app
from models import db, Role, User

def create_admin_user():
    """Create admin user and roles if they don't exist"""
    with app.app_context():
        try:
            # Check if roles exist
            admin_role = Role.query.filter_by(name='Admin').first()
            if not admin_role:
                print("Creating roles...")
                
                # Create roles
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
                
                # Refresh admin_role
                admin_role = Role.query.filter_by(name='Admin').first()
            else:
                print("✅ Roles already exist")

            # Check if admin user exists
            admin_user = User.query.filter_by(username='admin').first()
            if not admin_user:
                print("Creating admin user...")
                
                # Create admin user
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
                print("📧 Email: admin@inventory.com")
                print("👤 Username: admin")
                print("🔑 Password: Admin123!")
            else:
                print("✅ Admin user already exists")
                # Update password in case it was changed
                admin_user.set_password('Admin123!')
                db.session.commit()
                print("🔑 Password reset to: Admin123!")

            # Verify the user can authenticate
            test_user = User.query.filter_by(username='admin').first()
            if test_user and test_user.check_password('Admin123!'):
                print("✅ Admin user authentication verified!")
                print(f"👤 User ID: {test_user.id}")
                print(f"📧 Email: {test_user.email}")
                print(f"🎭 Role: {test_user.role.name}")
                print(f"✅ Active: {test_user.is_active}")
            else:
                print("❌ Admin user authentication failed!")
                
        except Exception as e:
            print(f"❌ Error creating admin user: {str(e)}")
            db.session.rollback()
            return False
            
        return True

if __name__ == '__main__':
    print("🚀 Creating admin user and roles...")
    success = create_admin_user()
    if success:
        print("\n🎉 Setup completed successfully!")
        print("\n📝 You can now login with:")
        print("   Username: admin")
        print("   Password: Admin123!")
    else:
        print("\n❌ Setup failed!")
        sys.exit(1) 