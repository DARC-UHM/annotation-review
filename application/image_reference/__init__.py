from flask import Blueprint

image_reference_bp = Blueprint(
    'image_reference', __name__,
    template_folder='templates',
    static_folder='static',
)

from . import routes
