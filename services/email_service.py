from flask import current_app
from flask_mail import Message, Mail
from models import db, NotificationLog, User, Inventory, PurchaseOrder
from datetime import datetime
import threading

def send_async_email(app, msg, mail):
    """Send email asynchronously"""
    with app.app_context():
        try:
            mail.send(msg)
            return True
        except Exception as e:
            current_app.logger.error(f"Email sending failed: {str(e)}")
            return False

def send_email(subject, recipient, html_body, text_body=None):
    """Send email and log the attempt"""
    try:
        # Create notification log entry
        notification = NotificationLog(
            type='email',
            title=subject,
            message=text_body or html_body,
            recipient_email=recipient,
            status='pending'
        )
        db.session.add(notification)
        db.session.commit()
        
        # Create email message
        msg = Message(
            subject=subject,
            recipients=[recipient],
            html=html_body,
            body=text_body
        )
        
        # Send email asynchronously
        mail = current_app.extensions['mail']
        app = current_app._get_current_object()
        
        def send_async():
            success = send_async_email(app, msg, mail)
            with app.app_context():
                notification = NotificationLog.query.get(notification.id)
                if notification:
                    if success:
                        notification.status = 'sent'
                        notification.sent_at = datetime.utcnow()
                    else:
                        notification.status = 'failed'
                        notification.error_message = 'Failed to send email'
                    db.session.commit()
        
        thread = threading.Thread(target=send_async)
        thread.start()
        
        return True
        
    except Exception as e:
        current_app.logger.error(f"Email service error: {str(e)}")
        # Update notification log
        try:
            notification.status = 'failed'
            notification.error_message = str(e)
            db.session.commit()
        except:
            pass
        return False

def send_low_stock_alert(inventory_item):
    """Send low stock alert email"""
    try:
        # Get admin users
        admin_users = User.query.join(User.role).filter(
            User.role.has(name='Admin'),
            User.is_active == True,
            User.email.isnot(None)
        ).all()
        
        if not admin_users:
            current_app.logger.warning("No admin users found for low stock alert")
            return False
        
        subject = f"Low Stock Alert - {inventory_item.product.name}"
        
        html_body = f"""
        <html>
        <body>
            <h2>Low Stock Alert</h2>
            <p>The following item is running low on stock:</p>
            
            <table border="1" cellpadding="10" cellspacing="0">
                <tr>
                    <td><strong>Product:</strong></td>
                    <td>{inventory_item.product.name}</td>
                </tr>
                <tr>
                    <td><strong>SKU:</strong></td>
                    <td>{inventory_item.product.sku}</td>
                </tr>
                <tr>
                    <td><strong>Warehouse:</strong></td>
                    <td>{inventory_item.warehouse.name}</td>
                </tr>
                <tr>
                    <td><strong>Current Stock:</strong></td>
                    <td>{inventory_item.quantity}</td>
                </tr>
                <tr>
                    <td><strong>Reorder Level:</strong></td>
                    <td>{inventory_item.reorder_level}</td>
                </tr>
            </table>
            
            <p>Please consider reordering this item to maintain adequate stock levels.</p>
            
            <p>Best regards,<br>Inventory Management System</p>
        </body>
        </html>
        """
        
        text_body = f"""
        Low Stock Alert
        
        The following item is running low on stock:
        
        Product: {inventory_item.product.name}
        SKU: {inventory_item.product.sku}
        Warehouse: {inventory_item.warehouse.name}
        Current Stock: {inventory_item.quantity}
        Reorder Level: {inventory_item.reorder_level}
        
        Please consider reordering this item to maintain adequate stock levels.
        
        Best regards,
        Inventory Management System
        """
        
        # Send to all admin users
        for admin in admin_users:
            send_email(subject, admin.email, html_body, text_body)
        
        return True
        
    except Exception as e:
        current_app.logger.error(f"Low stock alert error: {str(e)}")
        return False

def send_purchase_order_notification(purchase_order, notification_type):
    """Send purchase order status notification"""
    try:
        # Get admin users and the user who created the order (if applicable)
        admin_users = User.query.join(User.role).filter(
            User.role.has(name='Admin'),
            User.is_active == True,
            User.email.isnot(None)
        ).all()
        
        if not admin_users:
            return False
        
        # Determine subject and content based on notification type
        if notification_type == 'created':
            subject = f"New Purchase Order Created - {purchase_order.order_number}"
            action = "has been created"
        elif notification_type == 'approved':
            subject = f"Purchase Order Approved - {purchase_order.order_number}"
            action = "has been approved"
        elif notification_type == 'received':
            subject = f"Purchase Order Received - {purchase_order.order_number}"
            action = "has been received"
        elif notification_type == 'cancelled':
            subject = f"Purchase Order Cancelled - {purchase_order.order_number}"
            action = "has been cancelled"
        else:
            return False
        
        html_body = f"""
        <html>
        <body>
            <h2>Purchase Order Update</h2>
            <p>Purchase Order {purchase_order.order_number} {action}.</p>
            
            <table border="1" cellpadding="10" cellspacing="0">
                <tr>
                    <td><strong>Order Number:</strong></td>
                    <td>{purchase_order.order_number}</td>
                </tr>
                <tr>
                    <td><strong>Supplier:</strong></td>
                    <td>{purchase_order.supplier.name}</td>
                </tr>
                <tr>
                    <td><strong>Status:</strong></td>
                    <td>{purchase_order.status.title()}</td>
                </tr>
                <tr>
                    <td><strong>Total Amount:</strong></td>
                    <td>${purchase_order.total_amount:.2f}</td>
                </tr>
                <tr>
                    <td><strong>Order Date:</strong></td>
                    <td>{purchase_order.order_date.strftime('%Y-%m-%d')}</td>
                </tr>
            </table>
            
            <p>Please check the system for more details.</p>
            
            <p>Best regards,<br>Inventory Management System</p>
        </body>
        </html>
        """
        
        text_body = f"""
        Purchase Order Update
        
        Purchase Order {purchase_order.order_number} {action}.
        
        Order Number: {purchase_order.order_number}
        Supplier: {purchase_order.supplier.name}
        Status: {purchase_order.status.title()}
        Total Amount: ${purchase_order.total_amount:.2f}
        Order Date: {purchase_order.order_date.strftime('%Y-%m-%d')}
        
        Please check the system for more details.
        
        Best regards,
        Inventory Management System
        """
        
        # Send to admin users
        for admin in admin_users:
            send_email(subject, admin.email, html_body, text_body)
        
        return True
        
    except Exception as e:
        current_app.logger.error(f"Purchase order notification error: {str(e)}")
        return False

def check_and_send_low_stock_alerts():
    """Check for low stock items and send alerts"""
    try:
        # Get all low stock items
        low_stock_items = Inventory.query.filter(
            Inventory.quantity <= Inventory.reorder_level
        ).all()
        
        # Send alerts for each low stock item
        for item in low_stock_items:
            send_low_stock_alert(item)
        
        current_app.logger.info(f"Processed {len(low_stock_items)} low stock alerts")
        return len(low_stock_items)
        
    except Exception as e:
        current_app.logger.error(f"Low stock alert check error: {str(e)}")
        return 0

def send_test_email(recipient):
    """Send test email to verify email configuration"""
    try:
        subject = "Test Email - Inventory Management System"
        
        html_body = """
        <html>
        <body>
            <h2>Test Email</h2>
            <p>This is a test email to verify that the email configuration is working correctly.</p>
            <p>If you receive this email, the email system is functioning properly.</p>
            <p>Best regards,<br>Inventory Management System</p>
        </body>
        </html>
        """
        
        text_body = """
        Test Email
        
        This is a test email to verify that the email configuration is working correctly.
        If you receive this email, the email system is functioning properly.
        
        Best regards,
        Inventory Management System
        """
        
        return send_email(subject, recipient, html_body, text_body)
        
    except Exception as e:
        current_app.logger.error(f"Test email error: {str(e)}")
        return False 