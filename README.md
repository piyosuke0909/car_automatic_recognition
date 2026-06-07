# parking-video-analyzer 要件定義

## 概要

`parking-video-analyzer` は、MP4動画から車両を検出・追跡し、車両位置、移動経路、エリアごとの混雑情報をJSONとして出力するPython製MVPである。

Unityとは別プロジェクトとして作成し、最初はリアルタイム解析ではなく、ローカル動画ファイル `input/parking_sample.mp4` を読み込んで解析する。

## 使用技術

- Python
- OpenCV
- Ultralytics YOLO
- NumPy
- JSON

## 対象スコープ

### MVPで行うこと

- `input/parking_sample.mp4` を読み込む。
- YOLOで `car`, `truck`, `bus` を検出する。
- 検出した車両に `vehicleId` を付与する。
- 各フレームごとの bbox、center、confidence、areaId を記録する。
- `vehicleId` ごとに移動経路 `route` を作成する。
- 動画画面をエリア分割し、各エリアの車両数を集計する。
- エリアごとに `congestionScore` と `heatLevel` を計算する。
- `output/analysis_result.json` に解析結果を出力する。
- 検出枠、`vehicleId`、`areaId` を描画した `output/annotated_video.mp4` を出力する。

### MVPで行わないこと

- 駐車場座標への変換
- カメラキャリブレーション
- リアルタイム処理
- Unity連携
- 駐車枠単位の占有判定
- ナンバープレート認識
- 複数動画の一括処理

## 入力

```text
input/parking_sample.mp4
```

入力動画はMP4形式とする。座標は動画フレーム上の画像座標 `x, y` を使用する。

## 出力

```text
output/analysis_result.json
output/annotated_video.mp4
```

`analysis_result.json` には解析データを出力する。

`annotated_video.mp4` には検出結果、追跡ID、エリア情報を描画した確認用動画を出力する。

## ディレクトリ構成

```text
parking-video-analyzer/
├─ input/
│  └─ parking_sample.mp4
├─ output/
│  ├─ analysis_result.json
│  └─ annotated_video.mp4
├─ src/
│  ├─ main.py
│  ├─ vehicle_detector.py
│  ├─ vehicle_tracker.py
│  ├─ area_analyzer.py
│  ├─ route_analyzer.py
│  ├─ json_exporter.py
│  └─ config.py
├─ requirements.txt
└─ README.md
```

## モジュール要件

### `src/main.py`

- 全体の処理を制御する。
- 動画を読み込む。
- フレームごとに検出、追跡、エリア判定、描画を実行する。
- JSON出力と動画出力を行う。

### `src/vehicle_detector.py`

- Ultralytics YOLOを使って車両を検出する。
- 検出対象は `car`, `truck`, `bus` とする。
- bbox、center、label、confidenceを返す。

### `src/vehicle_tracker.py`

- 検出結果に `vehicleId` を付与する。
- MVPでは中心点距離ベースの簡易追跡を行う。

### `src/area_analyzer.py`

- 画像座標上でエリアを定義する。
- 車両中心点から `areaId` を判定する。
- フレームごとのエリア別車両数を集計する。
- エリアごとの混雑スコアを計算する。

### `src/route_analyzer.py`

- `vehicleId` ごとに中心点履歴を蓄積する。
- 車両ごとの `route` を生成する。

### `src/json_exporter.py`

- 解析結果をJSON形式に整形する。
- `output/analysis_result.json` に保存する。

### `src/config.py`

- 入力パス、出力パス、モデル名、しきい値、エリア分割設定などを管理する。

## JSON出力要件

トップレベルの形式は以下を満たす。

```json
{
  "source": "mp4_video",
  "videoFile": "input/parking_sample.mp4",
  "fps": 30,
  "frameCount": 0,
  "duration": 0,
  "vehicles": [],
  "frames": [],
  "areas": []
}
```

### `vehicles`

車両ごとの情報を格納する。

```json
{
  "vehicleId": "vehicle_1",
  "label": "car",
  "firstFrame": 0,
  "lastFrame": 120,
  "route": [
    {
      "frameIndex": 0,
      "x": 100,
      "y": 200,
      "areaId": "area_1"
    }
  ]
}
```

### `frames`

フレームごとの検出結果を格納する。

```json
{
  "frameIndex": 0,
  "timestamp": 0.0,
  "detections": [
    {
      "vehicleId": "vehicle_1",
      "label": "car",
      "confidence": 0.95,
      "bbox": {
        "x1": 10,
        "y1": 20,
        "x2": 200,
        "y2": 180
      },
      "center": {
        "x": 105,
        "y": 100
      },
      "areaId": "area_1"
    }
  ],
  "areaCounts": {
    "area_1": 1,
    "area_2": 0
  }
}
```

### `areas`

エリアごとの混雑集計を格納する。

```json
{
  "areaId": "area_1",
  "name": "Area 1",
  "bounds": {
    "x1": 0,
    "y1": 0,
    "x2": 640,
    "y2": 360
  },
  "averageCarCount": 1.5,
  "maxCarCount": 4,
  "congestionScore": 35.0,
  "heatLevel": "medium"
}
```

## 混雑スコア要件

混雑スコアは以下の式で計算する。

```text
congestionScore = averageCarCount * 10 + maxCarCount * 5
```

`heatLevel` は以下の基準で判定する。

```text
0-30: low
31-60: medium
61以上: high
```

## 確認用動画の描画要件

`output/annotated_video.mp4` には以下を描画する。

- 車両のbbox
- `vehicleId`
- label
- confidence
- `areaId`
- エリア境界線
- エリアごとの現在車両数

## 実行方法

```bash
python src/main.py
```

## セットアップ方法

実装時は以下の流れでセットアップする。

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

必要ライブラリは `requirements.txt` にまとめる。

## 受け入れ条件

- `python src/main.py` で解析が実行できる。
- `output/analysis_result.json` が生成される。
- `output/annotated_video.mp4` が生成される。
- JSONに `source`, `videoFile`, `fps`, `frameCount`, `duration`, `vehicles`, `frames`, `areas` が含まれる。
- `vehicles` に車両ごとの経路情報が含まれる。
- `frames` にフレームごとの検出情報が含まれる。
- `areas` にエリアごとの混雑情報が含まれる。
- 確認用動画にbbox、`vehicleId`、label、confidence、`areaId`、エリア境界線、エリアごとの現在車両数が描画される。
