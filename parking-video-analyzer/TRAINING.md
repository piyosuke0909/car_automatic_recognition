# Parking YOLO Fine-Tuning Flow

This project now supports three runtime profiles:

- `default`: current high-recall batch settings, including the temporary `cell phone -> car` alias.
- `realtime`: faster preview settings with lower image size and no tiling.
- `trained`: uses `models/parking_yolov8s/weights/best.pt` and removes the temporary label alias.

## 1. Extract Frames For Manual Labeling

```bash
python tools/extract_label_frames.py --split train --interval-seconds 1
python tools/extract_label_frames.py --split val --interval-seconds 5
```

Images are written under:

```text
dataset/images/train
dataset/images/val
```

## 2. Manual Labeling

Create YOLO-format `.txt` labels with the same filename stem as each image:

```text
dataset/labels/train/frame_000000.txt
dataset/labels/val/frame_000150.txt
```

Class index order:

```text
0 car
1 truck
2 bus
```

## 3. Create data.yaml

```bash
python tools/create_data_yaml.py
```

This writes:

```text
dataset/data.yaml
```

## 4. Fine-Tune YOLOv8s

```bash
python tools/train_yolov8s.py --epochs 50 --imgsz 960 --batch 8
```

The expected model path is:

```text
models/parking_yolov8s/weights/best.pt
```

## 5. Use The Fine-Tuned Model

```bash
python src/main.py --profile trained
```

For one-off model testing:

```bash
python src/main.py --profile realtime --model models/parking_yolov8s/weights/best.pt --disable-label-aliases
```
