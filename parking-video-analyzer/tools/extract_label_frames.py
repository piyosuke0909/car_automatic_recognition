import argparse
from pathlib import Path

import cv2


BASE_DIR = Path(__file__).resolve().parents[1]


def main():
    args = parse_args()
    input_path = Path(args.input)
    if not input_path.is_absolute():
        input_path = BASE_DIR / input_path

    output_dir = BASE_DIR / "dataset" / "images" / args.split
    output_dir.mkdir(parents=True, exist_ok=True)

    capture = cv2.VideoCapture(str(input_path))
    if not capture.isOpened():
        raise SystemExit(f"Failed to open input video: {input_path}")

    fps = capture.get(cv2.CAP_PROP_FPS) or 30.0
    interval_frames = args.interval_frames
    if interval_frames is None:
        interval_frames = max(1, round(fps * args.interval_seconds))

    frame_index = 0
    saved_count = 0
    try:
        while True:
            ok, frame = capture.read()
            if not ok:
                break

            should_save = (
                frame_index >= args.start_frame
                and (frame_index - args.start_frame) % interval_frames == 0
            )
            if should_save:
                output_path = output_dir / f"frame_{frame_index:06d}.jpg"
                cv2.imwrite(str(output_path), frame)
                saved_count += 1
                if args.max_frames and saved_count >= args.max_frames:
                    break

            frame_index += 1
    finally:
        capture.release()

    print(f"Saved {saved_count} frames to {output_dir}")


def parse_args():
    parser = argparse.ArgumentParser(
        description="Extract still frames for manual YOLO labeling."
    )
    parser.add_argument(
        "--input",
        default="input/parking_sample.mp4",
        help="Input video path. Relative paths are resolved from parking-video-analyzer.",
    )
    parser.add_argument(
        "--split",
        choices=("train", "val"),
        default="train",
        help="Dataset split to write into.",
    )
    parser.add_argument(
        "--interval-seconds",
        type=float,
        default=1.0,
        help="Seconds between extracted frames when --interval-frames is omitted.",
    )
    parser.add_argument(
        "--interval-frames",
        type=int,
        default=None,
        help="Frames between extracted images. Overrides --interval-seconds.",
    )
    parser.add_argument(
        "--start-frame",
        type=int,
        default=0,
        help="First frame index eligible for extraction.",
    )
    parser.add_argument(
        "--max-frames",
        type=int,
        default=0,
        help="Stop after this many saved frames. 0 means no limit.",
    )
    return parser.parse_args()


if __name__ == "__main__":
    main()
