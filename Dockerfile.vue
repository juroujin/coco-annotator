FROM node:10

WORKDIR /workspace/
COPY ./client /workspace/client

RUN npm install -g --quiet \
    @vue/cli@3.3.0 \
    @vue/cli-service@3.3.0

COPY ./client/package* /workspace/

RUN npm install
ENV NODE_PATH=/workspace/node_modules

WORKDIR /workspace/client
RUN npm run build

