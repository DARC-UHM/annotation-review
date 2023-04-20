import webbrowser
from flask import Flask, render_template, request, redirect, url_for
from jinja2 import Environment, FileSystemLoader
from review_image_loader import ReviewImageLoader
from sequences import sequences

# initialize a flask object
app = Flask(__name__)
env = Environment(loader=FileSystemLoader('templates/'))
home = env.get_template('index.html')
images = env.get_template('external_review.html')


@app.route('/')
def index():
    # return the rendered template
    return render_template(home)


@app.get('/review/<reviewer_name>')
def review(reviewer_name):
    # get images in sequence
    image_loader = ReviewImageLoader(sequences, reviewer_name)
    data = {'annotations': image_loader.distilled_records, 'reviewer': reviewer_name.title()}
    # return the rendered template
    return render_template(images, data=data)


@app.post('/update_annotation')
def update_annotation():
    image_loader = ImageLoader([request.values.get('sequenceName')])
    
    print(request.values)

    # get updated annotation from request
    # delete old annotation
    # push new annotation

    data = {'annotations': image_loader.distilled_records, 'messages': 'Annotation updated!'}
    return render_template(images, data=data)


def open_browser():
    webbrowser.open_new('http://127.0.0.1:5000')


# check to see if this is the main thread of execution
if __name__ == '__main__':
    # Timer(1, open_browser).start()
    app.run(debug=True)
