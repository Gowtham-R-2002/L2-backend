from flask import Blueprint, request, jsonify
from models import db, Supplier
from sqlalchemy.exc import IntegrityError

suppliers_bp = Blueprint('suppliers', __name__)

@suppliers_bp.route('', methods=['GET'])
def get_suppliers():
    """Get all suppliers with optional filtering"""
    try:
        is_active = request.args.get('is_active', type=bool)
        search = request.args.get('search', '')
        
        query = Supplier.query
        
        if is_active is not None:
            query = query.filter_by(is_active=is_active)
        
        if search:
            query = query.filter(
                db.or_(
                    Supplier.name.contains(search),
                    Supplier.contact_person.contains(search),
                    Supplier.email.contains(search)
                )
            )
        
        suppliers = query.all()
        
        return jsonify({
            'success': True,
            'data': [supplier.to_dict() for supplier in suppliers],
            'count': len(suppliers)
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@suppliers_bp.route('/<int:supplier_id>', methods=['GET'])
def get_supplier(supplier_id):
    """Get a specific supplier by ID"""
    try:
        supplier = Supplier.query.get_or_404(supplier_id)
        return jsonify({
            'success': True,
            'data': supplier.to_dict()
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@suppliers_bp.route('', methods=['POST'])
def create_supplier():
    """Create a new supplier"""
    try:
        data = request.get_json()
        
        if not data or not data.get('name'):
            return jsonify({'success': False, 'error': 'Supplier name is required'}), 400
        
        supplier = Supplier(
            name=data['name'],
            contact_person=data.get('contact_person'),
            email=data.get('email'),
            phone=data.get('phone'),
            address=data.get('address'),
            tax_id=data.get('tax_id'),
            payment_terms=data.get('payment_terms'),
            is_active=data.get('is_active', True)
        )
        
        db.session.add(supplier)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'data': supplier.to_dict(),
            'message': 'Supplier created successfully'
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

@suppliers_bp.route('/<int:supplier_id>', methods=['PUT'])
def update_supplier(supplier_id):
    """Update an existing supplier"""
    try:
        supplier = Supplier.query.get_or_404(supplier_id)
        data = request.get_json()
        
        if not data:
            return jsonify({'success': False, 'error': 'No data provided'}), 400
        
        # Update fields
        updatable_fields = ['name', 'contact_person', 'email', 'phone', 
                           'address', 'tax_id', 'payment_terms', 'is_active']
        
        for field in updatable_fields:
            if field in data:
                setattr(supplier, field, data[field])
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'data': supplier.to_dict(),
            'message': 'Supplier updated successfully'
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

@suppliers_bp.route('/<int:supplier_id>', methods=['DELETE'])
def delete_supplier(supplier_id):
    """Delete a supplier"""
    try:
        supplier = Supplier.query.get_or_404(supplier_id)
        
        # Check if supplier has purchase orders
        if supplier.purchase_orders:
            return jsonify({
                'success': False, 
                'error': 'Cannot delete supplier with existing purchase orders'
            }), 409
        
        db.session.delete(supplier)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Supplier deleted successfully'
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

@suppliers_bp.route('/<int:supplier_id>/purchase-orders', methods=['GET'])
def get_supplier_purchase_orders(supplier_id):
    """Get all purchase orders for a specific supplier"""
    try:
        supplier = Supplier.query.get_or_404(supplier_id)
        
        return jsonify({
            'success': True,
            'data': [po.to_dict() for po in supplier.purchase_orders],
            'supplier': supplier.name,
            'count': len(supplier.purchase_orders)
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500 