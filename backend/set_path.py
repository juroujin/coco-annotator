
import sys

paths = [
    '~/coco-annotator/backend/'
]

for path in paths:
    if path not in sys.path:
        sys.path.append(path)
