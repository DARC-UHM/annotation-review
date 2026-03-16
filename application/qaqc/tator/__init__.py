from flask import Blueprint

tator_qaqc_bp = Blueprint(
    'tator_qaqc', __name__,
    template_folder='templates',
)

from .dropcam import dropcam_qaqc_bp
from .sub import sub_qaqc_bp

tator_qaqc_bp.register_blueprint(dropcam_qaqc_bp, url_prefix='/dropcam')
tator_qaqc_bp.register_blueprint(sub_qaqc_bp, url_prefix='/sub')
