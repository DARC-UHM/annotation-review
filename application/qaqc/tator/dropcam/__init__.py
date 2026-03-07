from flask import Blueprint

dropcam_qaqc_bp = Blueprint(
    'dropcam_qaqc', __name__,
    static_folder='static',
    template_folder='templates',
)

from . import routes
