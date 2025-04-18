"""
General endpoints for VARS annotations/associations that are used throughout the application.

/vars/annotation/<observation_uuid> [GET]
/vars/annotation/concept [PATCH]
/vars/association [POST]
/vars/association/<uuid> [PATCH]
/vars/association/<uuid> [DELETE]
/vars/video-frame [GET]
"""

from io import BytesIO
from pathlib import Path

import requests
from flask import current_app, request, send_file

from . import vars_bp
from application.vars.annosaurus import Annosaurus


# get a single VARS annotation
@vars_bp.get('/annotation/<observation_uuid>')
def get_current_associations(observation_uuid):
    res = requests.get(url=f'{current_app.config.get("VARS_ANNOTATION_URL")}/{observation_uuid}')
    if res.status_code != 200:
        return {}, res.status_code
    return res.json(), 200


# updates annotation with a new concept name
@vars_bp.patch('/annotation/concept')
def update_annotation():
    annosaurus = Annosaurus(current_app.config.get('ANNOSAURUS_URL'))
    updated_response = annosaurus.update_concept_name(
        observation_uuid=request.values.get('observation_uuid'),
        concept=request.values.get('concept'),
        client_secret=current_app.config.get('ANNOSAURUS_CLIENT_SECRET'),
    )
    return updated_response['json'], updated_response['status']


# creates a new association for a VARS annotation
@vars_bp.post('/association')
def create_association():
    annosaurus = Annosaurus(current_app.config.get('ANNOSAURUS_URL'))
    new_association = {
        'link_name': request.values.get('link_name'),
        'link_value': request.values.get('link_value'),
        'to_concept': request.values.get('to_concept'),
    }
    created_response = annosaurus.create_association(
        observation_uuid=request.values.get('observation_uuid'),
        association=new_association,
        client_secret=current_app.config.get('ANNOSAURUS_CLIENT_SECRET'),
    )
    if created_response['status'] == 200:
        created_response['status'] = 201
    return created_response['json'], created_response['status']


# updates a VARS association
@vars_bp.patch('/association/<uuid>')
def update_association(uuid):
    annosaurus = Annosaurus(current_app.config.get('ANNOSAURUS_URL'))
    updated_association = {
        'link_name': request.values.get('link_name'),
        'link_value': request.values.get('link_value'),
        'to_concept': request.values.get('to_concept'),
    }
    updated_response = annosaurus.update_association(
        association_uuid=uuid,
        association=updated_association,
        client_secret=current_app.config.get('ANNOSAURUS_CLIENT_SECRET'),
    )
    return updated_response['json'], updated_response['status']


# deletes a VARS association
@vars_bp.delete('/association/<uuid>')
def delete_association(uuid):
    annosaurus = Annosaurus(current_app.config.get('ANNOSAURUS_URL'))
    deleted = annosaurus.delete_association(
        association_uuid=uuid,
        client_secret=current_app.config.get('ANNOSAURUS_CLIENT_SECRET'),
    )
    return deleted['json'], deleted['status']


# gets a frame from a VARS video for annotations without an image. caches images locally
@vars_bp.get('/video-frame')
def video_frame():
    try:
        import cv2
        from PIL import Image
    except ModuleNotFoundError:
        print('To display video frames, install cv2 and PIL by running the command "pip install -r requirements.txt"')
        return {}, 500
    video_url = request.args.get('url')
    timestamp = int(request.args.get('time', 0))
    if not video_url:
        print('Missing video URL')
        return {}, 400
    cache_dir = Path('cache', 'vars_frames')
    cache_dir.mkdir(exist_ok=True)
    cache_path = cache_dir / f'{video_url.split("/")[-1].split(".")[0]}__{timestamp}.jpeg'
    if cache_path.exists():
        with open(cache_path, 'rb') as f:
            return send_file(
                BytesIO(f.read()),
                mimetype='image/jpeg',
                as_attachment=False
            )
    cap = cv2.VideoCapture(video_url)
    if not cap.isOpened():
        print('Could not open video file')
        return {}, 500
    frame_number = timestamp * cap.get(cv2.CAP_PROP_FPS)  # calc frame number
    cap.set(cv2.CAP_PROP_POS_FRAMES, frame_number)  # set to frame
    ret, frame = cap.read()  # get frame
    cap.release()  # release video
    if not ret:
        print(f'Could not read frame at timestamp {timestamp}')
        return {}, 500
    frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)  # Convert BGR to RGB
    img = Image.fromarray(frame)
    img_byte_arr = BytesIO()
    img.save(img_byte_arr, format='JPEG')
    frame_data = img_byte_arr.getvalue()
    with open(cache_path, 'wb') as f:
        f.write(frame_data)
    return send_file(
        BytesIO(frame_data),
        mimetype='image/jpeg',
        as_attachment=False
    )
