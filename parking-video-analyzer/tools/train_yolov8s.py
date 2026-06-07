import argparse
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parents[1]


def main():
    args = parse_args()
    data_yaml = Path(args.data)
    if not data_yaml.is_absolute():
        data_yaml = BASE_DIR / data_yaml

    if not data_yaml.exists():
        raise SystemExit(f"data.yaml not found: {data_yaml}")

    try:
        from ultralytics import YOLO
    except ImportError as exc:
        raise SystemExit(
            "Ultralytics is not installed. Run: pip install -r requirements.txt"
        ) from exc

    model = YOLO(args.base_model)
    results = model.train(
        data=str(data_yaml),
        epochs=args.epochs,
        imgsz=args.imgsz,
        batch=args.batch,
        project=str(BASE_DIR / "models"),
        name=args.name,
        exist_ok=args.exist_ok,
        patience=args.patience,
    )

    print(results)
    print(f"Expected best model: {BASE_DIR / 'models' / args.name / 'weights' / 'best.pt'}")


def parse_args():
    parser = argparse.ArgumentParser(description="Fine-tune YOLOv8s for parking video.")
    parser.add_argument("--data", default="dataset/data.yaml", help="YOLO data.yaml path.")
    parser.add_argument("--base-model", default="yolov8s.pt", help="Base YOLO model.")
    parser.add_argument("--epochs", type=int, default=50, help="Training epochs.")
    parser.add_argument("--imgsz", type=int, default=960, help="Training image size.")
    parser.add_argument("--batch", type=int, default=8, help="Training batch size.")
    parser.add_argument("--patience", type=int, default=15, help="Early stopping patience.")
    parser.add_argument(
        "--name",
        default="parking_yolov8s",
        help="Run name under parking-video-analyzer/models.",
    )
    parser.add_argument(
        "--exist-ok",
        action="store_true",
        help="Allow writing into an existing training run directory.",
    )
    return parser.parse_args()


if __name__ == "__main__":
    main()
