from flask import Blueprint, request, session, render_template, flash
import requests
from application.server.vars_annotation_processor import VarsAnnotationProcessor

vars_image_review_bp = Blueprint('vars_image_review', __name__)

@vars_image_review_bp.route('/vars/image-review', methods=['GET'])
def view_images():
    # Your existing vars image review route code
    pass

# Add other VARS image review routes here
