from flask import Blueprint, render_template, request, jsonify, flash, redirect, url_for
from flask_login import login_required, current_user
from webapp import db
from webapp.models import RFP, ScraperLog, State
from webapp.scrapers import run_all_scrapers, run_state_scraper
from datetime import datetime

# Create blueprint
scraper_bp = Blueprint('scraper', __name__)

@scraper_bp.route('/run', methods=['POST'])
@login_required
def run_scraper():
    """Run scrapers for all enabled states"""
    # Allow all authenticated users to run scrapers, not just admins
    try:
        # Run all scrapers
        results = run_all_scrapers()
        
        return jsonify({'success': True, 'results': results})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@scraper_bp.route('/state/<state_code>', methods=['POST'])
@login_required
def run_state_scraper_route(state_code):
    """Run scraper for a specific state"""
    # Allow all authenticated users to run scrapers, not just admins
    
    # Check if state exists
    state = State.query.get(state_code)
    if not state:
        return jsonify({'success': False, 'message': 'State not found'}), 404
    
    try:
        # Run scraper for the state
        rfps_found = run_state_scraper(state_code)
        
        return jsonify({'success': True, 'rfps_found': rfps_found})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@scraper_bp.route('/status')
@login_required
def scraper_status():
    """Get status of scrapers"""
    # Allow all authenticated users to check status, not just admins
    
    # Check if any scrapers are currently running
    running_scrapers = ScraperLog.query.filter_by(
        end_time=None
    ).count()
    
    # Get the total number of RFPs found in the most recent scraper run
    latest_log = ScraperLog.query.filter(
        ScraperLog.end_time.isnot(None)
    ).order_by(
        ScraperLog.start_time.desc()
    ).first()
    
    rfps_found = latest_log.rfps_found if latest_log else 0
    
    # Get states with their latest log
    states = State.query.all()
    
    status = {}
    for state in states:
        latest_state_log = ScraperLog.query.filter_by(
            state=state.code
        ).order_by(
            ScraperLog.start_time.desc()
        ).first()
        
        status[state.code] = {
            'name': state.name,
            'enabled': state.enabled,
            'last_run': latest_state_log.start_time.isoformat() if latest_state_log else None,
            'success': latest_state_log.success if latest_state_log else None,
            'rfps_found': latest_state_log.rfps_found if latest_state_log else 0
        }
    
    return jsonify({
        'is_running': running_scrapers > 0,
        'rfps_found': rfps_found,
        'status': status
    })

@scraper_bp.route('/logs')
@login_required
def scraper_logs():
    """Get scraper logs"""
    if not current_user.is_admin:
        return jsonify({'error': 'Unauthorized'}), 403
    
    # Get filter parameters
    state = request.args.get('state', '')
    limit = request.args.get('limit', 50, type=int)
    
    # Start with base query
    query = ScraperLog.query
    
    # Apply filters
    if state:
        query = query.filter(ScraperLog.state == state)
    
    # Get logs
    logs = query.order_by(
        ScraperLog.start_time.desc()
    ).limit(limit).all()
    
    # Format logs
    formatted_logs = []
    for log in logs:
        formatted_logs.append({
            'id': log.id,
            'state': log.state,
            'start_time': log.start_time.isoformat(),
            'end_time': log.end_time.isoformat() if log.end_time else None,
            'duration': log.duration,
            'success': log.success,
            'rfps_found': log.rfps_found,
            'error_message': log.error_message
        })
    
    return jsonify({'logs': formatted_logs})

@scraper_bp.route('/admin/run', methods=['GET', 'POST'])
@login_required
def admin_run_scrapers():
    """Admin interface for running scrapers"""
    if not current_user.is_admin:
        flash('You do not have permission to access the admin area.', 'danger')
        return redirect(url_for('main.index'))
    
    if request.method == 'POST':
        state_code = request.form.get('state_code')
        
        if state_code == 'all':
            # Run all scrapers
            try:
                results = run_all_scrapers()
                flash('All scrapers completed. Check logs for details.', 'success')
            except Exception as e:
                flash(f'Error running scrapers: {str(e)}', 'danger')
        else:
            # Run specific state scraper
            try:
                rfps_found = run_state_scraper(state_code)
                flash(f'Scraper for {state_code} completed. Found {rfps_found} SCADA-related RFPs.', 'success')
            except Exception as e:
                flash(f'Error running scraper for {state_code}: {str(e)}', 'danger')
        
        return redirect(url_for('scraper.admin_run_scrapers'))
    
    # Get states
    states = State.query.all()
    
    # Get recent logs
    logs = ScraperLog.query.order_by(
        ScraperLog.start_time.desc()
    ).limit(10).all()
    
    return render_template('admin/run_scrapers.html', states=states, logs=logs)
