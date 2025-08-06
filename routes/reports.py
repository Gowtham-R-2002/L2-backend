from flask import Blueprint, request, jsonify
from models import db, Product, Inventory, StockMovement, PurchaseOrder, Warehouse
from sqlalchemy import func, desc, and_
from datetime import datetime, timedelta

reports_bp = Blueprint('reports', __name__)

@reports_bp.route('/dashboard', methods=['GET'])
def get_dashboard_summary():
    """Get dashboard summary statistics"""
    try:
        # Total products
        total_products = Product.query.filter_by(is_active=True).count()
        
        # Total warehouses
        total_warehouses = Warehouse.query.filter_by(is_active=True).count()
        
        # Low stock items count
        low_stock_count = db.session.query(Inventory).filter(
            Inventory.quantity <= Inventory.reorder_level
        ).count()
        
        # Pending purchase orders
        pending_pos = PurchaseOrder.query.filter_by(status='pending').count()
        
        # Total inventory value (approximation using unit_price)
        inventory_value = db.session.query(
            func.sum(Inventory.quantity * Product.unit_price)
        ).join(Product).filter(Product.unit_price.isnot(None)).scalar() or 0
        
        # Recent stock movements (last 7 days)
        seven_days_ago = datetime.utcnow() - timedelta(days=7)
        recent_movements = StockMovement.query.filter(
            StockMovement.created_at >= seven_days_ago
        ).count()
        
        return jsonify({
            'success': True,
            'data': {
                'total_products': total_products,
                'total_warehouses': total_warehouses,
                'low_stock_items': low_stock_count,
                'pending_purchase_orders': pending_pos,
                'total_inventory_value': float(inventory_value),
                'recent_movements': recent_movements
            }
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@reports_bp.route('/inventory-turnover', methods=['GET'])
def get_inventory_turnover():
    """Get inventory turnover analysis"""
    try:
        days = request.args.get('days', 30, type=int)
        start_date = datetime.utcnow() - timedelta(days=days)
        
        # Get products with movement data
        turnover_data = db.session.query(
            Product.id,
            Product.name,
            Product.sku,
            func.sum(StockMovement.quantity).label('total_movement'),
            func.avg(Inventory.quantity).label('avg_inventory')
        ).join(StockMovement, Product.id == StockMovement.product_id)\
         .join(Inventory, Product.id == Inventory.product_id)\
         .filter(StockMovement.created_at >= start_date)\
         .filter(StockMovement.movement_type == 'out')\
         .group_by(Product.id, Product.name, Product.sku)\
         .all()
        
        results = []
        for row in turnover_data:
            turnover_rate = (row.total_movement / row.avg_inventory) if row.avg_inventory > 0 else 0
            results.append({
                'product_id': row.id,
                'product_name': row.name,
                'sku': row.sku,
                'total_movement': int(row.total_movement),
                'avg_inventory': float(row.avg_inventory),
                'turnover_rate': round(turnover_rate, 2)
            })
        
        # Sort by turnover rate
        results.sort(key=lambda x: x['turnover_rate'], reverse=True)
        
        return jsonify({
            'success': True,
            'data': results,
            'period_days': days,
            'count': len(results)
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@reports_bp.route('/stock-levels', methods=['GET'])
def get_stock_levels_report():
    """Get current stock levels across all warehouses"""
    try:
        warehouse_id = request.args.get('warehouse_id', type=int)
        category_id = request.args.get('category_id', type=int)
        
        query = db.session.query(
            Product.id,
            Product.name,
            Product.sku,
            Product.category_id,
            Warehouse.id.label('warehouse_id'),
            Warehouse.name.label('warehouse_name'),
            Inventory.quantity,
            Inventory.reorder_level,
            Inventory.max_stock_level,
            (Inventory.quantity <= Inventory.reorder_level).label('is_low_stock')
        ).join(Inventory, Product.id == Inventory.product_id)\
         .join(Warehouse, Inventory.warehouse_id == Warehouse.id)
        
        if warehouse_id:
            query = query.filter(Warehouse.id == warehouse_id)
        
        if category_id:
            query = query.filter(Product.category_id == category_id)
        
        stock_levels = query.all()
        
        results = []
        for row in stock_levels:
            results.append({
                'product_id': row.id,
                'product_name': row.name,
                'sku': row.sku,
                'category_id': row.category_id,
                'warehouse_id': row.warehouse_id,
                'warehouse_name': row.warehouse_name,
                'quantity': row.quantity,
                'reorder_level': row.reorder_level,
                'max_stock_level': row.max_stock_level,
                'is_low_stock': bool(row.is_low_stock),
                'stock_percentage': round((row.quantity / row.max_stock_level) * 100, 2) if row.max_stock_level > 0 else 0
            })
        
        return jsonify({
            'success': True,
            'data': results,
            'count': len(results)
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@reports_bp.route('/stock-valuation', methods=['GET'])
def get_stock_valuation():
    """Get stock valuation report"""
    try:
        warehouse_id = request.args.get('warehouse_id', type=int)
        
        query = db.session.query(
            Product.id,
            Product.name,
            Product.sku,
            Product.unit_price,
            Warehouse.id.label('warehouse_id'),
            Warehouse.name.label('warehouse_name'),
            Inventory.quantity,
            (Inventory.quantity * Product.unit_price).label('total_value')
        ).join(Inventory, Product.id == Inventory.product_id)\
         .join(Warehouse, Inventory.warehouse_id == Warehouse.id)\
         .filter(Product.unit_price.isnot(None))
        
        if warehouse_id:
            query = query.filter(Warehouse.id == warehouse_id)
        
        valuation_data = query.all()
        
        results = []
        total_valuation = 0
        
        for row in valuation_data:
            value = float(row.total_value) if row.total_value else 0
            total_valuation += value
            
            results.append({
                'product_id': row.id,
                'product_name': row.name,
                'sku': row.sku,
                'unit_price': float(row.unit_price) if row.unit_price else 0,
                'warehouse_id': row.warehouse_id,
                'warehouse_name': row.warehouse_name,
                'quantity': row.quantity,
                'total_value': value
            })
        
        # Group by warehouse
        warehouse_totals = {}
        for item in results:
            wh_id = item['warehouse_id']
            if wh_id not in warehouse_totals:
                warehouse_totals[wh_id] = {
                    'warehouse_name': item['warehouse_name'],
                    'total_value': 0,
                    'item_count': 0
                }
            warehouse_totals[wh_id]['total_value'] += item['total_value']
            warehouse_totals[wh_id]['item_count'] += 1
        
        return jsonify({
            'success': True,
            'data': {
                'items': results,
                'warehouse_totals': warehouse_totals,
                'grand_total': round(total_valuation, 2)
            },
            'count': len(results)
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@reports_bp.route('/movement-history', methods=['GET'])
def get_movement_history():
    """Get stock movement history report"""
    try:
        days = request.args.get('days', 30, type=int)
        product_id = request.args.get('product_id', type=int)
        warehouse_id = request.args.get('warehouse_id', type=int)
        movement_type = request.args.get('movement_type')
        
        start_date = datetime.utcnow() - timedelta(days=days)
        
        query = db.session.query(
            StockMovement.id,
            StockMovement.movement_type,
            StockMovement.quantity,
            StockMovement.reference_type,
            StockMovement.reference_id,
            StockMovement.notes,
            StockMovement.created_at,
            Product.name.label('product_name'),
            Product.sku,
            Warehouse.name.label('warehouse_name')
        ).join(Product, StockMovement.product_id == Product.id)\
         .join(Warehouse, StockMovement.warehouse_id == Warehouse.id)\
         .filter(StockMovement.created_at >= start_date)
        
        if product_id:
            query = query.filter(StockMovement.product_id == product_id)
        
        if warehouse_id:
            query = query.filter(StockMovement.warehouse_id == warehouse_id)
        
        if movement_type:
            query = query.filter(StockMovement.movement_type == movement_type)
        
        movements = query.order_by(desc(StockMovement.created_at)).all()
        
        results = []
        for movement in movements:
            results.append({
                'id': movement.id,
                'movement_type': movement.movement_type,
                'quantity': movement.quantity,
                'reference_type': movement.reference_type,
                'reference_id': movement.reference_id,
                'notes': movement.notes,
                'created_at': movement.created_at.isoformat(),
                'product_name': movement.product_name,
                'sku': movement.sku,
                'warehouse_name': movement.warehouse_name
            })
        
        return jsonify({
            'success': True,
            'data': results,
            'period_days': days,
            'count': len(results)
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@reports_bp.route('/purchase-order-summary', methods=['GET'])
def get_purchase_order_summary():
    """Get purchase order summary report"""
    try:
        days = request.args.get('days', 30, type=int)
        start_date = datetime.utcnow() - timedelta(days=days)
        
        # PO status summary
        status_summary = db.session.query(
            PurchaseOrder.status,
            func.count(PurchaseOrder.id).label('count'),
            func.sum(PurchaseOrder.total_amount).label('total_amount')
        ).filter(PurchaseOrder.created_at >= start_date)\
         .group_by(PurchaseOrder.status).all()
        
        status_data = []
        for row in status_summary:
            status_data.append({
                'status': row.status,
                'count': row.count,
                'total_amount': float(row.total_amount) if row.total_amount else 0
            })
        
        # Supplier performance
        supplier_summary = db.session.query(
            PurchaseOrder.supplier_id,
            func.count(PurchaseOrder.id).label('order_count'),
            func.sum(PurchaseOrder.total_amount).label('total_spent'),
            func.avg(
                func.datediff(PurchaseOrder.actual_delivery, PurchaseOrder.order_date)
            ).label('avg_delivery_days')
        ).filter(PurchaseOrder.created_at >= start_date)\
         .group_by(PurchaseOrder.supplier_id).all()
        
        supplier_data = []
        for row in supplier_summary:
            supplier_data.append({
                'supplier_id': row.supplier_id,
                'order_count': row.order_count,
                'total_spent': float(row.total_spent) if row.total_spent else 0,
                'avg_delivery_days': float(row.avg_delivery_days) if row.avg_delivery_days else None
            })
        
        return jsonify({
            'success': True,
            'data': {
                'status_summary': status_data,
                'supplier_performance': supplier_data
            },
            'period_days': days
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500 