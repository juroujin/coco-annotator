from database import (
    ImageModel,
    TaskModel,
    DatasetModel
)

from celery import shared_task
from ..socket import create_socket

import os
import requests
from PIL import Image


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

                response = None
                try:
                    response = requests.post(
                        "http://35.200.126.224/api/model/openpose",
                        { "image": im })
                except:
                    task.error(f"Failed of request for /api/model/openpose")

                data = response.json()
                coco = data["coco"]
                images = coco["images"]
                categories = coco["categories"]
                annotations = coco["annotations"]

                if len(images) == 0 or len(categories) == 0 or len(annotations) == 0:
                    return

                indexedCategories = []
                for c in categories:
                    indexedCategories[c.id] = c

                for annotation in annotations:
                    keypoints = annotation["keyopints"]
                    segments = annotation["segmentation"]
                    category = indexedCategories[annotation["category_id"]]

                    if len(keypoints) == 0 and len(segments) == 0:
                        return

                    category = category["category"]

                    try:
                        requests.post(
                            "http://35.200.126.224/api/annotation",
                            { "image_id": db_image["id"],
                              "category_id": category["id"],
                              "segmentation": segments,
                              "keypoints": keypoints
                            })
                    except:
                        task.error(f"Failed of request for /api/annotation")

                count += 1
                task.info(f"Pre annotate file: {path}")

    task.info(f"Pre annotated {count} new image(s)")
    task.set_progress(100, socket=socket)

__all__ = ["pre_annotation"]
