# coco-annotator

person-pose-estimationのためのアノテーションツール  
[jsbroks/coco-annotator](https://github.com/jsbroks/coco-annotator)からforkしてきた。本家のwikiにドキュメントがある。

## 使い方
- GCPのサービスアカウントキーを取得してプロジェクトルートに配置
  - tonouchi-mlengine@juroujin-sandbox.iam.gserviceaccount.com
  - mlengineとgcsへの権限が付与してあればなんでもOK
  - 詳細はdocker-compose.build.ymlの環境変数を参照

- ビルド&サーバ起動
```
$ dc -f docker-compose.build.yml up -d --build
```

- サーバ停止
```
$ dc down
```

### アノテーションしたいデータの準備
- 再学習したいデータはjuroujin-sandbox-cocoannotator/datasets/以下のフォルダに保存すればpre_annotationしてくれるようになっている
- データセットpull用のapi作ったのでそれをswagger-ui上から叩く
  - パラメータはjuroujin-sandbox-cocoannotatorバケットのdatasets/直下のフォルダ名を指定
- アノテーションツールにアクセスして準備したdatasetへのpathを指定して作成
- pre_annotationファイルをインポートする
- 事前にモデルによるアノテーションが施されているため、人手による部分は微修正のみでよい


## Features
- 基本機能はOSSの方のwikiを参照
- 変更部分
  - 「pose estimation」の pre annotation機能（GUI上）
    - cloudml engineのopenposeにリクエスト飛ばしてる
  - dockerで立ち上げてるmongodbの分離
  - GCEへのデプロイのために一部改変
  - タスクの強制終了API
  - 一部ログインが必要なAPIをログイン不要化
  - pre annotationのバックグラウンドジョブ
    - これはgcsトリガーのcloud functionsでやってる

## 構成
- mongodb用のGCEインスタンス2台
  - asia-northeast1とasia-east1でレプリカセット組む
  - version3.2から２台構成でPRIMARY・SECONDARYの代替ができる
- アプリケーションサーバ用にGCEインスタンス1台
  - webserver, apiserver, rabbitmq, celeryが稼働
  - Container-Optimized OS選んでdocker-composeで起動する
