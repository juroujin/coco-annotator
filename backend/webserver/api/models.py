from flask_restplus import Namespace, Resource, reqparse
from werkzeug.datastructures import FileStorage
from imantics import Mask
from flask_login import login_required
from config import Config
from PIL import Image
from database import ImageModel

import os
import logging
import numpy as np
import base64
import io
import cv2
from scipy.ndimage.filters import gaussian_filter
import googleapiclient.discovery

logger = logging.getLogger('gunicorn.error')


MASKRCNN_LOADED = os.path.isfile(Config.MASK_RCNN_FILE)
if MASKRCNN_LOADED:
    from ..util.mask_rcnn import model as maskrcnn
else:
    logger.warning("MaskRCNN model is disabled.")

DEXTR_LOADED = os.path.isfile(Config.DEXTR_FILE)
if DEXTR_LOADED:
    from ..util.dextr import model as dextr
else:
    logger.warning("DEXTR model is disabled.")

api = Namespace('model', description='Model related operations')


image_upload = reqparse.RequestParser()
image_upload.add_argument('image', location='files', type=FileStorage, required=True, help='Image')

dextr_args = reqparse.RequestParser()
dextr_args.add_argument('points', location='json', type=list, required=True)
dextr_args.add_argument('padding', location='json', type=int, default=50)
dextr_args.add_argument('threshold', location='json', type=int, default=80)

# GCP settings
project = 'juroujin-sandbox'
model = 'pose_estimation'
version = 'v0_1'


@api.route('/dextr/<int:image_id>')
class MaskRCNN(Resource):

    @login_required
    @api.expect(dextr_args)
    def post(self, image_id):
        """ COCO data test """

        if not DEXTR_LOADED:
            return {"disabled": True, "message": "DEXTR is disabled"}, 400

        args = dextr_args.parse_args()
        points = args.get('points')
        # padding = args.get('padding')
        # threshold = args.get('threshold')

        if len(points) != 4:
            return {"message": "Invalid points entered"}, 400
        
        image_model = ImageModel.objects(id=image_id).first()
        if not image_model:
            return {"message": "Invalid image ID"}, 400
        
        image = Image.open(image_model.path)
        result = dextr.predict_mask(image, points)

        return { "segmentaiton": Mask(result).polygons().segmentation }


@api.route('/maskrcnn')
class MaskRCNN(Resource):

    #@login_required
    @api.expect(image_upload)
    def post(self):
        """ COCO data test """
        if not MASKRCNN_LOADED:
            return {"disabled": True, "coco": {}}

        args = image_upload.parse_args()
        im = Image.open(args.get('image'))
        coco = maskrcnn.detect(im)
        return {"coco": coco}


@api.route('/openpose')
class OpenPose(Resource):

    #@login_required
    @api.expect(image_upload)
    def post(self):

        """ COCO object detection """
        if not MASKRCNN_LOADED:
            return {"disabled": True, "coco": {}}

        args = image_upload.parse_args()
        im = Image.open(args.get('image')).convert('RGB')
        coco = maskrcnn.detect(im)

        """ COCO keypoints """
        h, w, _ = np.shape(im)

        if h > w:
            s1 = w / 368
            s2 = h / 656
            im = im.resize((368, 656))
        else:
            s1 = w / 656
            s2 = h / 368
            im = im.resize((656, 368))

        service = googleapiclient.discovery.build('ml', 'v1')
        name = 'projects/{}/models/{}'.format(project, model)
        if version is not None:
            name += '/versions/{}'.format(version)

        instanses = []
        img_bytes = io.BytesIO()
        im.save(img_bytes, format='JPEG')
        encoded_img = base64.b64encode(img_bytes.getvalue()).decode('utf-8')
        instanses.extend([{"image_bytes": {"b64": encoded_img}}])

        response = service.projects().predict(
            name=name,
            body={'instances': instanses}
        ).execute()

        if 'error' in response:
            raise RuntimeError(response['error'])

        heatmaps = response['predictions']
        all_peaks = postprocess(heatmaps[0])

        for i in range(len(all_peaks)):
            if all_peaks[i]:
                all_peaks[i][0] *= s1
                all_peaks[i][1] *= s2
            else:
                all_peaks[i] = [0.0, 0.0, 0.0]

        all_peaks = np.array(all_peaks).flatten().astype(np.int)
        coco.get('annotations')[0]['keypoints'] = all_peaks.tolist()

        return {"coco": coco}


def postprocess(x):
    x = np.squeeze(x)
    x = cv2.resize(x, (0, 0), fx=8, fy=8, interpolation=cv2.INTER_CUBIC)

    all_peaks = []

    keypoints_order = [0, 15, 14, 17, 16, 5, 2, 6, 3, 7, 4, 11, 8, 12, 9, 13, 10]

    for part in keypoints_order:
        map_ori = x[:, :, part]
        map = gaussian_filter(map_ori, sigma=3)

        map_left = np.zeros(map.shape)
        map_left[1:, :] = map[:-1, :]
        map_right = np.zeros(map.shape)
        map_right[:-1, :] = map[1:, :]
        map_up = np.zeros(map.shape)
        map_up[:, 1:] = map[:, :-1]
        map_down = np.zeros(map.shape)
        map_down[:, :-1] = map[:, 1:]

        peaks_binary = np.logical_and.reduce(
            (map >= map_left, map >= map_right, map >= map_up, map >= map_down, map > 0.1))
        peaks = list(zip(np.nonzero(peaks_binary)[1], np.nonzero(peaks_binary)[0]))  # note reverse

        con = 0
        peak_with_score = []
        for p in peaks:
            c = map_ori[p[1], p[0]]
            if c > con:
                con = c
                peak_with_score = [p[0], p[1], con]
        all_peaks.append(peak_with_score)

    return all_peaks
