from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from webapp import db
from webapp.models import User, Notification, RFP
from datetime import datetime

# Create blueprint
notifications_bp = Blueprint('notifications', __name__)

@notifications_bp.route('/')
@login_required
def index():
    """Display user notifications"""
    page = request.args.get('page', 1, type=int)
    per_page = 20
    
    # Get user's notifications with pagination
    notifications = Notification.query.filter_by(
        user_id=current_user.id
    ).order_by(
        Notification.sent_at.desc()
    ).paginate(page=page, per_page=per_page, error_out=False)
    
    # Mark all displayed notifications as read
    for notification in notifications.items:
        if not notification.read:
            notification.read = True
    
    db.session.commit()
    
    return render_template(
        'notifications/index.html',
        notifications=notifications
    )

@notifications_bp.route('/count')
@login_required
def count():
    """Get count of unread notifications for the current user"""
    count = Notification.query.filter_by(
        user_id=current_user.id,
        read=False
    ).count()
    
    return jsonify({'count': count})

@notifications_bp.route('/mark-all-read', methods=['POST'])
@login_required
def mark_all_read():
    """Mark all notifications as read for the current user"""
    Notification.query.filter_by(
        user_id=current_user.id,
        read=False
    ).update({'read': True})
    
    db.session.commit()
    
    return jsonify({'status': 'success'})

@notifications_bp.route('/preferences', methods=['GET', 'POST'])
@login_required
def preferences():
    """Manage notification preferences"""
    if request.method == 'POST':
        # Update notification preferences
        current_user.notification_enabled = 'notification_enabled' in request.form
        current_user.notification_frequency = request.form.get('notification_frequency', 'daily')
        current_user.min_relevance_score = int(request.form.get('min_relevance_score', 50))
        current_user.water_wastewater_enabled = 'water_wastewater_enabled' in request.form
        current_user.mining_enabled = 'mining_enabled' in request.form
        current_user.oil_gas_enabled = 'oil_gas_enabled' in request.form
        
        db.session.commit()
        flash('Notification preferences updated.', 'success')
        return redirect(url_for('notifications.preferences'))
    
    return render_template('notifications/preferences.html')

@notifications_bp.route('/test', methods=['POST'])
@login_required
def send_test():
    """Send a test notification to the current user"""
    # Find a high-relevance RFP to use for the test
    test_rfp = RFP.query.filter(
        RFP.scada_relevance_score >= 80
    ).order_by(
        RFP.scada_relevance_score.desc()
    ).first()
    
    if not test_rfp:
        # If no high-relevance RFP exists, use any RFP
        test_rfp = RFP.query.first()
    
    if not test_rfp:
        flash('No RFPs available for test notification.', 'danger')
        return redirect(url_for('notifications.preferences'))
    
    # Create test notification
    notification = Notification(
        user_id=current_user.id,
        rfp_id=test_rfp.id,
        sent_at=datetime.utcnow()
    )
    
    db.session.add(notification)
    db.session.commit()
    
    flash('Test notification sent.', 'success')
    return redirect(url_for('notifications.index'))
