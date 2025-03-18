from flask import Blueprint

image_review_bp = Blueprint('image_review', __name__, template_folder='templates')

from .external_review import external_review_bp
from .tator import tator_image_review_bp
from .vars import vars_image_review_bp

image_review_bp.register_blueprint(external_review_bp, url_prefix='/external-review')
image_review_bp.register_blueprint(tator_image_review_bp, url_prefix='/tator')
image_review_bp.register_blueprint(vars_image_review_bp, url_prefix='/vars')
