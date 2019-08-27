from database import (
    ImageModel,
    TaskModel,
    DatasetModel
)
from config import Config

from celery import shared_task
from ..socket import create_socket

import os
import requests
from PIL import Image
import cv2
import base64
import io
import numpy as np
from scipy.ndimage.filters import gaussian_filter
import googleapiclient.discovery


MASKRCNN_LOADED = os.path.isfile(Config.MASK_RCNN_FILE)
if MASKRCNN_LOADED:
    from webserver.util.mask_rcnn import model as maskrcnn

# GCP settings
project = 'juroujin-sandbox'
model = 'pose_estimation'
version = 'v0_1'

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


@shared_task
def pre_annotation(task_id, dataset_id):

    task = TaskModel.objects.get(id=task_id)
    dataset = DatasetModel.objects.get(id=dataset_id)

    task.update(status="PROGRESS")
    socket = create_socket()

    directory = dataset.directory
    toplevel = list(os.listdir(directory))
    task.info(f"Pre annotation {directory}")

    count = 0
    for root, dirs, files in os.walk(directory):

        try:
            youarehere = toplevel.index(root.split('/')[-1])
            progress = int(((youarehere)/len(toplevel))*100)
            task.set_progress(progress, socket=socket)
        except:
            pass

        if root.split('/')[-1].startswith('.'):
            continue

        for file in files:
            path = os.path.join(root, file)

            if path.endswith(ImageModel.PATTERN):
                db_image = ImageModel.objects(path=path).first()

                if db_image is None:
                    continue

                im = None
                try:
                    im = Image.open(path).convert("RGB")
                except:
                    task.warning(f"Could not read {path}")


                coco = maskrcnn.detect(im)
                """ COCO keypoints """
                """
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

                """
                images = coco["images"]
                categories = coco["categories"]
                annotations = coco["annotations"]

                if len(images) == 0 or len(categories) == 0 or len(annotations) == 0:
                    continue

                indexedCategories = []
                for c in categories:
                    indexedCategories[c.id] = c

                for annotation in annotations:
                    #keypoints = annotation["keyopints"]
                    segments = annotation["segmentation"]
                    category = indexedCategories[annotation["category_id"]]

                    #if len(keypoints) == 0 and len(segments) == 0:
                    #    continue

                    category = category["category"]

                    try:
                        requests.post(
                            "http://localhost/api/annotation",
                            { "image_id": db_image["id"],
                              "category_id": category["id"],
                              "segmentation": segments,
                              #"keypoints": keypoints
                            })
                    except:
                        task.error(f"Failed of request for /api/annotation")

                count += 1
                task.info(f"Pre annotate file: {path}")

    task.info(f"Pre annotated {count} new image(s)")
    task.set_progress(100, socket=socket)

__all__ = ["pre_annotation"]
