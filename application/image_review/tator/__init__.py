from flask import Blueprint

tator_image_review_bp = Blueprint('tator_image_review', __name__)

from . import routes
