from flask import Blueprint, request, jsonify
from models import db, Category
from sqlalchemy.exc import IntegrityError

categories_bp = Blueprint('categories', __name__)

@categories_bp.route('', methods=['GET'])
def get_categories():
    """Get all categories with optional filtering"""
    try:
        categories = Category.query.filter_by(parent_id=None).all()
        return jsonify({
            'success': True,
            'data': [category.to_dict() for category in categories],
            'count': len(categories)
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@categories_bp.route('/<int:category_id>', methods=['GET'])
def get_category(category_id):
    """Get a specific category by ID"""
    try:
        category = Category.query.get_or_404(category_id)
        return jsonify({
            'success': True,
            'data': category.to_dict()
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@categories_bp.route('', methods=['POST'])
def create_category():
    """Create a new category"""
    try:
        data = request.get_json()
        
        if not data or not data.get('name'):
            return jsonify({'success': False, 'error': 'Category name is required'}), 400
        
        category = Category(
            name=data['name'],
            description=data.get('description'),
            parent_id=data.get('parent_id')
        )
        
        db.session.add(category)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'data': category.to_dict(),
            'message': 'Category created successfully'
        }), 201
        
    except IntegrityError:
        db.session.rollback()
        return jsonify({'success': False, 'error': 'Category name already exists'}), 409
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

@categories_bp.route('/<int:category_id>', methods=['PUT'])
def update_category(category_id):
    """Update an existing category"""
    try:
        category = Category.query.get_or_404(category_id)
        data = request.get_json()
        
        if not data:
            return jsonify({'success': False, 'error': 'No data provided'}), 400
        
        if 'name' in data:
            category.name = data['name']
        if 'description' in data:
            category.description = data['description']
        if 'parent_id' in data:
            category.parent_id = data['parent_id']
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'data': category.to_dict(),
            'message': 'Category updated successfully'
        })
        
    except IntegrityError:
        db.session.rollback()
        return jsonify({'success': False, 'error': 'Category name already exists'}), 409
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

@categories_bp.route('/<int:category_id>', methods=['DELETE'])
def delete_category(category_id):
    """Delete a category"""
    try:
        category = Category.query.get_or_404(category_id)
        
        # Check if category has products
        if category.products:
            return jsonify({
                'success': False, 
                'error': 'Cannot delete category with existing products'
            }), 409
        
        # Check if category has subcategories
        if category.children:
            return jsonify({
                'success': False, 
                'error': 'Cannot delete category with subcategories'
            }), 409
        
        db.session.delete(category)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Category deleted successfully'
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

@categories_bp.route('/<int:category_id>/subcategories', methods=['GET'])
def get_subcategories(category_id):
    """Get all subcategories of a specific category"""
    try:
        category = Category.query.get_or_404(category_id)
        subcategories = Category.query.filter_by(parent_id=category_id).all()
        
        return jsonify({
            'success': True,
            'data': [subcat.to_dict() for subcat in subcategories],
            'count': len(subcategories),
            'parent_category': category.name
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500 