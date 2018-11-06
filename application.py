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

# Root directory of the project
ROOT_DIR = os.getcwd()

# Directory to save logs and trained model
MODEL_DIR = os.path.join(ROOT_DIR, "logs")

# Path to trained weights file
# Download this file and place in the root of your
# project (See README file for details)
COCO_MODEL_PATH = os.path.join(ROOT_DIR, "mask_rcnn_coco.pth")

# Directory of images to run detection on
IMAGE_DIR = os.path.join(ROOT_DIR, "images")

class InferenceConfig(coco.CocoConfig):
    # Set batch size to 1 since we'll be running inference on
    # one image at a time. Batch size = GPU_COUNT * IMAGES_PER_GPU
    # GPU_COUNT = 0 for CPU
    GPU_COUNT = 1
    IMAGES_PER_GPU = 1

config = InferenceConfig()

if not torch.cuda.is_available():
    config.GPU_COUNT = 0
config.display()

# Create model object.
model = modellib.MaskRCNN(model_dir=MODEL_DIR, config=config)
if config.GPU_COUNT:
    model = model.cuda()

# Load weights trained on MS-COCO
model.load_state_dict(torch.load(COCO_MODEL_PATH))

# COCO Class names
# Index of the class in the list is its ID. For example, to get ID of
# the teddy bear class, use: class_names.index('teddy bear')
class_names = ['BG', 'person', 'bicycle', 'car', 'motorcycle', 'airplane',
               'bus', 'train', 'truck', 'boat', 'traffic light',
               'fire hydrant', 'stop sign', 'parking meter', 'bench', 'bird',
               'cat', 'dog', 'horse', 'sheep', 'cow', 'elephant', 'bear',
               'zebra', 'giraffe', 'backpack', 'umbrella', 'handbag', 'tie',
               'suitcase', 'frisbee', 'skis', 'snowboard', 'sports ball',
               'kite', 'baseball bat', 'baseball glove', 'skateboard',
               'surfboard', 'tennis racket', 'bottle', 'wine glass', 'cup',
               'fork', 'knife', 'spoon', 'bowl', 'banana', 'apple',
               'sandwich', 'orange', 'broccoli', 'carrot', 'hot dog', 'pizza',
               'donut', 'cake', 'chair', 'couch', 'potted plant', 'bed',
               'dining table', 'toilet', 'tv', 'laptop', 'mouse', 'remote',
               'keyboard', 'cell phone', 'microwave', 'oven', 'toaster',
               'sink', 'refrigerator', 'book', 'clock', 'vase', 'scissors',
               'teddy bear', 'hair drier', 'toothbrush']

# Flask setting
app = Flask(__name__)
UPLOAD_FOLDER = os.path.basename('uploads')
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

@app.route("/")
def hello():
    return "Hello World!"

@app.route("/visualize", methods=['POST'])
def get_overlays():
    print(request.files)
    file_names = []
    for key in request.files.keys():
        file = request.files[key]

        f = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
        # add your custom code to check that the uploaded file is a valid image and not a malicious file (out-of-scope for this post)
        file.save(f)
        file_names.append(f)
    
    # Load a random image from the images folder
    image = skimage.io.imread(random.choice(file_names))

    # Run detection
    results = model.detect([image])
    r = results[0]
    visualize.display_instances(image, r['rois'], r['masks'], r['class_ids'],
                             class_names, r['scores'])
    plt.savefig('results.jpeg')

    return send_file("results.jpeg", mimetype='image/jpg')

@app.route("/extract", methods=['POST'])
def parse_objects():
    print(request.files)
    file_names = []
    for key in request.files.keys():
        file = request.files[key]

        f = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
        # add your custom code to check that the uploaded file is a valid image and not a malicious file (out-of-scope for this post)
        file.save(f)
        file_names.append(f)
    
    # Load a random image from the images folder
    image = skimage.io.imread(random.choice(file_names))

    # Run detection
    results = model.detect([image])
    r = results[0]

    outputs = fh.extract_bounding_boxes(image, r)
    fh.save_images_locally(outputs)

    if os.path.exists("result_0.jpg"):
        return send_file("result_0.jpg", mimetype='image/jpg')
    
    return "No objects detected"


@app.route('/base64', methods=['POST'])
def crop():
    # Get the image data from json 'base64Image'
    data = request.get_json()
    base64_image = data.get('base64Image')

    # Convert to image
    full_im = Image.open(BytesIO(base64.b64decode(base64_image)))
    img_format = full_im.format
    # Converts to array with only RGB channels
    image = np.array(full_im)[:,:,:3]

    # Run detection
    results = model.detect([image])
    r = results[0]

    # Get the outputs
    outputs = fh.extract_bounding_boxes(image, r)
    #fh.save_images_locally(outputs)
    output_strings = fh.outputs_to_base64(outputs, img_format)

    # Return response in json format
    return Response(dumps({'croppedImageList': output_strings}), mimetype='application/json')

if __name__ == '__main__':
    app.run(host='0.0.0.0')