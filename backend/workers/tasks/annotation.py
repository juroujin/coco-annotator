from database import (
    ImageModel,
    TaskModel,
    DatasetModel
)
from webserver.util.mask_rcnn import model as maskrcnn

from celery import shared_task
from ..socket import create_socket

import os
import requests
from PIL import Image

# GCP settings
project = 'juroujin-sandbox'
model = 'pose_estimation'
version = 'v0_1'


@shared_task
def pre_annotation(task_id, dataset_id):

    task = TaskModel.objects.get(id=task_id)
    task.info(f"aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa")
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
