
npm-install:
	@curl -sL https://deb.nodesource.com/setup_10.x | sudo -E bash -
	@sudo apt install nodejs npm

build-client:
	@~/coco-annotator/client/ && npm install -g --quiet @vue/cli@3.3.0 @vue/cli-service@3.3.0
	@~/coco-annotator/client/ && npm install
	@export NODE_PATH="~/coco-annotator/client/node_modules"
	@~/coco-annotator/client/ && npm run build
	@mv -f ~/coco-annotator/client/dist ~/coco-annotator/backend/dist

setup-maskrcnn:
	@git clone --single-branch --depth 1 https://github.com/matterport/Mask_RCNN.git /tmp/maskrcnn
	@cd /tmp/maskrcnn && pip install -r requirements.txt && python3 setup.py install

setup-app:
	@cd ~/coco-annotator/backend/ && pip install -r requirements.txt
	@pip install gunicorn[eventlet]==19.9.0 pycocotools google-api-python-client
	@cd ~/coco-annotator/backend/ && python set_path.py

run:
	@cd ~/coco-annotator/backend/ && gunicorn -c webserver/gunicorn_config.py webserver:app --no-sendfile --timeout 180
