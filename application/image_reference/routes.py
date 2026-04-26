import requests
from flask import current_app, flash, render_template, redirect, request

from . import image_reference_bp


@image_reference_bp.get('')
def image_reference_page():
    res = requests.get(f'{current_app.config.get("DARC_REVIEW_URL")}/image-reference')
    if res.status_code != 200:
        flash('Error retrieving image reference data', 'error')
        return redirect('/')
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
                'lat': request.form.get('lat'),
                'long': request.form.get('long'),
                'depth_m': request.form.get('depth_m'),
                'temp_c': request.form.get('temp_c'),
                'salinity_m_l': request.form.get('salinity_m_l'),
                'attracted': request.form.get('attracted'),
            },
        )
    return res.json(), res.status_code


@image_reference_bp.get('/refresh/<image_reference_id>')
def refresh_image_reference(image_reference_id):
    res = requests.get(
        url=f'{current_app.config.get("DARC_REVIEW_URL")}/image-reference/refresh/{image_reference_id}',
        headers=current_app.config.get('DARC_REVIEW_HEADERS'),
    )
    return res.json(), res.status_code


@image_reference_bp.delete('')
def delete_image_reference():
    url = f'{current_app.config.get("DARC_REVIEW_URL")}/image-reference/{request.values.get("scientific_name")}'
    if request.values.get('elemental_id'):
        url += f'/{request.values.get("elemental_id")}'
    if request.values.get('morphospecies'):
        url += f'?morphospecies={request.values.get("morphospecies")}'
    elif request.values.get('tentative_id'):
        url += f'?tentative_id={request.values.get("tentative_id")}'
    res = requests.delete(
        url=url,
        headers=current_app.config.get('DARC_REVIEW_HEADERS'),
        data={
            'scientific_name': request.values.get('scientific_name'),
            'morphospecies': request.values.get('morphospecies'),
            'tentative_id': request.values.get('tentative_id'),
        },
    )
    return res.json(), res.status_code
