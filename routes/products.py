from flask import Blueprint, request, jsonify
from models import db, Product, Category
from sqlalchemy.exc import IntegrityError
from sqlalchemy import or_

products_bp = Blueprint('products', __name__)

@products_bp.route('', methods=['GET'])
def get_products():
    """Get all products with optional filtering and search"""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = min(request.args.get('per_page', 20, type=int), 100)
        search = request.args.get('search', '')
        category_id = request.args.get('category_id', type=int)
        is_active = request.args.get('is_active', type=bool)
        
        query = Product.query
        
        # Apply filters
        if search:
            query = query.filter(or_(
                Product.name.contains(search),
                Product.description.contains(search),
                Product.sku.contains(search)
            ))
        
        if category_id:
            query = query.filter_by(category_id=category_id)
        
        if is_active is not None:
            query = query.filter_by(is_active=is_active)
        
        # Paginate results
        products = query.paginate(
            page=page, per_page=per_page, error_out=False
        )
        
        return jsonify({
            'success': True,
            'data': [product.to_dict() for product in products.items],
            'pagination': {
                'page': page,
                'per_page': per_page,
                'total': products.total,
                'pages': products.pages,
                'has_next': products.has_next,
                'has_prev': products.has_prev
            }
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@products_bp.route('/<int:product_id>', methods=['GET'])
def get_product(product_id):
    """Get a specific product by ID"""
    try:
        product = Product.query.get_or_404(product_id)
        return jsonify({
            'success': True,
            'data': product.to_dict()
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@products_bp.route('', methods=['POST'])
def create_product():
    """Create a new product"""
    try:
        data = request.get_json()
        
        if not data or not data.get('name') or not data.get('sku'):
            return jsonify({
                'success': False, 
                'error': 'Product name and SKU are required'
            }), 400
        
        # Verify category exists
        if data.get('category_id'):
            category = Category.query.get(data['category_id'])
            if not category:
                return jsonify({
                    'success': False, 
                    'error': 'Category not found'
                }), 404
        
        product = Product(
            name=data['name'],
            description=data.get('description'),
            sku=data['sku'],
            category_id=data.get('category_id'),
            specifications=data.get('specifications'),
            unit_price=data.get('unit_price'),
            is_active=data.get('is_active', True)
        )
        
        db.session.add(product)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'data': product.to_dict(),
            'message': 'Product created successfully'
        }), 201
        
    except IntegrityError:
        db.session.rollback()
        return jsonify({'success': False, 'error': 'SKU already exists'}), 409
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

@products_bp.route('/<int:product_id>', methods=['PUT'])
def update_product(product_id):
    """Update an existing product"""
    try:
        product = Product.query.get_or_404(product_id)
        data = request.get_json()
        
        if not data:
            return jsonify({'success': False, 'error': 'No data provided'}), 400
        
        # Verify category exists if provided
        if 'category_id' in data and data['category_id']:
            category = Category.query.get(data['category_id'])
            if not category:
                return jsonify({
                    'success': False, 
                    'error': 'Category not found'
                }), 404
        
        # Update fields
        updatable_fields = ['name', 'description', 'sku', 'category_id', 
                           'specifications', 'unit_price', 'is_active']
        
        for field in updatable_fields:
            if field in data:
                setattr(product, field, data[field])
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'data': product.to_dict(),
            'message': 'Product updated successfully'
        })
        
    except IntegrityError:
        db.session.rollback()
        return jsonify({'success': False, 'error': 'SKU already exists'}), 409
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

@products_bp.route('/<int:product_id>', methods=['DELETE'])
def delete_product(product_id):
    """Delete a product"""
    try:
        product = Product.query.get_or_404(product_id)
        
        # Check if product has inventory
        if product.inventory_items:
            return jsonify({
                'success': False, 
                'error': 'Cannot delete product with existing inventory'
            }), 409
        
        db.session.delete(product)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Product deleted successfully'
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

@products_bp.route('/by-category/<int:category_id>', methods=['GET'])
def get_products_by_category(category_id):
    """Get all products in a specific category"""
    try:
        category = Category.query.get_or_404(category_id)
        products = Product.query.filter_by(category_id=category_id, is_active=True).all()
        
        return jsonify({
            'success': True,
            'data': [product.to_dict() for product in products],
            'count': len(products),
            'category': category.name
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@products_bp.route('/low-stock', methods=['GET'])
def get_low_stock_products():
    """Get products with low stock levels"""
    try:
        # This will be implemented when we have inventory routes
        # For now, return empty array
        return jsonify({
            'success': True,
            'data': [],
            'message': 'Low stock functionality requires inventory module'
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500 