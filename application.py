import os
import sys
import random
import math
import numpy as np
import skimage.io
import matplotlib
import matplotlib.pyplot as plt

import coco
import utils
import model as modellib
import visualize

import torch
from flask import Flask, request, send_file, Response
import flask_helpers as fh
from io import BytesIO
import base64
from PIL import Image
from json import dumps


MODEL, CLASS_NAMES = fh.get_default_model()

# Flask setting
app = Flask(__name__)
UPLOAD_FOLDER = os.path.basename('uploads')
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

@app.route("/")
def hello():
    return "Hello World!"

@app.route("/changemodel", methods=['POST'])
def change_model():
    global MODEL
    global CLASS_NAMES
    data = request.get_json()
    model_name = data.get('modelName')
    model_url = data.get('modelUrl')
    class_names = data.get('classNames')

    MODEL, CLASS_NAMES = fh.set_model(model_name, model_url, class_names)

    return "Successfully updated model to {}".format(model_name)

@app.route("/visualize", methods=['POST'])
def return_visualized_image():
    print(request.files)
    file_names = []
    for key in request.files.keys():
        file = request.files[key]

        f = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
        # add your custom code to check that the uploaded file is a valid image and not a malicious file (out-of-scope for this post)
        file.save(f)
        file_names.append(f)
    
    # Load a random image from the images folder
    image = skimage.io.imread(random.choice(file_names))[:,:,:3]

    # Run detection
    results = MODEL.detect([image])
    r = results[0]
    visualize.display_instances(image, r['rois'], r['masks'], r['class_ids'],
                             CLASS_NAMES, r['scores'])
    plt.savefig('results.jpeg')

    return send_file("results.jpeg", mimetype='image/jpg')

@app.route("/extract", methods=['POST'])
def extract_first_object():
    print(request.files)
    file_names = []
    for key in request.files.keys():
        file = request.files[key]

        f = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
        # add your custom code to check that the uploaded file is a valid image and not a malicious file (out-of-scope for this post)
        file.save(f)
        file_names.append(f)
    
    # Load a random image from the images folder
    image = skimage.io.imread(random.choice(file_names))[:,:,:3]

    # Run detection
    results = MODEL.detect([image])
    r = results[0]

    outputs = fh.extract_bounding_boxes(image, r)
    fh.save_images_locally(outputs)

    if os.path.exists("result_0.jpg"):
        return send_file("result_0.jpg", mimetype='image/jpg')
    
    return "No objects detected"


@app.route('/base64', methods=['POST'])
def mask_base64_objects():
    # Get the image data from json 'base64Image'
    data = request.get_json()
    base64_image = data.get('base64Image')

    # Convert to image
    full_im = Image.open(BytesIO(base64.b64decode(base64_image)))
    img_format = full_im.format
    # Converts to array with only RGB channels
    image = np.array(full_im)[:,:,:3]

    # Run detection
    results = MODEL.detect([image])
    r = results[0]

    # Get the outputs
    outputs = fh.extract_bounding_boxes(image, r)
    #fh.save_images_locally(outputs)
    output_strings = fh.outputs_to_base64(outputs, img_format)

    # Return response in json format
    return Response(dumps({'croppedImageList': output_strings}), mimetype='application/json')

if __name__ == '__main__':
    app.run(host='0.0.0.0')