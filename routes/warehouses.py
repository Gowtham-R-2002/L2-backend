from flask import Blueprint, request, jsonify
from models import db, Warehouse
from sqlalchemy.exc import IntegrityError

warehouses_bp = Blueprint('warehouses', __name__)

@warehouses_bp.route('', methods=['GET'])
def get_warehouses():
    """Get all warehouses"""
    try:
        is_active = request.args.get('is_active', type=bool)
        
        query = Warehouse.query
        if is_active is not None:
            query = query.filter_by(is_active=is_active)
        
        warehouses = query.all()
        
        return jsonify({
            'success': True,
            'data': [warehouse.to_dict() for warehouse in warehouses],
            'count': len(warehouses)
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@warehouses_bp.route('/<int:warehouse_id>', methods=['GET'])
def get_warehouse(warehouse_id):
    """Get a specific warehouse by ID"""
    try:
        warehouse = Warehouse.query.get_or_404(warehouse_id)
        return jsonify({
            'success': True,
            'data': warehouse.to_dict()
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@warehouses_bp.route('', methods=['POST'])
def create_warehouse():
    """Create a new warehouse"""
    try:
        data = request.get_json()
        
        if not data or not data.get('name'):
            return jsonify({'success': False, 'error': 'Warehouse name is required'}), 400
        
        warehouse = Warehouse(
            name=data['name'],
            location=data.get('location'),
            address=data.get('address'),
            contact_info=data.get('contact_info'),
            is_active=data.get('is_active', True)
        )
        
        db.session.add(warehouse)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'data': warehouse.to_dict(),
            'message': 'Warehouse created successfully'
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

@warehouses_bp.route('/<int:warehouse_id>', methods=['PUT'])
def update_warehouse(warehouse_id):
    """Update an existing warehouse"""
    try:
        warehouse = Warehouse.query.get_or_404(warehouse_id)
        data = request.get_json()
        
        if not data:
            return jsonify({'success': False, 'error': 'No data provided'}), 400
        
        # Update fields
        updatable_fields = ['name', 'location', 'address', 'contact_info', 'is_active']
        
        for field in updatable_fields:
            if field in data:
                setattr(warehouse, field, data[field])
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'data': warehouse.to_dict(),
            'message': 'Warehouse updated successfully'
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

@warehouses_bp.route('/<int:warehouse_id>', methods=['DELETE'])
def delete_warehouse(warehouse_id):
    """Delete a warehouse"""
    try:
        warehouse = Warehouse.query.get_or_404(warehouse_id)
        
        # Check if warehouse has inventory
        if warehouse.inventory_items:
            return jsonify({
                'success': False, 
                'error': 'Cannot delete warehouse with existing inventory'
            }), 409
        
        db.session.delete(warehouse)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Warehouse deleted successfully'
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

@warehouses_bp.route('/<int:warehouse_id>/inventory', methods=['GET'])
def get_warehouse_inventory(warehouse_id):
    """Get inventory for a specific warehouse"""
    try:
        warehouse = Warehouse.query.get_or_404(warehouse_id)
        
        return jsonify({
            'success': True,
            'data': [item.to_dict() for item in warehouse.inventory_items],
            'warehouse': warehouse.name,
            'message': 'Warehouse inventory retrieved successfully'
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500 