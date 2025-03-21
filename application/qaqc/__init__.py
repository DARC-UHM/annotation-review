from flask import Blueprint

qaqc_bp = Blueprint('qaqc', __name__, static_folder='static')

from .tator import tator_qaqc_bp
from .vars import vars_qaqc_bp

qaqc_bp.register_blueprint(tator_qaqc_bp, url_prefix='/tator')
qaqc_bp.register_blueprint(vars_qaqc_bp, url_prefix='/vars')
