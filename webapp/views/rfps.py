from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from webapp import db
from webapp.models import RFP, Favorite
from datetime import datetime
import csv
import io

# Create blueprint
rfps_bp = Blueprint('rfps', __name__)

@rfps_bp.route('/')
def index():
    """Display RFP listings with filtering"""
    page = request.args.get('page', 1, type=int)
    per_page = 20
    
    # Get filter parameters
    state = request.args.get('state', '')
    industry = request.args.get('industry', '')
    min_score = request.args.get('min_score', 0, type=int)
    sort = request.args.get('sort', 'relevance')
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
    
    # Apply sorting
    if sort == 'relevance':
        query = query.order_by(RFP.scada_relevance_score.desc())
    elif sort == 'due_date':
        query = query.order_by(RFP.due_date.asc())
    elif sort == 'publication_date':
        query = query.order_by(RFP.publication_date.desc())
    elif sort == 'state':
        query = query.order_by(RFP.state.asc())
    
    # Get RFPs with pagination
    rfps = query.paginate(page=page, per_page=per_page, error_out=False)
    
    # Get available states for filter dropdown
    states = db.session.query(RFP.state).distinct().all()
    states = [state[0] for state in states]
    
    # Get user's favorites if logged in
    favorites = set()
    if current_user.is_authenticated:
        favorites = {fav.rfp_id for fav in current_user.favorites.all()}
    
    # Current filters for pagination links
    current_filters = {
        'state': state,
        'industry': industry,
        'min_score': min_score,
        'sort': sort,
        'q': search_query
    }
    
    return render_template(
        'rfps/index.html',
        rfps=rfps,
        states=states,
        favorites=favorites,
        current_filters=current_filters
    )

@rfps_bp.route('/<rfp_id>')
def detail(rfp_id):
    """Display RFP details"""
    rfp = RFP.query.get_or_404(rfp_id)
    
    # Get similar RFPs
    similar_rfps = RFP.query.filter(
        RFP.id != rfp_id,
        RFP.state == rfp.state,
        RFP.scada_relevance_score >= 50
    ).order_by(
        RFP.scada_relevance_score.desc()
    ).limit(5).all()
    
    # Get user's favorites if logged in
    favorites = set()
    if current_user.is_authenticated:
        favorites = {fav.rfp_id for fav in current_user.favorites.all()}
    
    return render_template(
        'rfps/detail.html',
        rfp=rfp,
        similar_rfps=similar_rfps,
        favorites=favorites
    )

@rfps_bp.route('/favorites')
@login_required
def favorites():
    """Display user's favorite RFPs"""
    page = request.args.get('page', 1, type=int)
    per_page = 20
    
    # Get user's favorites with pagination
    favorites = current_user.favorites.order_by(
        Favorite.created_at.desc()
    ).paginate(page=page, per_page=per_page, error_out=False)
    
    # Get RFPs for each favorite
    rfps = []
    for favorite in favorites.items:
        rfp = RFP.query.get(favorite.rfp_id)
        if rfp:
            rfps.append(rfp)
    
    return render_template(
        'rfps/favorites.html',
        favorites=favorites,
        rfps=rfps
    )

@rfps_bp.route('/<rfp_id>/favorite', methods=['POST'])
@login_required
def toggle_favorite(rfp_id):
    """Toggle favorite status for an RFP"""
    rfp = RFP.query.get_or_404(rfp_id)
    
    # Check if already favorited
    favorite = Favorite.query.filter_by(
        user_id=current_user.id,
        rfp_id=rfp_id
    ).first()
    
    if favorite:
        # Remove from favorites
        db.session.delete(favorite)
        db.session.commit()
        return jsonify({'is_favorite': False})
    else:
        # Add to favorites
        favorite = Favorite(
            user_id=current_user.id,
            rfp_id=rfp_id
        )
        db.session.add(favorite)
        db.session.commit()
        return jsonify({'is_favorite': True})

@rfps_bp.route('/export')
@login_required
def export():
    """Export filtered RFPs as CSV"""
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
    
    # Get RFPs
    rfps = query.order_by(RFP.scada_relevance_score.desc()).all()
    
    # Create CSV
    output = io.StringIO()
    writer = csv.writer(output)
    
    # Write header
    writer.writerow([
        'ID', 'Title', 'State', 'Agency', 'Publication Date', 'Due Date',
        'SCADA Relevance', 'Water/Wastewater', 'Mining', 'Oil & Gas',
        'Contact Name', 'Contact Email', 'Contact Phone', 'URL'
    ])
    
    # Write data
    for rfp in rfps:
        writer.writerow([
            rfp.id,
            rfp.title,
            rfp.state,
            rfp.agency,
            rfp.publication_date.strftime('%Y-%m-%d') if rfp.publication_date else '',
            rfp.due_date.strftime('%Y-%m-%d') if rfp.due_date else '',
            f"{rfp.scada_relevance_score}%",
            'Yes' if rfp.is_water_wastewater else 'No',
            'Yes' if rfp.is_mining else 'No',
            'Yes' if rfp.is_oil_gas else 'No',
            rfp.contact_name or '',
            rfp.contact_email or '',
            rfp.contact_phone or '',
            rfp.url or ''
        ])
    
    # Create response
    output.seek(0)
    return jsonify({'csv': output.getvalue()})

@rfps_bp.route('/<rfp_id>/export')
@login_required
def export_single(rfp_id):
    """Export a single RFP as CSV"""
    rfp = RFP.query.get_or_404(rfp_id)
    
    # Create CSV
    output = io.StringIO()
    writer = csv.writer(output)
    
    # Write header
    writer.writerow([
        'ID', 'Title', 'State', 'Agency', 'Publication Date', 'Due Date',
        'SCADA Relevance', 'Water/Wastewater', 'Mining', 'Oil & Gas',
        'Contact Name', 'Contact Email', 'Contact Phone', 'URL', 'Description'
    ])
    
    # Write data
    writer.writerow([
        rfp.id,
        rfp.title,
        rfp.state,
        rfp.agency,
        rfp.publication_date.strftime('%Y-%m-%d') if rfp.publication_date else '',
        rfp.due_date.strftime('%Y-%m-%d') if rfp.due_date else '',
        f"{rfp.scada_relevance_score}%",
        'Yes' if rfp.is_water_wastewater else 'No',
        'Yes' if rfp.is_mining else 'No',
        'Yes' if rfp.is_oil_gas else 'No',
        rfp.contact_name or '',
        rfp.contact_email or '',
        rfp.contact_phone or '',
        rfp.url or '',
        rfp.description or ''
    ])
    
    # Create response
    output.seek(0)
    return jsonify({'csv': output.getvalue()})
