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
    if not request.form.get('scientific_name'):
        res = requests.post(
            url=f'{current_app.config.get("DARC_REVIEW_URL")}/image-reference',
            headers=current_app.config.get('DARC_REVIEW_HEADERS'),
            data={'tator_localization_id': request.form.get('localizationId')},
        )
    else:
        res = requests.post(
            url=f'{current_app.config.get("DARC_REVIEW_URL")}/image-reference',
            headers=current_app.config.get('DARC_REVIEW_HEADERS'),
            json={
                'scientific_name': request.form.get('scientific_name'),
                'morphospecies': request.form.get('morphospecies'),
                'tentative_id': request.form.get('tentative_id'),
                'deployment_name': request.form.get('deployment_name'),
                'section_id': request.form.get('section_id'),
                'tator_elemental_id': request.form.get('tator_elemental_id'),
                'localization_media_id': request.form.get('localization_media_id'),
                'localization_frame': request.form.get('localization_frame'),
                'localization_type': request.form.get('localization_type'),
                'normalized_top_left_x_y': (request.form.get('x'), request.form.get('y')),
                'normalized_dimensions': (request.form.get('width'), request.form.get('height')),
                'depth_m': request.form.get('depth_m'),
                'temp_c': request.form.get('temp_c'),
                'salinity_m_l': request.form.get('salinity_m_l'),
            },
        )
    return {}, res.status_code
