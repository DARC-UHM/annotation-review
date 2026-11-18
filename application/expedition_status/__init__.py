from flask import Blueprint

expedition_status_bp = Blueprint(
    'expedition_status', __name__,
    template_folder='templates',
    static_folder='static',
)

from . import routes
