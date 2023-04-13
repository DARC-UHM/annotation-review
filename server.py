import webbrowser
from threading import Timer
from flask import Flask, render_template

from jinja2 import Environment, FileSystemLoader

# initialize a flask object
app = Flask(__name__)
env = Environment(loader=FileSystemLoader("templates/"))

data = [
    {
        'concept': 'Chaceon quinquedens',
        'identity_certainty': 'NA',
        'identity_reference': 'identity-reference | self | 3',
        'comment': 'NA',
        'image_url': 'https://hurlimage.soest.hawaii.edu/SupplementalPhotos/D2photos/EX1404photos/EX1404L2_DIVE01_20140905/EX1404L2_IMG_20140905T212752Z_ROVHD_CRA.jpg',
        'upon': 'upon | sed | nil',
        'index_recorded_timestamp': '2014-09-05 21:27:52',
        'video_sequence_name': 'Deep Discoverer 14040201',
     },
    {
        'concept': 'Chaceon quinquedens',
        'identity_certainty': 'NA',
        'identity_reference': 'identity-reference | self | 3',
        'comment': 'NA',
        'image_url': 'https://hurlimage.soest.hawaii.edu/SupplementalPhotos/D2photos/EX1404photos/EX1404L2_DIVE01_20140905/EX1404L2_IMG_20140905T212752Z_ROVHD_CRA.jpg',
        'upon': 'upon | sed | nil',
        'index_recorded_timestamp': '2014-09-05 21:27:52',
        'video_sequence_name': 'Deep Discoverer 14040201',
    },
    {
        'concept': 'Chaceon quinquedens',
        'identity_certainty': 'NA',
        'identity_reference': 'identity-reference | self | 3',
        'comment': 'NA',
        'image_url': 'https://hurlimage.soest.hawaii.edu/SupplementalPhotos/D2photos/EX1404photos/EX1404L2_DIVE01_20140905/EX1404L2_IMG_20140905T212752Z_ROVHD_CRA.jpg',
        'upon': 'upon | sed | nil',
        'index_recorded_timestamp': '2014-09-05 21:27:52',
        'video_sequence_name': 'Deep Discoverer 14040201',
    },
    {
        'concept': 'Chaceon quinquedens',
        'identity_certainty': 'NA',
        'identity_reference': 'identity-reference | self | 3',
        'comment': 'NA',
        'image_url': 'https://hurlimage.soest.hawaii.edu/SupplementalPhotos/D2photos/EX1404photos/EX1404L2_DIVE01_20140905/EX1404L2_IMG_20140905T212752Z_ROVHD_CRA.jpg',
        'upon': 'upon | sed | nil',
        'index_recorded_timestamp': '2014-09-05 21:27:52',
        'video_sequence_name': 'Deep Discoverer 14040201',
    },
    {
        'concept': 'Chaceon quinquedens',
        'identity_certainty': 'NA',
        'identity_reference': 'identity-reference | self | 3',
        'comment': 'NA',
        'image_url': 'https://hurlimage.soest.hawaii.edu/SupplementalPhotos/D2photos/EX1404photos/EX1404L2_DIVE01_20140905/EX1404L2_IMG_20140905T212752Z_ROVHD_CRA.jpg',
        'upon': 'upon | sed | nil',
        'index_recorded_timestamp': '2014-09-05 21:27:52',
        'video_sequence_name': 'Deep Discoverer 14040201',
    },
    {
        'concept': 'Chaceon quinquedens',
        'identity_certainty': 'NA',
        'identity_reference': 'identity-reference | self | 3',
        'comment': 'NA',
        'image_url': 'https://hurlimage.soest.hawaii.edu/SupplementalPhotos/D2photos/EX1404photos/EX1404L2_DIVE01_20140905/EX1404L2_IMG_20140905T212752Z_ROVHD_CRA.jpg',
        'upon': 'upon | sed | nil',
        'index_recorded_timestamp': '2014-09-05 21:27:52',
        'video_sequence_name': 'Deep Discoverer 14040201',
    }
]

home = env.get_template('index.html')

@app.route("/")
def index():
    # return the rendered template
    return render_template(home, data=data)


def open_browser():
    webbrowser.open_new('http://127.0.0.1:5000')


# check to see if this is the main thread of execution
if __name__ == '__main__':
    # Timer(1, open_browser).start()
    app.run(debug=True)
