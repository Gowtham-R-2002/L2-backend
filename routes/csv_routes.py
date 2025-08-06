from flask import Blueprint, request, jsonify, make_response
from flask_jwt_extended import jwt_required
from services.csv_service import CSVService
from io import StringIO

csv_bp = Blueprint('csv', __name__)

@csv_bp.route('/export/products', methods=['GET'])
@jwt_required()
def export_products():
    """Export products to CSV"""
    try:
        csv_content, error = CSVService.export_products()
        
        if error:
            return jsonify({'success': False, 'error': error}), 500
        
        # Create response with CSV content
        response = make_response(csv_content)
        response.headers['Content-Type'] = 'text/csv'
        response.headers['Content-Disposition'] = 'attachment; filename=products_export.csv'
        
        return response
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@csv_bp.route('/export/inventory', methods=['GET'])
@jwt_required()
def export_inventory():
    """Export inventory to CSV"""
    try:
        csv_content, error = CSVService.export_inventory()
        
        if error:
            return jsonify({'success': False, 'error': error}), 500
        
        # Create response with CSV content
        response = make_response(csv_content)
        response.headers['Content-Type'] = 'text/csv'
        response.headers['Content-Disposition'] = 'attachment; filename=inventory_export.csv'
        
        return response
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@csv_bp.route('/export/suppliers', methods=['GET'])
@jwt_required()
def export_suppliers():
    """Export suppliers to CSV"""
    try:
        csv_content, error = CSVService.export_suppliers()
        
        if error:
            return jsonify({'success': False, 'error': error}), 500
        
        # Create response with CSV content
        response = make_response(csv_content)
        response.headers['Content-Type'] = 'text/csv'
        response.headers['Content-Disposition'] = 'attachment; filename=suppliers_export.csv'
        
        return response
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@csv_bp.route('/import/products', methods=['POST'])
@jwt_required()
def import_products():
    """Import products from CSV"""
    try:
        # Check if file was uploaded
        if 'file' not in request.files:
            return jsonify({'success': False, 'error': 'No file uploaded'}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'success': False, 'error': 'No file selected'}), 400
        
        # Check file type
        if not file.filename.endswith('.csv'):
            return jsonify({'success': False, 'error': 'File must be CSV format'}), 400
        
        # Read file content
        csv_content = file.read().decode('utf-8')
        update_existing = request.form.get('update_existing', 'false').lower() == 'true'
        
        # Import products
        results, error = CSVService.import_products(csv_content, update_existing)
        
        if error:
            return jsonify({'success': False, 'error': error}), 500
        
        return jsonify({
            'success': True,
            'message': 'Products imported successfully',
            'results': results
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@csv_bp.route('/import/inventory', methods=['POST'])
@jwt_required()
def import_inventory():
    """Import inventory from CSV"""
    try:
        # Check if file was uploaded
        if 'file' not in request.files:
            return jsonify({'success': False, 'error': 'No file uploaded'}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'success': False, 'error': 'No file selected'}), 400
        
        # Check file type
        if not file.filename.endswith('.csv'):
            return jsonify({'success': False, 'error': 'File must be CSV format'}), 400
        
        # Read file content
        csv_content = file.read().decode('utf-8')
        update_existing = request.form.get('update_existing', 'false').lower() == 'true'
        
        # Import inventory
        results, error = CSVService.import_inventory(csv_content, update_existing)
        
        if error:
            return jsonify({'success': False, 'error': error}), 500
        
        return jsonify({
            'success': True,
            'message': 'Inventory imported successfully',
            'results': results
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@csv_bp.route('/template/<data_type>', methods=['GET'])
@jwt_required()
def get_import_template(data_type):
    """Get CSV template for import"""
    try:
        if data_type not in ['products', 'inventory', 'suppliers']:
            return jsonify({'success': False, 'error': 'Invalid data type'}), 400
        
        csv_content, error = CSVService.get_import_template(data_type)
        
        if error:
            return jsonify({'success': False, 'error': error}), 500
        
        # Create response with CSV template
        response = make_response(csv_content)
        response.headers['Content-Type'] = 'text/csv'
        response.headers['Content-Disposition'] = f'attachment; filename={data_type}_import_template.csv'
        
        return response
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@csv_bp.route('/validate', methods=['POST'])
@jwt_required()
def validate_csv():
    """Validate CSV file before import"""
    try:
        # Check if file was uploaded
        if 'file' not in request.files:
            return jsonify({'success': False, 'error': 'No file uploaded'}), 400
        
        file = request.files['file']
        data_type = request.form.get('data_type')
        
        if not data_type or data_type not in ['products', 'inventory', 'suppliers']:
            return jsonify({'success': False, 'error': 'Invalid data type'}), 400
        
        # Check file type
        if not file.filename.endswith('.csv'):
            return jsonify({'success': False, 'error': 'File must be CSV format'}), 400
        
        # Read and validate file content
        csv_content = file.read().decode('utf-8')
        
        # Basic validation
        import pandas as pd
        import io
        
        df = pd.read_csv(io.StringIO(csv_content))
        
        # Define required columns for each data type
        required_columns = {
            'products': ['name', 'sku'],
            'inventory': ['product_id', 'warehouse_id', 'quantity'],
            'suppliers': ['name']
        }
        
        missing_columns = [col for col in required_columns[data_type] if col not in df.columns]
        
        validation_result = {
            'row_count': len(df),
            'columns': list(df.columns),
            'missing_columns': missing_columns,
            'is_valid': len(missing_columns) == 0,
            'preview': df.head(5).to_dict('records') if len(df) > 0 else []
        }
        
        return jsonify({
            'success': True,
            'validation': validation_result
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500 