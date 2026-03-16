import json

import tator
import requests
from flask import current_app, flash, redirect, session


def init_tator_api():
    if 'tator_token' not in session:
        flash('Please log in to Tator', 'info')
        return None, redirect('/')
    try:
        api = tator.get_api(
            host=current_app.config.get('TATOR_URL'),
            token=session['tator_token'],
        )
        return api, None
    except tator.openapi.tator_openapi.exceptions.ApiException as e:
        flash(json.loads(e.body)['message'], 'danger')
        return None, redirect('/')


def get_comments_and_image_refs(deployment_names: list[str]) -> tuple[dict, dict]:
    comments = {}
    image_refs = {}
    try:
        for deployment in deployment_names:
            comment_res = requests.get(
                url=f'{current_app.config.get("DARC_REVIEW_URL")}/comment/sequence/{deployment}',
                headers=current_app.config.get('DARC_REVIEW_HEADERS'),
            )
            if comment_res.status_code != 200:
                raise requests.exceptions.ConnectionError
            comments |= comment_res.json()
        image_ref_res = requests.get(f'{current_app.config.get("DARC_REVIEW_URL")}/image-reference/quick')
        if image_ref_res.status_code != 200:
            raise requests.exceptions.ConnectionError
        image_refs = image_ref_res.json()
    except requests.exceptions.ConnectionError:
        print('\nERROR: unable to connect to external review server\n')
    return comments, image_refs
