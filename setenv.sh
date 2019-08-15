#!/usr/bin/env bash

export SECRET_KEY="RandomSecretKeyHere"
export FILE_WATCHER=true
export NAME="Test Annotator"
export GOOGLE_APPLICATION_CREDENTIALS="~/coco-annotator/juroujin-sandbox-f1eeaadf8ed6.json"
export MASK_RCNN_FILE="~/coco-annotator/models/mask_rcnn_coco.h5"
export MASK_RCNN_CLASSES="
        BG,person,bicycle,car,motorcycle,airplane,
        bus,train,truck,boat,traffic light,
        fire hydrant,stop sign,parking meter,bench,bird,
        cat,dog,horse,sheep,cow,elephant,bear,
        zebra,giraffe,backpack,umbrella,handbag,tie,
        suitcase,frisbee,skis,snowboard,sports ball,
        kite,baseball bat,baseball glove,skateboard,
        surfboard,tennis racket,bottle,wine glass,cup,
        fork,knife,spoon,bowl,banana',apple,
        sandwich,orange,broccoli,carrot,hot dog,pizza,
        donut,cake,chair,couch,potted plant,bed,
        dining table,toilet,tv,laptop,mouse,remote,
        keyboard,cell phone,microwave,oven,toaster,
        sink,refrigerator,book,clock,vase,scissors,
        teddy bear,hair drier,toothbrush"
export FLASK_ENV="production"
export DEBUG=false
