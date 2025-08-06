import pandas as pd
import io
import os
from flask import current_app
from models import db, Product, Category, Warehouse, Inventory, Supplier
from datetime import datetime

class CSVService:
    
    @staticmethod
    def export_products():
        """Export products to CSV format"""
        try:
            products = Product.query.all()
            
            data = []
            for product in products:
                data.append({
                    'id': product.id,
                    'name': product.name,
                    'description': product.description,
                    'sku': product.sku,
                    'barcode': product.barcode,
                    'category_id': product.category_id,
                    'category_name': product.category.name if product.category else '',
                    'unit_price': float(product.unit_price) if product.unit_price else None,
                    'is_active': product.is_active,
                    'created_at': product.created_at.isoformat() if product.created_at else None,
                    'specifications': str(product.specifications) if product.specifications else ''
                })
            
            df = pd.DataFrame(data)
            
            # Convert to CSV
            output = io.StringIO()
            df.to_csv(output, index=False)
            csv_content = output.getvalue()
            output.close()
            
            return csv_content, None
            
        except Exception as e:
            current_app.logger.error(f"Product export error: {str(e)}")
            return None, str(e)
    
    @staticmethod
    def import_products(csv_content, update_existing=False):
        """Import products from CSV content"""
        try:
            # Read CSV content
            df = pd.read_csv(io.StringIO(csv_content))
            
            # Validate required columns
            required_columns = ['name', 'sku']
            missing_columns = [col for col in required_columns if col not in df.columns]
            if missing_columns:
                return None, f"Missing required columns: {', '.join(missing_columns)}"
            
            results = {
                'created': 0,
                'updated': 0,
                'errors': []
            }
            
            for index, row in df.iterrows():
                try:
                    # Check if product exists
                    existing_product = Product.query.filter_by(sku=row['sku']).first()
                    
                    if existing_product and not update_existing:
                        results['errors'].append(f"Row {index + 1}: Product with SKU '{row['sku']}' already exists")
                        continue
                    
                    # Validate category
                    category_id = None
                    if pd.notna(row.get('category_id')):
                        category_id = int(row['category_id'])
                        if not Category.query.get(category_id):
                            results['errors'].append(f"Row {index + 1}: Category ID {category_id} not found")
                            continue
                    elif pd.notna(row.get('category_name')):
                        category = Category.query.filter_by(name=row['category_name']).first()
                        if category:
                            category_id = category.id
                        else:
                            results['errors'].append(f"Row {index + 1}: Category '{row['category_name']}' not found")
                            continue
                    
                    # Prepare product data
                    product_data = {
                        'name': row['name'],
                        'description': row.get('description', ''),
                        'sku': row['sku'],
                        'barcode': row.get('barcode') if pd.notna(row.get('barcode')) else None,
                        'category_id': category_id,
                        'unit_price': float(row['unit_price']) if pd.notna(row.get('unit_price')) else None,
                        'is_active': bool(row.get('is_active', True))
                    }
                    
                    if existing_product:
                        # Update existing product
                        for key, value in product_data.items():
                            setattr(existing_product, key, value)
                        results['updated'] += 1
                    else:
                        # Create new product
                        product = Product(**product_data)
                        db.session.add(product)
                        results['created'] += 1
                
                except Exception as e:
                    results['errors'].append(f"Row {index + 1}: {str(e)}")
            
            db.session.commit()
            return results, None
            
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Product import error: {str(e)}")
            return None, str(e)
    
    @staticmethod
    def export_inventory():
        """Export inventory to CSV format"""
        try:
            inventory_items = Inventory.query.all()
            
            data = []
            for item in inventory_items:
                data.append({
                    'id': item.id,
                    'product_id': item.product_id,
                    'product_name': item.product.name if item.product else '',
                    'product_sku': item.product.sku if item.product else '',
                    'warehouse_id': item.warehouse_id,
                    'warehouse_name': item.warehouse.name if item.warehouse else '',
                    'quantity': item.quantity,
                    'reorder_level': item.reorder_level,
                    'max_stock_level': item.max_stock_level,
                    'is_low_stock': item.quantity <= item.reorder_level,
                    'last_updated': item.last_updated.isoformat() if item.last_updated else None
                })
            
            df = pd.DataFrame(data)
            
            # Convert to CSV
            output = io.StringIO()
            df.to_csv(output, index=False)
            csv_content = output.getvalue()
            output.close()
            
            return csv_content, None
            
        except Exception as e:
            current_app.logger.error(f"Inventory export error: {str(e)}")
            return None, str(e)
    
    @staticmethod
    def import_inventory(csv_content, update_existing=False):
        """Import inventory from CSV content"""
        try:
            # Read CSV content
            df = pd.read_csv(io.StringIO(csv_content))
            
            # Validate required columns
            required_columns = ['product_id', 'warehouse_id', 'quantity']
            missing_columns = [col for col in required_columns if col not in df.columns]
            if missing_columns:
                return None, f"Missing required columns: {', '.join(missing_columns)}"
            
            results = {
                'created': 0,
                'updated': 0,
                'errors': []
            }
            
            for index, row in df.iterrows():
                try:
                    # Validate product and warehouse
                    product_id = int(row['product_id'])
                    warehouse_id = int(row['warehouse_id'])
                    
                    if not Product.query.get(product_id):
                        results['errors'].append(f"Row {index + 1}: Product ID {product_id} not found")
                        continue
                    
                    if not Warehouse.query.get(warehouse_id):
                        results['errors'].append(f"Row {index + 1}: Warehouse ID {warehouse_id} not found")
                        continue
                    
                    # Check if inventory item exists
                    existing_item = Inventory.query.filter_by(
                        product_id=product_id,
                        warehouse_id=warehouse_id
                    ).first()
                    
                    if existing_item and not update_existing:
                        results['errors'].append(f"Row {index + 1}: Inventory item already exists for product {product_id} in warehouse {warehouse_id}")
                        continue
                    
                    # Prepare inventory data
                    inventory_data = {
                        'product_id': product_id,
                        'warehouse_id': warehouse_id,
                        'quantity': int(row['quantity']),
                        'reorder_level': int(row.get('reorder_level', 10)),
                        'max_stock_level': int(row.get('max_stock_level', 1000))
                    }
                    
                    if existing_item:
                        # Update existing inventory
                        for key, value in inventory_data.items():
                            setattr(existing_item, key, value)
                        existing_item.last_updated = datetime.utcnow()
                        results['updated'] += 1
                    else:
                        # Create new inventory item
                        inventory_item = Inventory(**inventory_data)
                        db.session.add(inventory_item)
                        results['created'] += 1
                
                except Exception as e:
                    results['errors'].append(f"Row {index + 1}: {str(e)}")
            
            db.session.commit()
            return results, None
            
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Inventory import error: {str(e)}")
            return None, str(e)
    
    @staticmethod
    def export_suppliers():
        """Export suppliers to CSV format"""
        try:
            suppliers = Supplier.query.all()
            
            data = []
            for supplier in suppliers:
                data.append({
                    'id': supplier.id,
                    'name': supplier.name,
                    'contact_person': supplier.contact_person,
                    'email': supplier.email,
                    'phone': supplier.phone,
                    'address': supplier.address,
                    'tax_id': supplier.tax_id,
                    'payment_terms': supplier.payment_terms,
                    'is_active': supplier.is_active,
                    'created_at': supplier.created_at.isoformat() if supplier.created_at else None
                })
            
            df = pd.DataFrame(data)
            
            # Convert to CSV
            output = io.StringIO()
            df.to_csv(output, index=False)
            csv_content = output.getvalue()
            output.close()
            
            return csv_content, None
            
        except Exception as e:
            current_app.logger.error(f"Supplier export error: {str(e)}")
            return None, str(e)
    
    @staticmethod
    def get_import_template(data_type):
        """Generate CSV template for import"""
        try:
            if data_type == 'products':
                template_data = {
                    'name': ['Example Product 1', 'Example Product 2'],
                    'description': ['Product description 1', 'Product description 2'],
                    'sku': ['PROD001', 'PROD002'],
                    'barcode': ['1234567890123', '1234567890124'],
                    'category_id': [1, 1],
                    'unit_price': [29.99, 39.99],
                    'is_active': [True, True]
                }
            elif data_type == 'inventory':
                template_data = {
                    'product_id': [1, 2],
                    'warehouse_id': [1, 1],
                    'quantity': [100, 50],
                    'reorder_level': [10, 15],
                    'max_stock_level': [500, 200]
                }
            elif data_type == 'suppliers':
                template_data = {
                    'name': ['Supplier Company 1', 'Supplier Company 2'],
                    'contact_person': ['John Doe', 'Jane Smith'],
                    'email': ['contact@supplier1.com', 'contact@supplier2.com'],
                    'phone': ['+1-555-0123', '+1-555-0456'],
                    'address': ['123 Supplier St, City, State', '456 Vendor Ave, City, State'],
                    'tax_id': ['TAX123456', 'TAX789012'],
                    'payment_terms': ['Net 30', 'Net 45'],
                    'is_active': [True, True]
                }
            else:
                return None, "Invalid data type"
            
            df = pd.DataFrame(template_data)
            
            # Convert to CSV
            output = io.StringIO()
            df.to_csv(output, index=False)
            csv_content = output.getvalue()
            output.close()
            
            return csv_content, None
            
        except Exception as e:
            current_app.logger.error(f"Template generation error: {str(e)}")
            return None, str(e) 