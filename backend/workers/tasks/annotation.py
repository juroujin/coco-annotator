from database import (
    ImageModel,
    TaskModel,
    DatasetModel
)

from celery import shared_task
from ..socket import create_socket

import requests
from PIL import Image

keypoints_order = [0, 15, 14, 17, 16, 5, 2, 6, 3, 7, 4, 11, 8, 12, 9, 13, 10]


@shared_task
def pre_annotation(task_id, image_id):

    task = TaskModel.objects.get(id=task_id)
    image = ImageModel.objects.get(id=image_id)

    task.update(status="PROGRESS")
    socket = create_socket()

    path = image.path
    task.info(f"Pre annotation {path}")

    im = Image.open(path).convert('RGB')
    response = requests.post(
        "http://localhost:5000/api/model/openpose",
        { "image": im })

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

        requests.post(
            "http://localhost:5000/api/annotation",
            { "image_id": image_id,
              "category_id": category["id"],
              "segmentation": segments,
              "keypoints": keypoints
            })

    task.info(f"Annotated {path}")
    task.set_progress(100, socket=socket)

__all__ = ["pre_annotation"]
