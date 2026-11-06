from flask import Blueprint

expedition_status_bp = Blueprint('expedition_status', __name__)

from . import routes
