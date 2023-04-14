import webbrowser
import requests
from threading import Timer
from flask import Flask, render_template
from jinja2 import Environment, FileSystemLoader
from util import *

# initialize a flask object
app = Flask(__name__)
env = Environment(loader=FileSystemLoader("templates/"))
home = env.get_template('index.html')
concept_phylogeny = {}

with requests.get('http://hurlstor.soest.hawaii.edu:8086/query/dive/Deep%20Discoverer%2014040201') as r:
    response = r.json()

image_records = []
video_sequence_name = response['media'][0]['video_sequence_name']

for annotation in response['annotations']:
    concept_name = annotation['concept']
    if annotation['image_references'] and concept_name[0].isupper():
        image_records.append(annotation)
        if concept_name not in concept_phylogeny.keys():
            # get the phylogeny from VARS kb
            concept_phylogeny[concept_name] = {}
            with requests.get(f'http://hurlstor.soest.hawaii.edu:8083/kb/v1/phylogeny/up/{concept_name}') \
                    as vars_tax_res:
                if vars_tax_res.status_code == 200:
                    # this get us to kingdom
                    vars_tree = vars_tax_res.json()['children'][0]['children'][0]['children'][0]['children'][0]
                    while 'children' in vars_tree.keys():
                        concept_phylogeny[concept_name][vars_tree['rank']] = vars_tree['name']
                        vars_tree = vars_tree['children'][0]
                else:
                    print(f'Unable to find record for {annotation["concept"]}')


distilled_records = []

for record in image_records:
    # convert hyphens to underlines and remove excess data
    id_cert = 'NA'
    id_ref = 'NA'
    upon = 'NA'
    comment = 'NA'
    url = ''

    temp = get_association(record, 'identity-certainty')
    if temp:
        id_cert = temp['link_value']
    temp = get_association(record, 'identity-reference')
    if temp:
        id_ref = temp['link_value']
    temp = get_association(record, 'upon')
    if temp:
        code = temp['to_concept']
        upon = translate_substrate_code(code) if translate_substrate_code(code) else code
    temp = get_association(record, 'comment')
    if temp:
        comment = temp['link_value']

    url = record['image_references'][0]['url']
    for i in range(1, len(record['image_references'])):
        if '.png' in record['image_references'][i]['url']:
            url = record['image_references'][i]['url']
            break

    url = url.replace('http://hurlstor.soest.hawaii.edu/imagearchive', 'https://hurlimage.soest.hawaii.edu')

    distilled_records.append({
        'concept': record['concept'],
        'identity_certainty': id_cert,
        'identity_reference': id_ref,
        'comment': comment,
        'image_url': url,
        'upon': upon,
        'recorded_timestamp': record['recorded_timestamp'],
        'video_sequence_name': video_sequence_name,
    })


@app.route("/")
def index():
    # return the rendered template
    return render_template(home, data=distilled_records)


def open_browser():
    webbrowser.open_new('http://127.0.0.1:5000')


# check to see if this is the main thread of execution
if __name__ == '__main__':
    # Timer(1, open_browser).start()
    app.run(debug=True)
