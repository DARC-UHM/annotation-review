from flask import Blueprint, request, session, render_template, flash
import requests
from application.server.vars_qaqc_processor import VarsQaqcProcessor

vars_qaqc_bp = Blueprint('vars_qaqc', __name__)

@vars_qaqc_bp.route('/vars/qaqc-checklist', methods=['GET'])
def vars_qaqc_checklist():
    # Your existing vars qaqc checklist route code
    pass

# Add other VARS QAQC routes here
