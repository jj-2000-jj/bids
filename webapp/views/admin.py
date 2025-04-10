from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from webapp import db
from webapp.models import RFP, User, ScraperLog, SystemConfig, State
import json
from datetime import datetime, timedelta

# Create blueprint
admin_bp = Blueprint('admin', __name__)

@admin_bp.route('/')
@login_required
def index():
    """Admin dashboard"""
    if not current_user.is_admin:
        flash('You do not have permission to access the admin area.', 'danger')
        return redirect(url_for('main.index'))
    
    # Get statistics
    stats = {
        'total_rfps': RFP.query.count(),
        'total_users': User.query.count(),
        'states_covered': db.session.query(RFP.state).distinct().count(),
        'high_relevance_rfps': RFP.query.filter(RFP.scada_relevance_score >= 80).count(),
        'water_rfps': RFP.query.filter_by(is_water_wastewater=True).count(),
        'mining_rfps': RFP.query.filter_by(is_mining=True).count(),
        'oil_gas_rfps': RFP.query.filter_by(is_oil_gas=True).count()
    }
    
    # Get RFPs by state for chart
    state_counts = db.session.query(
        RFP.state, db.func.count(RFP.id)
    ).group_by(RFP.state).all()
    
    state_data = {}
    for state, count in state_counts:
        state_data[state] = count
    
    # Get RFPs by relevance for chart
    relevance_counts = [
        {'label': 'Very Low (0-20%)', 'count': RFP.query.filter(RFP.scada_relevance_score < 20).count()},
        {'label': 'Low (20-40%)', 'count': RFP.query.filter(RFP.scada_relevance_score.between(20, 39)).count()},
        {'label': 'Medium (40-60%)', 'count': RFP.query.filter(RFP.scada_relevance_score.between(40, 59)).count()},
        {'label': 'High (60-80%)', 'count': RFP.query.filter(RFP.scada_relevance_score.between(60, 79)).count()},
        {'label': 'Very High (80-100%)', 'count': RFP.query.filter(RFP.scada_relevance_score >= 80).count()}
    ]
    
    # Get recent scraper logs
    recent_logs = ScraperLog.query.order_by(
        ScraperLog.start_time.desc()
    ).limit(10).all()
    
    return render_template(
        'admin/index.html',
        stats=stats,
        state_data=json.dumps(state_data),
        relevance_counts=json.dumps(relevance_counts),
        recent_logs=recent_logs
    )

@admin_bp.route('/users')
@login_required
def users():
    """Manage users"""
    if not current_user.is_admin:
        flash('You do not have permission to access the admin area.', 'danger')
        return redirect(url_for('main.index'))
    
    page = request.args.get('page', 1, type=int)
    per_page = 20
    
    # Get users with pagination
    users = User.query.order_by(
        User.created_at.desc()
    ).paginate(page=page, per_page=per_page, error_out=False)
    
    return render_template('admin/users.html', users=users)

@admin_bp.route('/users/<int:user_id>', methods=['GET', 'POST'])
@login_required
def edit_user(user_id):
    """Edit user"""
    if not current_user.is_admin:
        flash('You do not have permission to access the admin area.', 'danger')
        return redirect(url_for('main.index'))
    
    user = User.query.get_or_404(user_id)
    
    if request.method == 'POST':
        # Update user
        user.username = request.form.get('username')
        user.email = request.form.get('email')
        user.is_admin = 'is_admin' in request.form
        
        # Update password if provided
        new_password = request.form.get('new_password')
        if new_password:
            user.password = new_password
        
        db.session.commit()
        flash('User updated.', 'success')
        return redirect(url_for('admin.users'))
    
    return render_template('admin/edit_user.html', user=user)

@admin_bp.route('/users/<int:user_id>/delete', methods=['POST'])
@login_required
def delete_user(user_id):
    """Delete user"""
    if not current_user.is_admin:
        flash('You do not have permission to access the admin area.', 'danger')
        return redirect(url_for('main.index'))
    
    user = User.query.get_or_404(user_id)
    
    # Prevent deleting self
    if user.id == current_user.id:
        flash('You cannot delete your own account.', 'danger')
        return redirect(url_for('admin.users'))
    
    db.session.delete(user)
    db.session.commit()
    
    flash('User deleted.', 'success')
    return redirect(url_for('admin.users'))

@admin_bp.route('/rfps')
@login_required
def rfps():
    """Manage RFPs"""
    if not current_user.is_admin:
        flash('You do not have permission to access the admin area.', 'danger')
        return redirect(url_for('main.index'))
    
    page = request.args.get('page', 1, type=int)
    per_page = 20
    
    # Get filter parameters
    state = request.args.get('state', '')
    industry = request.args.get('industry', '')
    min_score = request.args.get('min_score', 0, type=int)
    search_query = request.args.get('q', '')
    
    # Start with base query
    query = RFP.query
    
    # Apply filters
    if state:
        query = query.filter(RFP.state == state)
    
    if industry:
        if industry == 'water':
            query = query.filter(RFP.is_water_wastewater == True)
        elif industry == 'mining':
            query = query.filter(RFP.is_mining == True)
        elif industry == 'oil_gas':
            query = query.filter(RFP.is_oil_gas == True)
    
    if min_score > 0:
        query = query.filter(RFP.scada_relevance_score >= min_score)
    
    if search_query:
        search_terms = f"%{search_query}%"
        query = query.filter(
            (RFP.title.ilike(search_terms)) | 
            (RFP.description.ilike(search_terms)) |
            (RFP.agency.ilike(search_terms))
        )
    
    # Get RFPs with pagination
    rfps = query.order_by(
        RFP.created_at.desc()
    ).paginate(page=page, per_page=per_page, error_out=False)
    
    # Get available states for filter dropdown
    states = db.session.query(RFP.state).distinct().all()
    states = [state[0] for state in states]
    
    # Current filters for pagination links
    current_filters = {
        'state': state,
        'industry': industry,
        'min_score': min_score,
        'q': search_query
    }
    
    return render_template(
        'admin/rfps.html',
        rfps=rfps,
        states=states,
        current_filters=current_filters
    )

@admin_bp.route('/rfps/<rfp_id>', methods=['GET', 'POST'])
@login_required
def edit_rfp(rfp_id):
    """Edit RFP"""
    if not current_user.is_admin:
        flash('You do not have permission to access the admin area.', 'danger')
        return redirect(url_for('main.index'))
    
    rfp = RFP.query.get_or_404(rfp_id)
    
    if request.method == 'POST':
        # Update RFP
        rfp.title = request.form.get('title')
        rfp.description = request.form.get('description')
        rfp.state = request.form.get('state')
        rfp.agency = request.form.get('agency')
        
        # Parse dates
        pub_date = request.form.get('publication_date')
        if pub_date:
            rfp.publication_date = datetime.strptime(pub_date, '%Y-%m-%d').date()
        else:
            rfp.publication_date = None
        
        due_date = request.form.get('due_date')
        if due_date:
            rfp.due_date = datetime.strptime(due_date, '%Y-%m-%d').date()
        else:
            rfp.due_date = None
        
        rfp.url = request.form.get('url')
        rfp.requirements = request.form.get('requirements')
        rfp.contact_name = request.form.get('contact_name')
        rfp.contact_email = request.form.get('contact_email')
        rfp.contact_phone = request.form.get('contact_phone')
        
        # SCADA relevance fields
        rfp.scada_relevance_score = int(request.form.get('scada_relevance_score', 0))
        rfp.is_water_wastewater = 'is_water_wastewater' in request.form
        rfp.is_mining = 'is_mining' in request.form
        rfp.is_oil_gas = 'is_oil_gas' in request.form
        
        rfp.updated_at = datetime.utcnow()
        
        db.session.commit()
        flash('RFP updated.', 'success')
        return redirect(url_for('admin.rfps'))
    
    # Get available states for dropdown
    states = db.session.query(State.code).all()
    states = [state[0] for state in states]
    
    return render_template('admin/edit_rfp.html', rfp=rfp, states=states)

@admin_bp.route('/rfps/<rfp_id>/delete', methods=['POST'])
@login_required
def delete_rfp(rfp_id):
    """Delete RFP"""
    if not current_user.is_admin:
        flash('You do not have permission to access the admin area.', 'danger')
        return redirect(url_for('main.index'))
    
    rfp = RFP.query.get_or_404(rfp_id)
    
    db.session.delete(rfp)
    db.session.commit()
    
    flash('RFP deleted.', 'success')
    return redirect(url_for('admin.rfps'))

@admin_bp.route('/scrapers')
@login_required
def scrapers():
    """Manage scrapers"""
    if not current_user.is_admin:
        flash('You do not have permission to access the admin area.', 'danger')
        return redirect(url_for('main.index'))
    
    # Get states
    states = State.query.all()
    
    # Get recent logs for each state
    logs = {}
    for state in states:
        logs[state.code] = ScraperLog.query.filter_by(
            state=state.code
        ).order_by(
            ScraperLog.start_time.desc()
        ).first()
    
    return render_template('admin/scrapers.html', states=states, logs=logs)

@admin_bp.route('/scrapers/<state_code>/toggle', methods=['POST'])
@login_required
def toggle_scraper(state_code):
    """Toggle scraper enabled state"""
    if not current_user.is_admin:
        flash('You do not have permission to access the admin area.', 'danger')
        return redirect(url_for('main.index'))
    
    state = State.query.get_or_404(state_code)
    
    state.enabled = not state.enabled
    db.session.commit()
    
    return jsonify({'enabled': state.enabled})

@admin_bp.route('/scrapers/<state_code>/run', methods=['POST'])
@login_required
def run_scraper(state_code):
    """Run scraper manually"""
    if not current_user.is_admin:
        flash('You do not have permission to access the admin area.', 'danger')
        return redirect(url_for('main.index'))
    
    state = State.query.get_or_404(state_code)
    
    # Create log entry
    log = ScraperLog(
        state=state.code,
        start_time=datetime.utcnow()
    )
    db.session.add(log)
    db.session.commit()
    
    # In a real implementation, this would trigger the scraper
    # For now, we'll just simulate a successful run
    log.end_time = datetime.utcnow() + timedelta(seconds=5)
    log.success = True
    log.rfps_found = 3
    db.session.commit()
    
    flash(f'Scraper for {state.name} ran successfully.', 'success')
    return redirect(url_for('admin.scrapers'))

@admin_bp.route('/logs')
@login_required
def logs():
    """View scraper logs"""
    if not current_user.is_admin:
        flash('You do not have permission to access the admin area.', 'danger')
        return redirect(url_for('main.index'))
    
    page = request.args.get('page', 1, type=int)
    per_page = 50
    
    # Get filter parameters
    state = request.args.get('state', '')
    status = request.args.get('status', '')
    
    # Start with base query
    query = ScraperLog.query
    
    # Apply filters
    if state:
        query = query.filter(ScraperLog.state == state)
    
    if status:
        if status == 'success':
            query = query.filter(ScraperLog.success == True)
        elif status == 'failed':
            query = query.filter(ScraperLog.success == False)
    
    # Get logs with pagination
    logs = query.order_by(
        ScraperLog.start_time.desc()
    ).paginate(page=page, per_page=per_page, error_out=False)
    
    # Get available states for filter dropdown
    states = db.session.query(ScraperLog.state).distinct().all()
    states = [state[0] for state in states]
    
    # Current filters for pagination links
    current_filters = {
        'state': state,
        'status': status
    }
    
    return render_template(
        'admin/logs.html',
        logs=logs,
        states=states,
        current_filters=current_filters
    )

@admin_bp.route('/config', methods=['GET', 'POST'])
@login_required
def config():
    """System configuration"""
    if not current_user.is_admin:
        flash('You do not have permission to access the admin area.', 'danger')
        return redirect(url_for('main.index'))
    
    if request.method == 'POST':
        # Update configuration
        for key in request.form:
            if key.startswith('config_'):
                config_key = key[7:]  # Remove 'config_' prefix
                config = SystemConfig.query.get(config_key)
                if config:
                    config.value = request.form[key]
        
        db.session.commit()
        flash('Configuration updated.', 'success')
        return redirect(url_for('admin.config'))
    
    # Get all configuration settings
    configs = SystemConfig.query.all()
    
    return render_template('admin/config.html', configs=configs)
