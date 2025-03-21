from flask import Blueprint

tator_qaqc_bp = Blueprint(
    'tator_qaqc', __name__,
    static_folder='static',
    template_folder='templates',
)

from . import routes
