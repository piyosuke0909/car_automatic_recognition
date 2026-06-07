import argparse
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parents[1]
DEFAULT_CLASSES = ("car", "truck", "bus")


def main():
    args = parse_args()
    dataset_dir = Path(args.dataset_dir)
    if not dataset_dir.is_absolute():
        dataset_dir = BASE_DIR / dataset_dir

    create_dataset_dirs(dataset_dir)
    output_path = Path(args.output)
    if not output_path.is_absolute():
        output_path = dataset_dir / output_path

    classes = [name.strip() for name in args.classes.split(",") if name.strip()]
    if not classes:
        raise SystemExit("At least one class name is required.")

    output_path.write_text(build_yaml(args.path_value, classes), encoding="utf-8")
    print(f"Wrote {output_path}")


def create_dataset_dirs(dataset_dir):
    for relative_path in (
        "images/train",
        "images/val",
        "labels/train",
        "labels/val",
    ):
        (dataset_dir / relative_path).mkdir(parents=True, exist_ok=True)


def build_yaml(path_value, classes):
    lines = [
        f"path: {path_value}",
        "train: images/train",
        "val: images/val",
        "names:",
    ]
    for index, class_name in enumerate(classes):
        lines.append(f"  {index}: {class_name}")
    return "\n".join(lines) + "\n"


def parse_args():
    parser = argparse.ArgumentParser(description="Create YOLO data.yaml.")
    parser.add_argument(
        "--dataset-dir",
        default="dataset",
        help="Dataset directory. Relative paths are resolved from parking-video-analyzer.",
    )
    parser.add_argument(
        "--output",
        default="data.yaml",
        help="Output YAML path. Relative paths are resolved from --dataset-dir.",
    )
    parser.add_argument(
        "--classes",
        default=",".join(DEFAULT_CLASSES),
        help="Comma-separated class names in YOLO label index order.",
    )
    parser.add_argument(
        "--path-value",
        default=".",
        help="Value written to the YAML path field.",
    )
    return parser.parse_args()


if __name__ == "__main__":
    main()
