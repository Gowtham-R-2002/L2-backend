from flask import Blueprint, request, jsonify
from models import db, Inventory, Product, Warehouse, StockMovement
from sqlalchemy.exc import IntegrityError
from sqlalchemy import and_
from datetime import datetime

inventory_bp = Blueprint('inventory', __name__)

@inventory_bp.route('', methods=['GET'])
def get_inventory():
    """Get inventory with optional filtering"""
    try:
        warehouse_id = request.args.get('warehouse_id', type=int)
        product_id = request.args.get('product_id', type=int)
        low_stock = request.args.get('low_stock', type=bool)
        
        query = Inventory.query
        
        if warehouse_id:
            query = query.filter_by(warehouse_id=warehouse_id)
        
        if product_id:
            query = query.filter_by(product_id=product_id)
        
        if low_stock:
            query = query.filter(Inventory.quantity <= Inventory.reorder_level)
        
        inventory_items = query.all()
        
        return jsonify({
            'success': True,
            'data': [item.to_dict() for item in inventory_items],
            'count': len(inventory_items)
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@inventory_bp.route('/<int:inventory_id>', methods=['GET'])
def get_inventory_item(inventory_id):
    """Get a specific inventory item by ID"""
    try:
        inventory_item = Inventory.query.get_or_404(inventory_id)
        return jsonify({
            'success': True,
            'data': inventory_item.to_dict()
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@inventory_bp.route('', methods=['POST'])
def create_inventory_item():
    """Create a new inventory item"""
    try:
        data = request.get_json()
        
        if not data or not data.get('product_id') or not data.get('warehouse_id'):
            return jsonify({
                'success': False, 
                'error': 'Product ID and Warehouse ID are required'
            }), 400
        
        # Check if product and warehouse exist
        product = Product.query.get(data['product_id'])
        warehouse = Warehouse.query.get(data['warehouse_id'])
        
        if not product:
            return jsonify({'success': False, 'error': 'Product not found'}), 404
        if not warehouse:
            return jsonify({'success': False, 'error': 'Warehouse not found'}), 404
        
        # Check if inventory item already exists
        existing = Inventory.query.filter_by(
            product_id=data['product_id'],
            warehouse_id=data['warehouse_id']
        ).first()
        
        if existing:
            return jsonify({
                'success': False, 
                'error': 'Inventory item already exists for this product-warehouse combination'
            }), 409
        
        inventory_item = Inventory(
            product_id=data['product_id'],
            warehouse_id=data['warehouse_id'],
            quantity=data.get('quantity', 0),
            reorder_level=data.get('reorder_level', 10),
            max_stock_level=data.get('max_stock_level', 1000)
        )
        
        db.session.add(inventory_item)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'data': inventory_item.to_dict(),
            'message': 'Inventory item created successfully'
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

@inventory_bp.route('/<int:inventory_id>', methods=['PUT'])
def update_inventory_item(inventory_id):
    """Update an existing inventory item"""
    try:
        inventory_item = Inventory.query.get_or_404(inventory_id)
        data = request.get_json()
        
        if not data:
            return jsonify({'success': False, 'error': 'No data provided'}), 400
        
        # Update fields
        updatable_fields = ['quantity', 'reorder_level', 'max_stock_level']
        
        for field in updatable_fields:
            if field in data:
                setattr(inventory_item, field, data[field])
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'data': inventory_item.to_dict(),
            'message': 'Inventory item updated successfully'
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

@inventory_bp.route('/adjust', methods=['POST'])
def adjust_inventory():
    """Adjust inventory levels and record stock movement"""
    try:
        data = request.get_json()
        
        required_fields = ['product_id', 'warehouse_id', 'quantity_change', 'movement_type']
        if not data or not all(field in data for field in required_fields):
            return jsonify({
                'success': False, 
                'error': 'Product ID, Warehouse ID, quantity change, and movement type are required'
            }), 400
        
        # Get or create inventory item
        inventory_item = Inventory.query.filter_by(
            product_id=data['product_id'],
            warehouse_id=data['warehouse_id']
        ).first()
        
        if not inventory_item:
            # Create new inventory item if it doesn't exist
            inventory_item = Inventory(
                product_id=data['product_id'],
                warehouse_id=data['warehouse_id'],
                quantity=0,
                reorder_level=data.get('reorder_level', 10),
                max_stock_level=data.get('max_stock_level', 1000)
            )
            db.session.add(inventory_item)
        
        # Update quantity
        new_quantity = inventory_item.quantity + data['quantity_change']
        
        if new_quantity < 0:
            return jsonify({
                'success': False, 
                'error': 'Insufficient stock for this operation'
            }), 400
        
        inventory_item.quantity = new_quantity
        inventory_item.last_updated = datetime.utcnow()
        
        # Record stock movement
        stock_movement = StockMovement(
            product_id=data['product_id'],
            warehouse_id=data['warehouse_id'],
            movement_type=data['movement_type'],
            quantity=abs(data['quantity_change']),
            reference_type=data.get('reference_type'),
            reference_id=data.get('reference_id'),
            notes=data.get('notes')
        )
        
        db.session.add(stock_movement)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'data': {
                'inventory': inventory_item.to_dict(),
                'movement': stock_movement.to_dict()
            },
            'message': 'Inventory adjusted successfully'
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

@inventory_bp.route('/transfer', methods=['POST'])
def transfer_inventory():
    """Transfer inventory between warehouses"""
    try:
        data = request.get_json()
        
        required_fields = ['product_id', 'from_warehouse_id', 'to_warehouse_id', 'quantity']
        if not data or not all(field in data for field in required_fields):
            return jsonify({
                'success': False, 
                'error': 'Product ID, source warehouse, destination warehouse, and quantity are required'
            }), 400
        
        # Get source inventory
        source_inventory = Inventory.query.filter_by(
            product_id=data['product_id'],
            warehouse_id=data['from_warehouse_id']
        ).first()
        
        if not source_inventory or source_inventory.quantity < data['quantity']:
            return jsonify({
                'success': False, 
                'error': 'Insufficient stock in source warehouse'
            }), 400
        
        # Get or create destination inventory
        dest_inventory = Inventory.query.filter_by(
            product_id=data['product_id'],
            warehouse_id=data['to_warehouse_id']
        ).first()
        
        if not dest_inventory:
            dest_inventory = Inventory(
                product_id=data['product_id'],
                warehouse_id=data['to_warehouse_id'],
                quantity=0,
                reorder_level=10,
                max_stock_level=1000
            )
            db.session.add(dest_inventory)
        
        # Update quantities
        source_inventory.quantity -= data['quantity']
        dest_inventory.quantity += data['quantity']
        
        # Record stock movements
        movements = [
            StockMovement(
                product_id=data['product_id'],
                warehouse_id=data['from_warehouse_id'],
                movement_type='out',
                quantity=data['quantity'],
                reference_type='transfer',
                notes=f"Transfer to warehouse {data['to_warehouse_id']}"
            ),
            StockMovement(
                product_id=data['product_id'],
                warehouse_id=data['to_warehouse_id'],
                movement_type='in',
                quantity=data['quantity'],
                reference_type='transfer',
                notes=f"Transfer from warehouse {data['from_warehouse_id']}"
            )
        ]
        
        for movement in movements:
            db.session.add(movement)
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'data': {
                'source_inventory': source_inventory.to_dict(),
                'destination_inventory': dest_inventory.to_dict()
            },
            'message': 'Inventory transferred successfully'
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

@inventory_bp.route('/low-stock', methods=['GET'])
def get_low_stock_items():
    """Get all inventory items with low stock"""
    try:
        low_stock_items = Inventory.query.filter(
            Inventory.quantity <= Inventory.reorder_level
        ).all()
        
        return jsonify({
            'success': True,
            'data': [item.to_dict() for item in low_stock_items],
            'count': len(low_stock_items),
            'message': 'Low stock items retrieved successfully'
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@inventory_bp.route('/movements', methods=['GET'])
def get_stock_movements():
    """Get stock movement history with optional filtering"""
    try:
        product_id = request.args.get('product_id', type=int)
        warehouse_id = request.args.get('warehouse_id', type=int)
        movement_type = request.args.get('movement_type')
        
        query = StockMovement.query
        
        if product_id:
            query = query.filter_by(product_id=product_id)
        
        if warehouse_id:
            query = query.filter_by(warehouse_id=warehouse_id)
        
        if movement_type:
            query = query.filter_by(movement_type=movement_type)
        
        movements = query.order_by(StockMovement.created_at.desc()).all()
        
        return jsonify({
            'success': True,
            'data': [movement.to_dict() for movement in movements],
            'count': len(movements)
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500 