from flask import Blueprint, render_template, request, flash, current_app
from app.services.discogs_api import DiscogsService

bp = Blueprint('marketplace', __name__, url_prefix='/marketplace')

@bp.route('/sold', methods=['GET', 'POST'])
def sold():
    username = request.form.get('username') or request.args.get('username')
    refresh = request.form.get('refresh') == 'on'
    
    overlaps = []
    
    if username:
        token = current_app.config.get('DISCOGS_TOKEN')
        if not token:
            flash("Ein Discogs API Token wird für diese Funktion benötigt (bitte in .env setzen).", "error")
        else:
            service = DiscogsService(username, token)
            try:
                releases = service.fetch_collection(force_refresh=refresh)
                sold_items = service.fetch_sold_items()
                overlaps = service.get_sold_comparison(releases, sold_items)
                
                if not overlaps:
                    flash("Keine Übereinstimmungen gefunden. Deine Collection scheint aktuell zu sein!", "success")
            except Exception as e:
                flash(f"Fehler: {str(e)}", "error")
            
    return render_template('marketplace/sold.html', 
                           username=username, 
                           overlaps=overlaps)
