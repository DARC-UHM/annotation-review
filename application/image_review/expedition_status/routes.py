"""
Expedition annotation status for the office.

/image-review/expedition-status [GET, PATCH]

The external review server works out the expedition names (application/expedition_name.py in external-image-review),
so the names here always match the expedition filter on the reviewer page.
"""

from urllib.parse import quote

import requests
from flask import current_app, flash, render_template, request

from . import expedition_status_bp

REVIEW_SERVER_TIMEOUT = (10, 30)  # (connect, read) seconds


def _review_url(path=''):
    return f'{current_app.config.get("DARC_REVIEW_URL")}/expedition-status{path}'


def _is_valid_status(value):
    # bool is a subclass of int, so check the exact type to reject true/false
    return type(value) is int and 0 <= value <= 2


@expedition_status_bp.get('')
def expedition_status_page():
    statuses = []
    try:
        res = requests.get(
            _review_url(),
            headers=current_app.config.get('DARC_REVIEW_HEADERS'),
            timeout=REVIEW_SERVER_TIMEOUT,
        )
        if res.status_code == 200:
            statuses = res.json()
        else:
            current_app.logger.info(f'Unable to load expedition statuses: {res.status_code} {res.text[:200]}')
            flash('Unable to load expedition statuses from the external review server.', 'danger')
    except (requests.RequestException, ValueError) as error:  # ValueError covers a response that isn't JSON
        current_app.logger.info(f'Unable to load expedition statuses: {error}')
        flash('Unable to reach the external review server.', 'danger')
    return render_template('image_review/expedition-status.html', statuses=statuses)


@expedition_status_bp.patch('')
def patch_expedition_status():
    body = request.get_json(silent=True)
    if not isinstance(body, dict):
        body = {}
    expedition_name = body.get('expedition_name')
    status = body.get('status')
    if not isinstance(expedition_name, str) or not expedition_name.strip():
        return {'error': 'expedition_name is required'}, 400
    if not _is_valid_status(status):
        return {'error': 'status must be the integer 0, 1, or 2'}, 400
    try:
        res = requests.patch(
            url=_review_url(f'/{quote(expedition_name, safe="")}'),
            headers=current_app.config.get('DARC_REVIEW_HEADERS'),
            json={'status': status},
            timeout=REVIEW_SERVER_TIMEOUT,
        )
    except requests.RequestException as error:
        current_app.logger.info(f'Unable to update expedition status for {expedition_name}: {error}')
        return {'error': 'Unable to reach the external review server'}, 502
    try:
        payload = res.json()
    except ValueError:
        payload = {'error': f'External review server returned {res.status_code}'}
    return payload, res.status_code
