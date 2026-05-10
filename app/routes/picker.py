import os
import random
from flask import Blueprint, render_template, request, flash, current_app
from app.services.discogs_api import DiscogsService

bp = Blueprint('picker', __name__)

@bp.route('/', methods=['GET', 'POST'])
def index():
    default_user = os.environ.get('DEFAULT_DISCOGS_USERNAME')
    username = request.form.get('username') or request.args.get('username') or default_user
    query = request.form.get('query')
    is_random = request.form.get('random') == 'on'
    refresh = request.form.get('refresh') == 'on'
    
    releases = []
    selected = None
    
    if username:
        token = current_app.config.get('DISCOGS_TOKEN') or os.environ.get('DISCOGS_TOKEN')
        service = DiscogsService(username, token)
        try:
            releases = service.fetch_collection(force_refresh=refresh)
            filtered = service.search_library(releases, query=query)
            
            if not filtered:
                flash("Keine Alben gefunden.", "error")
            elif is_random:
                selected = random.choice(filtered)
            else:
                releases = filtered
        except Exception as e:
            flash(f"Fehler: {str(e)}", "error")
            
    return render_template('picker/index.html', 
                           username=username, 
                           releases=releases, 
                           selected=selected,
                           query=query)
