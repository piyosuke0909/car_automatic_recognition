import argparse
import sys
from pathlib import Path
from time import perf_counter

import cv2

from analysis_reporter import write_tuning_report
from area_analyzer import AreaAnalyzer
from config import (
    AREA_LINE_COLOR,
    AREA_TEXT_COLOR,
    BOX_COLOR,
    DEFAULT_FPS,
    TEXT_BG_COLOR,
    TEXT_COLOR,
    available_profiles,
    load_profile,
    selected_parameters,
)
from json_exporter import export_analysis
from performance_reporter import write_performance_report
from route_analyzer import RouteAnalyzer
from vehicle_detector import VehicleDetector
from vehicle_tracker import VehicleTracker


def main(argv=None):
    args = parse_args(argv)
    try:
        profile = load_profile(
            args.profile,
            model_override=args.model,
            disable_label_aliases=args.disable_label_aliases,
        )
    except ValueError as exc:
        print(str(exc), file=sys.stderr)
        return 2

    if args.output_dir:
        apply_output_dir(profile, args.output_dir)

    input_video_path = profile["input_video_path"]
    if not input_video_path.exists():
        print(f"Input video not found: {input_video_path}", file=sys.stderr)
        return 1

    profile["output_json_path"].parent.mkdir(parents=True, exist_ok=True)

    capture = cv2.VideoCapture(to_opencv_path(input_video_path))
    if not capture.isOpened():
        print(f"Failed to open input video: {input_video_path}", file=sys.stderr)
        return 1

    fps = capture.get(cv2.CAP_PROP_FPS) or DEFAULT_FPS
    if fps <= 0:
        fps = DEFAULT_FPS

    width = int(capture.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(capture.get(cv2.CAP_PROP_FRAME_HEIGHT))
    if width <= 0 or height <= 0:
        print("Failed to read video dimensions.", file=sys.stderr)
        capture.release()
        return 1

    writer = None
    if not args.skip_video_output:
        writer = create_video_writer(profile["output_video_path"], fps, width, height)
        if not writer.isOpened():
            print(
                f"Warning: failed to open output video, continuing without video: "
                f"{profile['output_video_path']}",
                file=sys.stderr,
            )
            writer = None

    detector = VehicleDetector(
        profile["yolo_model_name"],
        profile["target_labels"],
        profile["confidence_threshold"],
        profile["label_aliases"],
        profile["yolo_image_size"],
        profile["bbox_filter"],
        profile["enable_full_frame_detection"],
        profile["enable_tiled_detection"],
        profile["tile_rows"],
        profile["tile_columns"],
        profile["tile_overlap_pixels"],
        profile["nms_iou_threshold"],
    )
    tracker = VehicleTracker(
        profile["track_max_distance"],
        profile["track_max_missed_frames"],
    )
    area_analyzer = AreaAnalyzer(
        width,
        height,
        profile["area_rows"],
        profile["area_columns"],
    )
    route_analyzer = RouteAnalyzer()

    frames = []
    area_count_history = []
    frame_timings = []
    frame_index = 0
    run_started_at = perf_counter()

    print(f"Profile: {profile['name']}")
    print(f"Model: {profile['yolo_model_name']}")

    try:
        while True:
            if args.max_frames and frame_index >= args.max_frames:
                break

            ok, frame = capture.read()
            if not ok:
                break

            frame_started_at = perf_counter()
            detection_started_at = perf_counter()
            detections = detector.detect(frame)
            detection_seconds = perf_counter() - detection_started_at

            tracking_started_at = perf_counter()
            tracked_detections = tracker.update(detections, frame_index)
            tracking_seconds = perf_counter() - tracking_started_at

            area_route_started_at = perf_counter()
            for detection in tracked_detections:
                detection["areaId"] = area_analyzer.get_area_id(detection["center"])

            area_counts = area_analyzer.count_by_area(tracked_detections)
            area_count_history.append(area_counts)
            route_analyzer.update(frame_index, tracked_detections)
            area_route_seconds = perf_counter() - area_route_started_at

            frames.append(
                {
                    "frameIndex": int(frame_index),
                    "timestamp": round(frame_index / fps, 3),
                    "detections": tracked_detections,
                    "areaCounts": area_counts,
                }
            )

            draw_write_started_at = perf_counter()
            if writer is not None:
                annotated_frame = frame.copy()
                draw_areas(annotated_frame, area_analyzer.areas, area_counts)
                draw_detections(annotated_frame, tracked_detections)
                writer.write(annotated_frame)
            draw_write_seconds = perf_counter() - draw_write_started_at
            frame_total_seconds = perf_counter() - frame_started_at

            frame_timings.append(
                {
                    "frameIndex": int(frame_index),
                    "detectionCount": len(tracked_detections),
                    "frame_total_seconds": round(frame_total_seconds, 6),
                    "detection_seconds": round(detection_seconds, 6),
                    "tracking_seconds": round(tracking_seconds, 6),
                    "area_route_seconds": round(area_route_seconds, 6),
                    "draw_write_seconds": round(draw_write_seconds, 6),
                }
            )

            frame_index += 1
            if frame_index % profile["progress_interval_frames"] == 0:
                print(f"Processed {frame_index} frames")
    finally:
        capture.release()
        if writer is not None:
            writer.release()

    total_wall_seconds = perf_counter() - run_started_at
    vehicles = route_analyzer.build_vehicles()
    areas = area_analyzer.summarize(area_count_history)
    duration = frame_index / fps if fps else 0

    analysis_result = export_analysis(
        output_path=profile["output_json_path"],
        video_file=profile["input_video_relative"],
        fps=fps,
        frame_count=frame_index,
        duration=duration,
        vehicles=vehicles,
        frames=frames,
        areas=areas,
    )
    parameters = selected_parameters(profile)
    write_tuning_report(
        profile["output_tuning_report_path"],
        analysis_result,
        parameters,
    )
    write_performance_report(
        profile["output_performance_report_path"],
        analysis_result,
        parameters,
        frame_timings,
        total_wall_seconds,
    )

    print(f"Analysis JSON: {profile['output_json_path']}")
    print(f"Tuning report: {profile['output_tuning_report_path']}")
    print(f"Performance report: {profile['output_performance_report_path']}")
    if writer is not None:
        print(f"Annotated video: {profile['output_video_path']}")
    else:
        print("Annotated video: skipped")
    print(f"Processed frames: {frame_index}")
    return 0


def parse_args(argv):
    parser = argparse.ArgumentParser(description="Analyze parking-lot video.")
    parser.add_argument(
        "--profile",
        choices=available_profiles(),
        default="default",
        help="Runtime configuration profile.",
    )
    parser.add_argument(
        "--model",
        default=None,
        help="Override the YOLO model path/name for the selected profile.",
    )
    parser.add_argument(
        "--disable-label-aliases",
        action="store_true",
        help="Disable temporary label aliases such as cell phone -> car.",
    )
    parser.add_argument(
        "--max-frames",
        type=int,
        default=0,
        help="Stop after this many frames. 0 means process the full video.",
    )
    parser.add_argument(
        "--skip-video-output",
        action="store_true",
        help="Skip annotated video writing and only generate JSON reports.",
    )
    parser.add_argument(
        "--output-dir",
        default=None,
        help="Override output directory. Relative paths are resolved from the current directory.",
    )
    return parser.parse_args(argv)


def apply_output_dir(profile, output_dir):
    output_dir = Path(output_dir)
    if not output_dir.is_absolute():
        output_dir = Path.cwd() / output_dir

    profile["output_json_path"] = output_dir / "analysis_result.json"
    profile["output_video_path"] = output_dir / "annotated_video.mp4"
    profile["output_tuning_report_path"] = output_dir / "tuning_report.json"
    profile["output_performance_report_path"] = output_dir / "performance_report.json"


def create_video_writer(path, fps, width, height):
    fourcc = cv2.VideoWriter_fourcc(*"mp4v")
    return cv2.VideoWriter(to_opencv_path(path), fourcc, fps, (width, height))


def to_opencv_path(path):
    path = Path(path)
    try:
        return str(path.relative_to(Path.cwd()))
    except ValueError:
        return str(path)


def draw_areas(frame, areas, area_counts):
    for area in areas:
        bounds = area["bounds"]
        area_id = area["areaId"]
        x1 = bounds["x1"]
        y1 = bounds["y1"]
        x2 = bounds["x2"]
        y2 = bounds["y2"]

        cv2.rectangle(frame, (x1, y1), (x2, y2), AREA_LINE_COLOR, 1)
        label = f"{area_id}: {area_counts.get(area_id, 0)}"
        draw_label(frame, label, x1 + 6, y1 + 20, AREA_TEXT_COLOR)


def draw_detections(frame, detections):
    for detection in detections:
        bbox = detection["bbox"]
        x1 = bbox["x1"]
        y1 = bbox["y1"]
        x2 = bbox["x2"]
        y2 = bbox["y2"]

        cv2.rectangle(frame, (x1, y1), (x2, y2), BOX_COLOR, 2)

        label = (
            f"{detection['vehicleId']} "
            f"{detection['label']} "
            f"{detection['confidence']:.2f} "
            f"{detection.get('areaId', 'unknown')}"
        )
        draw_label(frame, label, x1, max(y1 - 6, 14), TEXT_COLOR)


def draw_label(frame, text, x, y, text_color):
    font = cv2.FONT_HERSHEY_SIMPLEX
    scale = 0.5
    thickness = 1
    (text_width, text_height), baseline = cv2.getTextSize(text, font, scale, thickness)
    x = max(0, min(x, frame.shape[1] - text_width - 2))
    y = max(text_height + 2, min(y, frame.shape[0] - baseline - 2))

    cv2.rectangle(
        frame,
        (x, y - text_height - baseline - 2),
        (x + text_width + 4, y + baseline + 2),
        TEXT_BG_COLOR,
        -1,
    )
    cv2.putText(frame, text, (x + 2, y), font, scale, text_color, thickness, cv2.LINE_AA)


if __name__ == "__main__":
    raise SystemExit(main())
