from flask import Blueprint

tator_qaqc_bp = Blueprint('tator_qaqc', __name__)

from .dropcam import dropcam_qaqc_bp

tator_qaqc_bp.register_blueprint(dropcam_qaqc_bp, url_prefix='/dropcam')
