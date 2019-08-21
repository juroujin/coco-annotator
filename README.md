# coco-annotator

person-pose-estimationのためのアノテーションツール  
[jsbroks/coco-annotator](https://github.com/jsbroks/coco-annotator)からforkしてきた。本家のwikiにドキュメントがある。

## 使い方
- アノテーションしたいデータの準備
```
# アノテーションサーバが稼働しているインスタンスにsshでつなぐ
$ docker run -v 567325:/tmp -it google/cloud-sdk:latest gsutil -m cp -r gs://juroujin-sandbox-measurement-result/video/5673251619471360/5673251619471360-9223372035290071807-hsg3so/lt_foot_standing_front/original_image/ /tmp/
```

- アノテーションツールにアクセスして準備したdatasetへのpathを指定して作成


## オリジナルからの変更項目
- 「pose estimation」の pre annotation機能
  - cloudml engineのopenposeにリクエスト飛ばしてる
- GCE上へのデプロイのために改変

## 構成
- mongodb用のGCEインスタンス2台
  - asia-northeast1とasia-east1でレプリカセット組む
  - version3.2から２台構成でPRIMARY・SECONDARYの代替ができる
- アプリケーションサーバ用にGCEインスタンス1台
  - webserver, apiserver, rabbitmq, celeryが稼働
  - Container-Optimized OS選んでdocker-composeで起動する


## 開発
- clientの開発をした場合は以下のコマンドでビルドし直す必要がある
    
```
# コンテナ内でビルドして
$ docker build -t build-client -f Dockerfile.vue .
# とりあえずコンテナ起動
$ docker run --name client.temp -it build-client ls
# 元のビルド済みdirを削除
$ rm -rf ./client/dist
# ホスト側にコピー
$ docker cp client.temp:/workspace/client/dist ./client/
$ docker rm client.temp

# 全体をビルドし直し，起動
$ dc -f docker-compose.build.yml up -d --build
```

## TODOs
- body25への対応
- アノテーション済みデータセットのGCSへの出力
- pre annotationのスケジューリング
  - 現状は一個一個手動でやってる