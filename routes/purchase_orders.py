from flask import Blueprint, request, jsonify
from models import db, PurchaseOrder, PurchaseOrderItem, Supplier, Product, Inventory, StockMovement
from sqlalchemy.exc import IntegrityError
from datetime import datetime
import uuid

purchase_orders_bp = Blueprint('purchase_orders', __name__)

def generate_order_number():
    """Generate a unique order number"""
    timestamp = datetime.now().strftime('%Y%m%d')
    unique_id = str(uuid.uuid4())[:8].upper()
    return f"PO-{timestamp}-{unique_id}"

@purchase_orders_bp.route('', methods=['GET'])
def get_purchase_orders():
    """Get all purchase orders with optional filtering"""
    try:
        supplier_id = request.args.get('supplier_id', type=int)
        status = request.args.get('status')
        page = request.args.get('page', 1, type=int)
        per_page = min(request.args.get('per_page', 20, type=int), 100)
        
        query = PurchaseOrder.query
        
        if supplier_id:
            query = query.filter_by(supplier_id=supplier_id)
        
        if status:
            query = query.filter_by(status=status)
        
        # Paginate results
        purchase_orders = query.order_by(PurchaseOrder.created_at.desc()).paginate(
            page=page, per_page=per_page, error_out=False
        )
        
        return jsonify({
            'success': True,
            'data': [po.to_dict() for po in purchase_orders.items],
            'pagination': {
                'page': page,
                'per_page': per_page,
                'total': purchase_orders.total,
                'pages': purchase_orders.pages,
                'has_next': purchase_orders.has_next,
                'has_prev': purchase_orders.has_prev
            }
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@purchase_orders_bp.route('/<int:po_id>', methods=['GET'])
def get_purchase_order(po_id):
    """Get a specific purchase order by ID"""
    try:
        purchase_order = PurchaseOrder.query.get_or_404(po_id)
        po_data = purchase_order.to_dict()
        po_data['items'] = [item.to_dict() for item in purchase_order.items]
        
        return jsonify({
            'success': True,
            'data': po_data
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@purchase_orders_bp.route('', methods=['POST'])
def create_purchase_order():
    """Create a new purchase order"""
    try:
        data = request.get_json()
        
        if not data or not data.get('supplier_id') or not data.get('items'):
            return jsonify({
                'success': False, 
                'error': 'Supplier ID and items are required'
            }), 400
        
        # Verify supplier exists
        supplier = Supplier.query.get(data['supplier_id'])
        if not supplier:
            return jsonify({'success': False, 'error': 'Supplier not found'}), 404
        
        # Create purchase order
        purchase_order = PurchaseOrder(
            order_number=generate_order_number(),
            supplier_id=data['supplier_id'],
            status='pending',
            expected_delivery=datetime.fromisoformat(data['expected_delivery']) if data.get('expected_delivery') else None,
            notes=data.get('notes')
        )
        
        db.session.add(purchase_order)
        db.session.flush()  # Get the ID
        
        total_amount = 0
        
        # Create purchase order items
        for item_data in data['items']:
            if not item_data.get('product_id') or not item_data.get('quantity') or not item_data.get('unit_price'):
                return jsonify({
                    'success': False, 
                    'error': 'Product ID, quantity, and unit price are required for all items'
                }), 400
            
            # Verify product exists
            product = Product.query.get(item_data['product_id'])
            if not product:
                return jsonify({
                    'success': False, 
                    'error': f"Product with ID {item_data['product_id']} not found"
                }), 404
            
            po_item = PurchaseOrderItem(
                purchase_order_id=purchase_order.id,
                product_id=item_data['product_id'],
                quantity=item_data['quantity'],
                unit_price=item_data['unit_price']
            )
            
            db.session.add(po_item)
            total_amount += item_data['quantity'] * item_data['unit_price']
        
        purchase_order.total_amount = total_amount
        db.session.commit()
        
        # Get complete data with items
        po_data = purchase_order.to_dict()
        po_data['items'] = [item.to_dict() for item in purchase_order.items]
        
        return jsonify({
            'success': True,
            'data': po_data,
            'message': 'Purchase order created successfully'
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

@purchase_orders_bp.route('/<int:po_id>', methods=['PUT'])
def update_purchase_order(po_id):
    """Update an existing purchase order"""
    try:
        purchase_order = PurchaseOrder.query.get_or_404(po_id)
        data = request.get_json()
        
        if not data:
            return jsonify({'success': False, 'error': 'No data provided'}), 400
        
        # Only allow updates for pending orders
        if purchase_order.status not in ['pending', 'approved']:
            return jsonify({
                'success': False, 
                'error': 'Cannot update purchase order in current status'
            }), 409
        
        # Update basic fields
        updatable_fields = ['status', 'expected_delivery', 'notes']
        
        for field in updatable_fields:
            if field in data:
                if field == 'expected_delivery' and data[field]:
                    setattr(purchase_order, field, datetime.fromisoformat(data[field]))
                else:
                    setattr(purchase_order, field, data[field])
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'data': purchase_order.to_dict(),
            'message': 'Purchase order updated successfully'
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

@purchase_orders_bp.route('/<int:po_id>/approve', methods=['POST'])
def approve_purchase_order(po_id):
    """Approve a purchase order"""
    try:
        purchase_order = PurchaseOrder.query.get_or_404(po_id)
        
        if purchase_order.status != 'pending':
            return jsonify({
                'success': False, 
                'error': 'Can only approve pending purchase orders'
            }), 409
        
        purchase_order.status = 'approved'
        db.session.commit()
        
        return jsonify({
            'success': True,
            'data': purchase_order.to_dict(),
            'message': 'Purchase order approved successfully'
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

@purchase_orders_bp.route('/<int:po_id>/receive', methods=['POST'])
def receive_purchase_order(po_id):
    """Receive items from a purchase order and update inventory"""
    try:
        data = request.get_json()
        purchase_order = PurchaseOrder.query.get_or_404(po_id)
        
        if purchase_order.status not in ['approved', 'ordered']:
            return jsonify({
                'success': False, 
                'error': 'Can only receive from approved or ordered purchase orders'
            }), 409
        
        if not data or not data.get('warehouse_id') or not data.get('received_items'):
            return jsonify({
                'success': False, 
                'error': 'Warehouse ID and received items are required'
            }), 400
        
        # Process received items
        for received_item in data['received_items']:
            po_item_id = received_item.get('po_item_id')
            received_quantity = received_item.get('received_quantity', 0)
            
            if not po_item_id or received_quantity <= 0:
                continue
            
            po_item = PurchaseOrderItem.query.get(po_item_id)
            if not po_item or po_item.purchase_order_id != po_id:
                continue
            
            # Update received quantity
            po_item.received_quantity += received_quantity
            
            # Update inventory
            inventory_item = Inventory.query.filter_by(
                product_id=po_item.product_id,
                warehouse_id=data['warehouse_id']
            ).first()
            
            if not inventory_item:
                inventory_item = Inventory(
                    product_id=po_item.product_id,
                    warehouse_id=data['warehouse_id'],
                    quantity=0,
                    reorder_level=10,
                    max_stock_level=1000
                )
                db.session.add(inventory_item)
            
            inventory_item.quantity += received_quantity
            
            # Record stock movement
            stock_movement = StockMovement(
                product_id=po_item.product_id,
                warehouse_id=data['warehouse_id'],
                movement_type='in',
                quantity=received_quantity,
                reference_type='purchase_order',
                reference_id=po_id,
                notes=f"Received from PO {purchase_order.order_number}"
            )
            db.session.add(stock_movement)
        
        # Check if all items are fully received
        all_received = all(
            item.received_quantity >= item.quantity 
            for item in purchase_order.items
        )
        
        if all_received:
            purchase_order.status = 'received'
            purchase_order.actual_delivery = datetime.utcnow()
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'data': purchase_order.to_dict(),
            'message': 'Items received and inventory updated successfully'
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

@purchase_orders_bp.route('/<int:po_id>/cancel', methods=['POST'])
def cancel_purchase_order(po_id):
    """Cancel a purchase order"""
    try:
        purchase_order = PurchaseOrder.query.get_or_404(po_id)
        
        if purchase_order.status in ['received', 'cancelled']:
            return jsonify({
                'success': False, 
                'error': 'Cannot cancel purchase order in current status'
            }), 409
        
        purchase_order.status = 'cancelled'
        db.session.commit()
        
        return jsonify({
            'success': True,
            'data': purchase_order.to_dict(),
            'message': 'Purchase order cancelled successfully'
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500 