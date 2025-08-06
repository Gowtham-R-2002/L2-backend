from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required
from models import db, Product, Inventory, StockMovement
from datetime import datetime

barcode_bp = Blueprint('barcode', __name__)

@barcode_bp.route('/lookup', methods=['POST'])
@jwt_required()
def lookup_product():
    """Look up product by barcode"""
    try:
        data = request.get_json()
        
        if not data or not data.get('barcode'):
            return jsonify({'success': False, 'error': 'Barcode is required'}), 400
        
        barcode = data['barcode']
        
        # Find product by barcode
        product = Product.query.filter_by(barcode=barcode).first()
        
        if not product:
            return jsonify({
                'success': False,
                'error': 'Product not found',
                'barcode': barcode
            }), 404
        
        # Get inventory information
        inventory_items = Inventory.query.filter_by(product_id=product.id).all()
        
        inventory_data = []
        total_quantity = 0
        
        for item in inventory_items:
            inventory_data.append({
                'warehouse_id': item.warehouse_id,
                'warehouse_name': item.warehouse.name,
                'quantity': item.quantity,
                'reorder_level': item.reorder_level,
                'is_low_stock': item.quantity <= item.reorder_level
            })
            total_quantity += item.quantity
        
        return jsonify({
            'success': True,
            'product': product.to_dict(),
            'inventory': inventory_data,
            'total_quantity': total_quantity
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@barcode_bp.route('/scan-receive', methods=['POST'])
@jwt_required()
def scan_receive():
    """Receive inventory using barcode scan"""
    try:
        data = request.get_json()
        
        required_fields = ['barcode', 'warehouse_id', 'quantity']
        if not data or not all(field in data for field in required_fields):
            return jsonify({'success': False, 'error': 'Barcode, warehouse_id, and quantity are required'}), 400
        
        barcode = data['barcode']
        warehouse_id = data['warehouse_id']
        quantity = int(data['quantity'])
        
        if quantity <= 0:
            return jsonify({'success': False, 'error': 'Quantity must be greater than 0'}), 400
        
        # Find product by barcode
        product = Product.query.filter_by(barcode=barcode).first()
        if not product:
            return jsonify({'success': False, 'error': 'Product not found'}), 404
        
        # Get or create inventory item
        inventory_item = Inventory.query.filter_by(
            product_id=product.id,
            warehouse_id=warehouse_id
        ).first()
        
        if not inventory_item:
            inventory_item = Inventory(
                product_id=product.id,
                warehouse_id=warehouse_id,
                quantity=0,
                reorder_level=10,
                max_stock_level=1000
            )
            db.session.add(inventory_item)
        
        # Update inventory
        old_quantity = inventory_item.quantity
        inventory_item.quantity += quantity
        inventory_item.last_updated = datetime.utcnow()
        
        # Record stock movement
        stock_movement = StockMovement(
            product_id=product.id,
            warehouse_id=warehouse_id,
            movement_type='in',
            quantity=quantity,
            reference_type='barcode_scan',
            notes=f"Barcode scan receive: {barcode}"
        )
        
        db.session.add(stock_movement)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Inventory received successfully',
            'product': product.to_dict(),
            'inventory': inventory_item.to_dict(),
            'old_quantity': old_quantity,
            'new_quantity': inventory_item.quantity,
            'received_quantity': quantity
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

@barcode_bp.route('/scan-issue', methods=['POST'])
@jwt_required()
def scan_issue():
    """Issue inventory using barcode scan"""
    try:
        data = request.get_json()
        
        required_fields = ['barcode', 'warehouse_id', 'quantity']
        if not data or not all(field in data for field in required_fields):
            return jsonify({'success': False, 'error': 'Barcode, warehouse_id, and quantity are required'}), 400
        
        barcode = data['barcode']
        warehouse_id = data['warehouse_id']
        quantity = int(data['quantity'])
        
        if quantity <= 0:
            return jsonify({'success': False, 'error': 'Quantity must be greater than 0'}), 400
        
        # Find product by barcode
        product = Product.query.filter_by(barcode=barcode).first()
        if not product:
            return jsonify({'success': False, 'error': 'Product not found'}), 404
        
        # Get inventory item
        inventory_item = Inventory.query.filter_by(
            product_id=product.id,
            warehouse_id=warehouse_id
        ).first()
        
        if not inventory_item:
            return jsonify({'success': False, 'error': 'No inventory found for this product in the warehouse'}), 404
        
        if inventory_item.quantity < quantity:
            return jsonify({
                'success': False,
                'error': f'Insufficient stock. Available: {inventory_item.quantity}, Requested: {quantity}'
            }), 400
        
        # Update inventory
        old_quantity = inventory_item.quantity
        inventory_item.quantity -= quantity
        inventory_item.last_updated = datetime.utcnow()
        
        # Record stock movement
        stock_movement = StockMovement(
            product_id=product.id,
            warehouse_id=warehouse_id,
            movement_type='out',
            quantity=quantity,
            reference_type='barcode_scan',
            notes=f"Barcode scan issue: {barcode}"
        )
        
        db.session.add(stock_movement)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Inventory issued successfully',
            'product': product.to_dict(),
            'inventory': inventory_item.to_dict(),
            'old_quantity': old_quantity,
            'new_quantity': inventory_item.quantity,
            'issued_quantity': quantity
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

@barcode_bp.route('/scan-count', methods=['POST'])
@jwt_required()
def scan_count():
    """Perform stock count using barcode scan"""
    try:
        data = request.get_json()
        
        required_fields = ['barcode', 'warehouse_id', 'counted_quantity']
        if not data or not all(field in data for field in required_fields):
            return jsonify({'success': False, 'error': 'Barcode, warehouse_id, and counted_quantity are required'}), 400
        
        barcode = data['barcode']
        warehouse_id = data['warehouse_id']
        counted_quantity = int(data['counted_quantity'])
        
        if counted_quantity < 0:
            return jsonify({'success': False, 'error': 'Counted quantity cannot be negative'}), 400
        
        # Find product by barcode
        product = Product.query.filter_by(barcode=barcode).first()
        if not product:
            return jsonify({'success': False, 'error': 'Product not found'}), 404
        
        # Get or create inventory item
        inventory_item = Inventory.query.filter_by(
            product_id=product.id,
            warehouse_id=warehouse_id
        ).first()
        
        if not inventory_item:
            inventory_item = Inventory(
                product_id=product.id,
                warehouse_id=warehouse_id,
                quantity=0,
                reorder_level=10,
                max_stock_level=1000
            )
            db.session.add(inventory_item)
        
        # Calculate adjustment
        old_quantity = inventory_item.quantity
        adjustment = counted_quantity - old_quantity
        
        # Update inventory
        inventory_item.quantity = counted_quantity
        inventory_item.last_updated = datetime.utcnow()
        
        # Record stock movement if there's an adjustment
        if adjustment != 0:
            stock_movement = StockMovement(
                product_id=product.id,
                warehouse_id=warehouse_id,
                movement_type='adjustment',
                quantity=abs(adjustment),
                reference_type='barcode_count',
                notes=f"Stock count adjustment: {barcode}. Old: {old_quantity}, New: {counted_quantity}"
            )
            
            db.session.add(stock_movement)
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Stock count completed successfully',
            'product': product.to_dict(),
            'inventory': inventory_item.to_dict(),
            'old_quantity': old_quantity,
            'counted_quantity': counted_quantity,
            'adjustment': adjustment
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

@barcode_bp.route('/generate', methods=['POST'])
@jwt_required()
def generate_barcode():
    """Generate barcode for a product"""
    try:
        data = request.get_json()
        
        if not data or not data.get('product_id'):
            return jsonify({'success': False, 'error': 'Product ID is required'}), 400
        
        product_id = data['product_id']
        product = Product.query.get_or_404(product_id)
        
        # Generate barcode if not exists
        if not product.barcode:
            # Simple barcode generation based on product ID and timestamp
            import time
            timestamp = str(int(time.time()))[-6:]  # Last 6 digits of timestamp
            barcode = f"{product_id:06d}{timestamp}"
            
            # Ensure uniqueness
            while Product.query.filter_by(barcode=barcode).first():
                timestamp = str(int(time.time()))[-6:]
                barcode = f"{product_id:06d}{timestamp}"
            
            product.barcode = barcode
            db.session.commit()
        
        return jsonify({
            'success': True,
            'product': product.to_dict(),
            'barcode': product.barcode
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

@barcode_bp.route('/history', methods=['GET'])
@jwt_required()
def get_barcode_history():
    """Get barcode scan history"""
    try:
        barcode = request.args.get('barcode')
        days = request.args.get('days', 30, type=int)
        
        if not barcode:
            return jsonify({'success': False, 'error': 'Barcode parameter is required'}), 400
        
        # Find product by barcode
        product = Product.query.filter_by(barcode=barcode).first()
        if not product:
            return jsonify({'success': False, 'error': 'Product not found'}), 404
        
        # Get stock movements for this product in the last N days
        from datetime import datetime, timedelta
        start_date = datetime.utcnow() - timedelta(days=days)
        
        movements = StockMovement.query.filter(
            StockMovement.product_id == product.id,
            StockMovement.reference_type == 'barcode_scan',
            StockMovement.created_at >= start_date
        ).order_by(StockMovement.created_at.desc()).all()
        
        return jsonify({
            'success': True,
            'product': product.to_dict(),
            'barcode': barcode,
            'movements': [movement.to_dict() for movement in movements],
            'count': len(movements),
            'period_days': days
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500 