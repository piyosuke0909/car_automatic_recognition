# 進捗メモ

最終更新: 2026-06-07

## 現在の目的

駐車場動画 `input/parking_sample.mp4` から車両を検出し、フレームごとの車両位置、車両IDごとの追跡履歴、エリアごとの混雑状況をJSONで取得する。

## ここまで実装済み

- MP4動画の読み込み
- YOLOv8による物体検出
- 検出bbox、中心座標、信頼度の取得
- `vehicleId` による簡易追跡
- 画面を2行 x 3列に分けたエリア判定
- エリア別の車両数集計
- 車両IDごとの移動履歴作成
- `analysis_result.json` 出力
- `tuning_report.json` 出力
- `performance_report.json` 出力
- profile設定の導入
- `realtime` profileの高リコール設定化
- 手作業ラベル付け、`data.yaml` 作成、YOLOv8s追加学習用スクリプト追加

## 使用技術

- Python
- OpenCV
- Ultralytics YOLOv8
- JSON

## 現在の実行profile

`realtime` profileを主に使用している。

```text
使用モデル: yolov8n.pt
信頼度しきい値: 0.10
YOLO入力画像サイズ: 1280
分割検出: 有効
分割行数: 2
分割列数: 3
分割時の重なり幅: 80px
重複除去しきい値: 0.45
同一車両とみなす最大距離: 55.0
見失い許容フレーム数: 45
```

## 現在の検出対象ラベル

```text
car
truck
bus
cell phone
bottle
```

## 現在のラベル置き換え

標準YOLOが俯瞰の駐車車両を `car` として認識しにくいため、暫定的に以下の置き換えをしている。

```text
cell phone -> car
bottle -> car
```

JSONには置き換え後の `label` だけでなく、YOLOが元々出した `sourceLabel` も残している。

## 最新JSONで取得できているデータ

対象ファイル:

```text
output/analysis_result.json
output/tuning_report.json
output/performance_report.json
```

最新の解析概要:

```text
解析フレーム数: 907
動画時間: 30.233秒
総検出数: 112438
追跡車両ID数: 232
```

最終ラベル別の検出数:

```text
car: 112352
bus: 86
```

YOLOの元ラベル別の検出数:

```text
cell phone: 86095
bottle: 25878
car: 379
bus: 86
```

信頼度分布:

```text
最小: 0.10
中央値: 0.4951
平均: 0.485
最大: 0.9331
```

エリア別集計:

```text
area_1 平均車両数: 27.076 最大車両数: 30 混雑レベル: high
area_2 平均車両数: 27.863 最大車両数: 31 混雑レベル: high
area_3 平均車両数: 28.518 最大車両数: 32 混雑レベル: high
area_4 平均車両数: 15.698 最大車両数: 18 混雑レベル: high
area_5 平均車両数: 14.946 最大車両数: 18 混雑レベル: high
area_6 平均車両数: 9.865 最大車両数: 13 混雑レベル: high
```

## `analysis_result.json` に入っているデータ

トップレベル:

```text
source: データ元の種類
videoFile: 解析対象動画
fps: FPS
frameCount: 総フレーム数
duration: 動画時間
vehicles: 車両IDごとの追跡結果
frames: フレームごとの検出結果
areas: エリアごとの混雑集計
```

`frames`:

```text
frameIndex: フレーム番号
timestamp: 動画内時刻
detections: そのフレームの検出一覧
areaCounts: そのフレームのエリア別車両数
```

`detections`:

```text
vehicleId: 追跡用車両ID
label: 最終ラベル
sourceLabel: YOLOの元ラベル
labelAliasApplied: ラベル置き換えをしたか
confidence: 検出信頼度
bbox: 検出枠座標
center: 検出枠の中心座標
areaId: 所属エリア
```

`vehicles`:

```text
vehicleId: 車両ID
label: 車両ラベル
firstFrame: 最初に検出されたフレーム
lastFrame: 最後に検出されたフレーム
route: フレームごとの移動履歴
```

`areas`:

```text
areaId: エリアID
name: エリア名
bounds: エリア範囲
averageCarCount: 平均車両数
maxCarCount: 最大車両数
congestionScore: 混雑スコア
heatLevel: 混雑レベル
```

## 現在わかっている課題

- 標準YOLOの `yolov8n.pt` は、俯瞰の駐車場車両を `car` としてほとんど認識できていない。
- 実際には `cell phone` と `bottle` として多く検出されているため、暫定的に `car` に置き換えている。
- `area_6` は他エリアより検出数が少ない。右端・下端の部分表示、実際の車両数の少なさ、別ラベル化が原因として考えられる。
- 追跡は中心点距離ベースの簡易実装なので、車両IDが実車数より多くなることがある。
- 根本的な精度改善には、駐車場画像での追加学習が必要。

## 次にやること

1. 現在の `cell phone -> car` と `bottle -> car` の暫定設定で、出力動画とJSONを目視確認する。
2. 誤検出が多ければ `confidenceThreshold` を `0.12` または `0.15` に上げる。
3. 漏れが多ければ `confidenceThreshold` を `0.08` まで下げる。
4. 手作業ラベル付けを行い、`yolov8s.pt` で追加学習する。
5. 学習済みモデルを `trained` profileで使い、暫定ラベル置き換えを外す。

## 主な実行コマンド

```powershell
cd C:\プログラム\車認識\car_automatic_recognition\parking-video-analyzer
.\.venv\Scripts\python.exe src\main.py --profile realtime
```

ラベル用フレーム抽出:

```powershell
.\.venv\Scripts\python.exe tools\extract_label_frames.py --split train --interval-seconds 1
.\.venv\Scripts\python.exe tools\extract_label_frames.py --split val --interval-seconds 5
```

追加学習:

```powershell
.\.venv\Scripts\python.exe tools\create_data_yaml.py
.\.venv\Scripts\python.exe tools\train_yolov8s.py --epochs 50 --imgsz 960 --batch 8
```
