from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import current_user, login_required
from webapp import db
from webapp.models import RFP, State

# Create blueprint
main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def index():
    """Home page"""
    # Get statistics for the dashboard
    stats = {
        'total_rfps': RFP.query.count(),
        'states_count': db.session.query(RFP.state).distinct().count(),
        'water_count': RFP.query.filter_by(is_water_wastewater=True).count(),
        'mining_count': RFP.query.filter_by(is_mining=True).count(),
        'oil_gas_count': RFP.query.filter_by(is_oil_gas=True).count()
    }
    
    # Get recent high-relevance RFPs
    recent_rfps = RFP.query.filter(
        RFP.scada_relevance_score >= 70
    ).order_by(
        RFP.created_at.desc()
    ).limit(6).all()
    
    # Get user's favorites if logged in
    favorites = set()
    if current_user.is_authenticated:
        favorites = {fav.rfp_id for fav in current_user.favorites.all()}
    
    return render_template(
        'main/index.html',
        stats=stats,
        recent_rfps=recent_rfps,
        favorites=favorites
    )

@main_bp.route('/about')
def about():
    """About page"""
    return render_template('main/about.html')

@main_bp.route('/contact')
def contact():
    """Contact page"""
    return render_template('main/contact.html')

@main_bp.route('/dashboard')
@login_required
def dashboard():
    """User dashboard"""
    # Get user's favorites
    favorites = current_user.favorites.all()
    favorite_rfps = []
    for fav in favorites:
        rfp = RFP.query.get(fav.rfp_id)
        if rfp:
            favorite_rfps.append(rfp)
    
    # Get recent notifications
    recent_notifications = current_user.notifications.order_by(
        db.desc('sent_at')
    ).limit(5).all()
    
    # Get RFPs matching user's preferences
    matching_rfps = RFP.query
    
    if current_user.min_relevance_score > 0:
        matching_rfps = matching_rfps.filter(
            RFP.scada_relevance_score >= current_user.min_relevance_score
        )
    
    industry_filters = []
    if current_user.water_wastewater_enabled:
        industry_filters.append(RFP.is_water_wastewater == True)
    if current_user.mining_enabled:
        industry_filters.append(RFP.is_mining == True)
    if current_user.oil_gas_enabled:
        industry_filters.append(RFP.is_oil_gas == True)
    
    if industry_filters:
        matching_rfps = matching_rfps.filter(db.or_(*industry_filters))
    
    matching_rfps = matching_rfps.order_by(
        db.desc(RFP.scada_relevance_score)
    ).limit(10).all()
    
    return render_template(
        'main/dashboard.html',
        favorite_rfps=favorite_rfps,
        recent_notifications=recent_notifications,
        matching_rfps=matching_rfps
    )

@main_bp.route('/search')
def search():
    """Global search"""
    query = request.args.get('q', '')
    if not query:
        return redirect(url_for('main.index'))
    
    # Search RFPs
    search_terms = f"%{query}%"
    rfps = RFP.query.filter(
        (RFP.title.ilike(search_terms)) | 
        (RFP.description.ilike(search_terms)) |
        (RFP.agency.ilike(search_terms))
    ).order_by(
        db.desc(RFP.scada_relevance_score)
    ).limit(20).all()
    
    return render_template(
        'main/search.html',
        query=query,
        rfps=rfps
    )
