import requests
from flask import current_app, flash, render_template, redirect

from . import image_reference_bp


@image_reference_bp.get('')
def image_reference_page():
    res = requests.get(f'{current_app.config.get("DARC_REVIEW_URL")}/image-reference')
    if res.status_code != 200:
        flash('Error retrieving image reference data', 'error')
        redirect('/')
    return render_template('image_reference/image-reference.html', image_references=res.text)
