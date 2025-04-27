import requests
from flask import current_app, flash, render_template, redirect, request

from . import image_reference_bp


@image_reference_bp.get('')
def image_reference_page():
    res = requests.get(f'{current_app.config.get("DARC_REVIEW_URL")}/image-reference')
    if res.status_code != 200:
        flash('Error retrieving image reference data', 'error')
        redirect('/')
    return render_template('image_reference/image-reference.html', image_references=res.text)


@image_reference_bp.post('')
def add_image_reference():
    res = requests.post(
        url=f'{current_app.config.get("DARC_REVIEW_URL")}/image-reference',
        headers=current_app.config.get('DARC_REVIEW_HEADERS'),
        data={'tator_localization_id': request.form.get('localizationId')},
    )
    if res.status_code != 201:
        flash('Error adding image reference', 'error')
        return redirect('/')
    flash('Image reference added successfully', 'success')
    return redirect('/')
