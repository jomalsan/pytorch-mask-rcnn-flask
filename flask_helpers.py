import numpy as np
from PIL import Image
from io import BytesIO
import base64

# Global vars
ENCODING = 'utf-8'

def extract_bounding_boxes(image, results, apply_mask=True):
    """Slices regions defined by bounding box into separate images
    Inputs:
        image: np.array, original image
        results: results object, results of maskrcnn
        apply_mask: boolean, toggles if the mask should be applied
    Output:
        output_images: list of np.arrays, image segments
    """
    bounding_boxes = results['rois']
    output_images = []
    
    try:
        num_images = bounding_boxes.shape[0]
        for ix in range(num_images):
            cur_image = image.copy()
            if apply_mask:
                cur_mask = np.squeeze(results['masks'][:,:,ix])
                cur_image[cur_mask==0,:] = 255
            
            #bbox array [num_instances, (y1, x1, y2, x2)].
            bb = bounding_boxes[ix,:]
            cur_out = cur_image[bb[0]:bb[2], bb[1]:bb[3]]
            
            output_images.append(cur_out)
            
    except Exception as e:
        print(e)
    
    return output_images

def save_images_locally(output_images):
    """Saves the results of extract_bounding_boxes locally
    Inputs:
        output_images: list of np.arrays, image segments
    """

    for ix in range(len(output_images)):
        cur_img = Image.fromarray(output_images[ix])
        save_name = "result_{}.jpg".format(ix)
        cur_img.save(save_name)

def outputs_to_base64(output_images, img_format):
    """Converts the output images to a list of base64 strings
    Input:
        output_images: list of np.arrays, image segments
        img_format: string, format of original image
    Output:
        output_strings: list of string, base64 encoded images
    """
    output_strings = []
    # Encode back to base64 to send back to ImageProcessing function
    for ix in range(len(output_images)):
        cur_image = Image.fromarray(output_images[ix])

        cropped_img_bytes = BytesIO()
        cur_image.save(cropped_img_bytes, format=img_format)
        cropped_img_bytes = cropped_img_bytes.getvalue()
        base64_bytes = base64.b64encode(cropped_img_bytes)

        base64_string = base64_bytes.decode(ENCODING)
        output_strings.append(base64_string)
    
    return output_strings