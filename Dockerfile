FROM jsbroks/coco-annotator:python-env

WORKDIR /workspace/
COPY ./backend/ /workspace/
COPY ./.git /workspace/.git
RUN python set_path.py
RUN pip install google-api-python-client

COPY ./client/dist /workspace/dist
COPY ./datasets /datasets
COPY ./models /models
COPY ./juroujin-sandbox-f1eeaadf8ed6.json /juroujin-sandbox-f1eeaadf8ed6.json

ENV FLASK_ENV=production
ENV DEBUG=false

ENV SECRET_KEY=RandomSecretKeyHere
ENV FILE_WATCHER=true
ENV NAME="Test Annotator"
ENV GOOGLE_APPLICATION_CREDENTIALS=/juroujin-sandbox-f1eeaadf8ed6.json
ENV MASK_RCNN_FILE=/models/mask_rcnn_coco.h5
ENV MASK_RCNN_CLASSES="BG,person,bicycle,car,motorcycle,airplane, \
    bus,train,truck,boat,traffic light, \
    fire hydrant,stop sign,parking meter,bench,bird, \
    cat,dog,horse,sheep,cow,elephant,bear, \
    zebra,giraffe,backpack,umbrella,handbag,tie, \
    suitcase,frisbee,skis,snowboard,sports ball, \
    kite,baseball bat,baseball glove,skateboard, \
    surfboard,tennis racket,bottle,wine glass,cup, \
    fork,knife,spoon,bowl,banana',apple, \
    sandwich,orange,broccoli,carrot,hot dog,pizza, \
    donut,cake,chair,couch,potted plant,bed, \
    dining table,toilet,tv,laptop,mouse,remote, \
    keyboard,cell phone,microwave,oven,toaster, \
    sink,refrigerator,book,clock,vase,scissors, \
    teddy bear,hair drier,toothbrush"

EXPOSE 5000
#CMD gunicorn -c webserver/gunicorn_config.py webserver:app --no-sendfile --timeout 180

