import traceback
from concurrent.futures import ThreadPoolExecutor, as_completed
from json import JSONDecodeError

from flask import flash, render_template, request, session

from application import app
from application.util.constants import TERM_NORMAL, TERM_RED
from application.vars.annosaurus import *


@app.route('/favicon.ico')
def favicon():
    return app.send_static_file('img/favicon.ico')


@app.route('/')
def index():
    def fetch_json(url, headers=None):
        try:
            res = requests.get(url, headers=headers)
            res.raise_for_status()
            return res.json(), None
        except requests.exceptions.RequestException as e:
            msg = f'Unable to connect to {url}: {e}'
            print(f'{TERM_RED}ERROR{TERM_NORMAL}: {msg}')
            return None, msg
        except JSONDecodeError:
            msg = f'Failed to parse JSON from {url}'
            print(f'{TERM_RED}ERROR{TERM_NORMAL}: {msg}')
            return None, msg

    http_requests = [
        dict(name='reviewers', url=f'{app.config["DARC_REVIEW_URL"]}/reviewer/all', headers=app.config['DARC_REVIEW_HEADERS']),
        dict(name='stats', url=f'{app.config["DARC_REVIEW_URL"]}/stats', headers=app.config['DARC_REVIEW_HEADERS']),
        dict(name='sequences', url=app.config['VARS_SEQUENCE_LIST_URL']),
        dict(name='concepts', url=app.config['VARS_CONCEPT_LIST_URL'])
    ]
    results = {}
    errors = []
    with ThreadPoolExecutor(max_workers=4) as executor:
        future_to_name = {
            executor.submit(fetch_json, url=item['url'], headers=item.get('headers')): item['name']
            for item in http_requests
        }
        for future in as_completed(future_to_name):
            name = future_to_name[future]
            data, error = future.result()
            results[name] = data
            if error:
                errors.append(error)

    for error in errors:
        flash(error, 'danger')

    stats = results.get('stats') or {}
    session['reviewers'] = results.get('reviewers') or []
    session['vars_video_sequences'] = results.get('sequences') or []
    session['vars_concepts'] = results.get('concepts') or []

    return render_template(
        'index.html',
        sequences=session['vars_video_sequences'],
        unread_comment_count=stats.get('unread_comments', 0),
        read_comment_count=stats.get('read_comments', 0),
        total_comment_count=stats.get('total_comments', 0),
        active_reviewers=stats.get('active_reviewers', []),
    )


# video player
@app.get('/video')
def video():
    data = {'link': request.args.get('link'), 'time': request.args.get('time')}
    return render_template('video.html', data=data), 200


@app.errorhandler(404)
def page_not_found(e):
    return render_template('errors/404.html', err=''), 404


@app.errorhandler(Exception)
def server_error(e):
    error = f'{type(e).__name__}: {e}'
    print('\nApplication error 😔')
    print(error)
    print(traceback.format_exc())
    requests.post(
        url=f'{app.config.get("DARC_REVIEW_URL")}/log-error',
        headers=app.config.get('DARC_REVIEW_HEADERS'),
        json={'error': traceback.format_exc()},
    )
    return render_template('errors/500.html', err=error), 500
