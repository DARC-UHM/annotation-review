from flask import Blueprint

sub_qaqc_bp = Blueprint(
    'sub_qaqc', __name__,
    static_folder='static',
    template_folder='templates',
)

from . import routes
