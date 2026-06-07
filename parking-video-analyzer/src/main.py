import sys

import cv2

from area_analyzer import AreaAnalyzer
from config import (
    AREA_COLUMNS,
    AREA_LINE_COLOR,
    AREA_ROWS,
    AREA_TEXT_COLOR,
    BOX_COLOR,
    CONFIDENCE_THRESHOLD,
    DEFAULT_FPS,
    INPUT_VIDEO_PATH,
    INPUT_VIDEO_RELATIVE,
    OUTPUT_DIR,
    OUTPUT_JSON_PATH,
    OUTPUT_VIDEO_PATH,
    PROGRESS_INTERVAL_FRAMES,
    TARGET_LABELS,
    TEXT_BG_COLOR,
    TEXT_COLOR,
    TRACK_MAX_DISTANCE,
    TRACK_MAX_MISSED_FRAMES,
    YOLO_MODEL_NAME,
)
from json_exporter import export_analysis
from route_analyzer import RouteAnalyzer
from vehicle_detector import VehicleDetector
from vehicle_tracker import VehicleTracker


def main():
    if not INPUT_VIDEO_PATH.exists():
        print(f"Input video not found: {INPUT_VIDEO_PATH}", file=sys.stderr)
        return 1

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    capture = cv2.VideoCapture(str(INPUT_VIDEO_PATH))
    if not capture.isOpened():
        print(f"Failed to open input video: {INPUT_VIDEO_PATH}", file=sys.stderr)
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

    writer = create_video_writer(OUTPUT_VIDEO_PATH, fps, width, height)
    if not writer.isOpened():
        print(f"Failed to open output video: {OUTPUT_VIDEO_PATH}", file=sys.stderr)
        capture.release()
        return 1

    detector = VehicleDetector(YOLO_MODEL_NAME, TARGET_LABELS, CONFIDENCE_THRESHOLD)
    tracker = VehicleTracker(TRACK_MAX_DISTANCE, TRACK_MAX_MISSED_FRAMES)
    area_analyzer = AreaAnalyzer(width, height, AREA_ROWS, AREA_COLUMNS)
    route_analyzer = RouteAnalyzer()

    frames = []
    area_count_history = []
    frame_index = 0

    try:
        while True:
            ok, frame = capture.read()
            if not ok:
                break

            detections = detector.detect(frame)
            tracked_detections = tracker.update(detections, frame_index)

            for detection in tracked_detections:
                detection["areaId"] = area_analyzer.get_area_id(detection["center"])

            area_counts = area_analyzer.count_by_area(tracked_detections)
            area_count_history.append(area_counts)
            route_analyzer.update(frame_index, tracked_detections)

            frames.append(
                {
                    "frameIndex": int(frame_index),
                    "timestamp": round(frame_index / fps, 3),
                    "detections": tracked_detections,
                    "areaCounts": area_counts,
                }
            )

            annotated_frame = frame.copy()
            draw_areas(annotated_frame, area_analyzer.areas, area_counts)
            draw_detections(annotated_frame, tracked_detections)
            writer.write(annotated_frame)

            frame_index += 1
            if frame_index % PROGRESS_INTERVAL_FRAMES == 0:
                print(f"Processed {frame_index} frames")
    finally:
        capture.release()
        writer.release()

    vehicles = route_analyzer.build_vehicles()
    areas = area_analyzer.summarize(area_count_history)
    duration = frame_index / fps if fps else 0

    export_analysis(
        output_path=OUTPUT_JSON_PATH,
        video_file=INPUT_VIDEO_RELATIVE,
        fps=fps,
        frame_count=frame_index,
        duration=duration,
        vehicles=vehicles,
        frames=frames,
        areas=areas,
    )

    print(f"Analysis JSON: {OUTPUT_JSON_PATH}")
    print(f"Annotated video: {OUTPUT_VIDEO_PATH}")
    print(f"Processed frames: {frame_index}")
    return 0


def create_video_writer(path, fps, width, height):
    fourcc = cv2.VideoWriter_fourcc(*"mp4v")
    return cv2.VideoWriter(str(path), fourcc, fps, (width, height))


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
