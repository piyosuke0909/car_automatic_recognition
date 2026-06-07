# parking-video-analyzer

MP4動画から車両を検出・追跡し、車両位置、移動経路、エリアごとの混雑情報をJSONとして出力するMVPです。

## セットアップ

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

## 入力

解析対象の動画を以下に配置します。

```text
input/parking_sample.mp4
```

## 実行

```bash
python src/main.py
```

初回実行時に `yolov8n.pt` が自動ダウンロードされる場合があります。

## 出力

```text
output/analysis_result.json
output/annotated_video.mp4
```

`analysis_result.json` には以下を出力します。

- `vehicles`: 車両ごとのID、ラベル、検出開始フレーム、最終検出フレーム、移動経路
- `frames`: フレームごとの検出結果、bbox、中心点、信頼度、エリアID、エリア別車両数
- `areas`: エリアごとの平均車両数、最大車両数、混雑スコア、heatLevel

## JSON形式

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

## 混雑スコア

```text
congestionScore = averageCarCount * 10 + maxCarCount * 5
```

```text
0-30: low
31-60: medium
61以上: high
```

## 実装メモ

- 検出対象は `car`, `truck`, `bus` です。
- 追跡は中心点距離ベースの簡易実装です。
- エリア判定は画像座標で行います。
- 初期状態では画面を横3列、縦2行に分割します。
- 駐車場座標への変換は行いません。
