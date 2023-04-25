import webbrowser
import requests
from flask import Flask, render_template, request, redirect, url_for
from jinja2 import Environment, FileSystemLoader
from image_loader import ImageLoader
from annosaurus import *
from env.env import *

# initialize a flask object
app = Flask(__name__)
env = Environment(loader=FileSystemLoader('templates/'))
home = env.get_template('index.html')
images = env.get_template('internal_review.html')

# get concept list from vars (for input validation)
with requests.get('http://hurlstor.soest.hawaii.edu:8083/kb/v1/concept') as r:
    vars_concepts = r.json()


@app.route('/favicon.ico')
def favicon():
    return app.send_static_file('img/favicon.ico')


@app.route('/')
def index():
    # return the rendered template
    return render_template(home)


@app.get('/dive')
def view_images():
    # get images in sequence
    sequence_name = request.args.get('sequence')
    image_loader = ImageLoader([sequence_name.replace('%20', ' ')])
    data = {'annotations': image_loader.distilled_records, 'concepts': vars_concepts}
    # return the rendered template
    return render_template(images, data=data)


""" FOR TESTING """
@app.post('/add_annotation')
def add_annotation():
    image_loader = ImageLoader(['Deep Discoverer 14040203'])
    annosaurus = Annosaurus(ANNOSAURUS_URL)
    '''
    this doesn't work :)
    annosaurus.update_annotation(
        {
            'observation_uuid': '5f41d4f8-62a1-464d-4f64-4b32c308de1e',
            'concept': 'rob concept UPDATE',
            'elapsed_time_millis': 4854851,
            'recorded_date': '2021-11-29T13:18:17.851Z'
        },
        ANNOSAURUS_CLIENT_SECRET
    )
    '''
    '''
    annosaurus.create_annotation(
        video_reference_uuid='a6349903-d6c7-4c08-8343-f33fa06caa58',
        concept='rob test concept',
        observer='rob',
        elapsed_time_millis=4854851,
        recorded_timestamp=datetime.today(),
        client_secret=ANNOSAURUS_CLIENT_SECRET
    )
    
    annosaurus.create_association(
        observation_uuid='125e4bd4-25c4-44c0-fb68-32e24e39de1e',
        association={
            'link_name': 'test',
            'to_concept': 'it\'s',
            'link_value': 'WORKINGGG'
        },
        client_secret=ANNOSAURUS_CLIENT_SECRET
    )
    
    
    annosaurus.update_association(
        uuid='1d6589f3-bc51-4dd2-796b-92fc173bde1e',
        association={'link_value': 'Lets be serious'},
        client_secret=ANNOSAURUS_CLIENT_SECRET
    )
    '''

    data = {'annotations': image_loader.distilled_records}

    return render_template(images, data=data)


@app.post('/update_annotation')
def update_annotation():
    annosaurus = Annosaurus(ANNOSAURUS_URL)
    updated_annotation = {
        'concept': request.values.get('editConceptName'),
        'identity-certainty': request.values.get('editIdCert'),
        'identity-reference': request.values.get('editIdRef'),
        'upon': request.values.get('editUpon'),
        'comment': request.values.get('editComments'),
        'guide-photo': request.values.get('editGuidePhoto'),
    }

    annosaurus.update_annotation(
        observation_uuid=request.values.get('observation_uuid'),
        updated_annotation=updated_annotation,
        client_secret=ANNOSAURUS_CLIENT_SECRET
    )

    return redirect(f'dive?sequence={request.values.get("sequenceName")}')


def open_browser():
    webbrowser.open_new('http://127.0.0.1:5000')


# check to see if this is the main thread of execution
if __name__ == '__main__':
    # Timer(1, open_browser).start()
    app.run(debug=True)
