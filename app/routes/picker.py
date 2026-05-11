import os
import random
from flask import Blueprint, render_template, request, flash, current_app
from app.services.discogs_api import DiscogsService

bp = Blueprint('picker', __name__)

@bp.route('/', methods=['GET', 'POST'])
def index():
    default_user = os.environ.get('DEFAULT_DISCOGS_USERNAME')
    username = request.form.get('username') or request.args.get('username') or default_user
    query = request.form.get('query') or request.args.get('query')
    
    # Action can be from form or args (for pagination)
    action = request.form.get('action') or request.args.get('action', 'search')
    is_random = action == 'random'
    
    refresh = request.form.get('refresh') == 'on'
    page = int(request.args.get('page', 1))
    per_page = 50
    
    releases = []
    selected = None
    total_count = 0
    total_pages = 0
    
    if username:
        token = current_app.config.get('DISCOGS_TOKEN') or os.environ.get('DISCOGS_TOKEN')
        service = DiscogsService(username, token)
        try:
            all_releases = service.fetch_collection(force_refresh=refresh)
            filtered = service.search_library(all_releases, query=query)
            total_count = len(filtered)
            
            if not filtered:
                flash("Keine Alben gefunden.", "error")
            elif is_random:
                selected = random.choice(filtered)
            else:
                total_pages = (total_count + per_page - 1) // per_page
                # Pagination logic
                start = (page - 1) * per_page
                end = start + per_page
                releases = filtered[start:end]
                
        except Exception as e:
            flash(f"Fehler: {str(e)}", "error")
            
    return render_template('picker/index.html', 
                           username=username, 
                           releases=releases, 
                           selected=selected,
                           query=query,
                           page=page,
                           total_count=total_count,
                           total_pages=total_pages,
                           action=action)
