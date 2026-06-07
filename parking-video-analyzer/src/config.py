from copy import deepcopy
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[1]

INPUT_VIDEO_RELATIVE = "input/parking_sample.mp4"
INPUT_VIDEO_PATH = BASE_DIR / INPUT_VIDEO_RELATIVE

OUTPUT_DIR = BASE_DIR / "output"
OUTPUT_JSON_PATH = OUTPUT_DIR / "analysis_result.json"
OUTPUT_VIDEO_PATH = OUTPUT_DIR / "annotated_video.mp4"
OUTPUT_TUNING_REPORT_PATH = OUTPUT_DIR / "tuning_report.json"
OUTPUT_PERFORMANCE_REPORT_PATH = OUTPUT_DIR / "performance_report.json"

DATASET_DIR = BASE_DIR / "dataset"
DATA_YAML_PATH = DATASET_DIR / "data.yaml"
TRAINED_MODEL_PATH = BASE_DIR / "models" / "parking_yolov8s" / "weights" / "best.pt"

DEFAULT_FPS = 30.0
DEFAULT_PROFILE_NAME = "default"

BASE_PROFILE = {
    "name": DEFAULT_PROFILE_NAME,
    "description": "High-recall batch analysis profile for the current sample video.",
    "input_video_relative": INPUT_VIDEO_RELATIVE,
    "output_json_path": OUTPUT_JSON_PATH,
    "output_video_path": OUTPUT_VIDEO_PATH,
    "output_tuning_report_path": OUTPUT_TUNING_REPORT_PATH,
    "output_performance_report_path": OUTPUT_PERFORMANCE_REPORT_PATH,
    "yolo_model_name": "yolov8n.pt",
    "target_labels": {"car", "truck", "bus", "cell phone", "bottle"},
    "label_aliases": {
        "cell phone": "car",
        "bottle": "car",
    },
    "confidence_threshold": 0.20,
    "yolo_image_size": 1280,
    "bbox_filter": {
        "min_width": 15,
        "max_width": 100,
        "min_height": 20,
        "max_height": 180,
        "min_area": 550,
        "max_area": 9000,
        "min_aspect_ratio": 0.15,
        "max_aspect_ratio": 3.5,
    },
    "enable_full_frame_detection": True,
    "enable_tiled_detection": True,
    "tile_rows": 2,
    "tile_columns": 3,
    "tile_overlap_pixels": 80,
    "nms_iou_threshold": 0.45,
    "area_rows": 2,
    "area_columns": 3,
    "track_max_distance": 55.0,
    "track_max_missed_frames": 30,
    "progress_interval_frames": 100,
}

PROFILE_OVERRIDES = {
    "default": {},
    "realtime": {
        "description": "Temporary high-coverage profile for the current parking video.",
        "confidence_threshold": 0.10,
        "yolo_image_size": 1280,
        "enable_tiled_detection": True,
        "tile_rows": 2,
        "tile_columns": 3,
        "tile_overlap_pixels": 80,
        "track_max_distance": 55.0,
        "track_max_missed_frames": 45,
        "progress_interval_frames": 30,
    },
    "trained": {
        "description": "Profile for a fine-tuned parking-lot YOLOv8s model.",
        "yolo_model_name": str(TRAINED_MODEL_PATH),
        "target_labels": {"car", "truck", "bus"},
        "label_aliases": {},
        "confidence_threshold": 0.25,
        "yolo_image_size": 960,
        "enable_tiled_detection": False,
        "tile_rows": 1,
        "tile_columns": 1,
        "tile_overlap_pixels": 0,
        "track_max_distance": 50.0,
        "track_max_missed_frames": 20,
    },
}


def available_profiles():
    return tuple(PROFILE_OVERRIDES.keys())


def load_profile(name=DEFAULT_PROFILE_NAME, model_override=None, disable_label_aliases=False):
    if name not in PROFILE_OVERRIDES:
        valid_names = ", ".join(available_profiles())
        raise ValueError(f"Unknown profile: {name}. Expected one of: {valid_names}")

    profile = deepcopy(BASE_PROFILE)
    profile.update(deepcopy(PROFILE_OVERRIDES[name]))
    profile["name"] = name

    if model_override:
        profile["yolo_model_name"] = model_override
    if disable_label_aliases:
        profile["label_aliases"] = {}
        profile["target_labels"] = {
            label
            for label in profile["target_labels"]
            if label not in BASE_PROFILE["label_aliases"]
        }

    profile["input_video_path"] = BASE_DIR / profile["input_video_relative"]
    return profile


def selected_parameters(profile):
    return {
        "profile": {
            "name": profile["name"],
            "description": profile["description"],
        },
        "model": profile["yolo_model_name"],
        "targetLabels": sorted(profile["target_labels"]),
        "labelAliases": dict(sorted(profile["label_aliases"].items())),
        "confidenceThreshold": profile["confidence_threshold"],
        "yoloImageSize": profile["yolo_image_size"],
        "bboxFilter": {
            "minWidth": profile["bbox_filter"]["min_width"],
            "maxWidth": profile["bbox_filter"]["max_width"],
            "minHeight": profile["bbox_filter"]["min_height"],
            "maxHeight": profile["bbox_filter"]["max_height"],
            "minArea": profile["bbox_filter"]["min_area"],
            "maxArea": profile["bbox_filter"]["max_area"],
            "minAspectRatio": profile["bbox_filter"]["min_aspect_ratio"],
            "maxAspectRatio": profile["bbox_filter"]["max_aspect_ratio"],
        },
        "tiling": {
            "enabled": profile["enable_tiled_detection"],
            "rows": profile["tile_rows"],
            "columns": profile["tile_columns"],
            "overlapPixels": profile["tile_overlap_pixels"],
        },
        "nmsIouThreshold": profile["nms_iou_threshold"],
        "tracking": {
            "maxDistance": profile["track_max_distance"],
            "maxMissedFrames": profile["track_max_missed_frames"],
        },
    }

BOX_COLOR = (0, 255, 0)
TEXT_COLOR = (255, 255, 255)
TEXT_BG_COLOR = (0, 0, 0)
AREA_LINE_COLOR = (255, 180, 0)
AREA_TEXT_COLOR = (255, 255, 0)

# Backward-compatible constants for small external scripts or notebooks.
YOLO_MODEL_NAME = BASE_PROFILE["yolo_model_name"]
TARGET_LABELS = BASE_PROFILE["target_labels"]
LABEL_ALIASES = BASE_PROFILE["label_aliases"]
CONFIDENCE_THRESHOLD = BASE_PROFILE["confidence_threshold"]
YOLO_IMAGE_SIZE = BASE_PROFILE["yolo_image_size"]
BBOX_MIN_WIDTH = BASE_PROFILE["bbox_filter"]["min_width"]
BBOX_MAX_WIDTH = BASE_PROFILE["bbox_filter"]["max_width"]
BBOX_MIN_HEIGHT = BASE_PROFILE["bbox_filter"]["min_height"]
BBOX_MAX_HEIGHT = BASE_PROFILE["bbox_filter"]["max_height"]
BBOX_MIN_AREA = BASE_PROFILE["bbox_filter"]["min_area"]
BBOX_MAX_AREA = BASE_PROFILE["bbox_filter"]["max_area"]
BBOX_MIN_ASPECT_RATIO = BASE_PROFILE["bbox_filter"]["min_aspect_ratio"]
BBOX_MAX_ASPECT_RATIO = BASE_PROFILE["bbox_filter"]["max_aspect_ratio"]
ENABLE_FULL_FRAME_DETECTION = BASE_PROFILE["enable_full_frame_detection"]
ENABLE_TILED_DETECTION = BASE_PROFILE["enable_tiled_detection"]
TILE_ROWS = BASE_PROFILE["tile_rows"]
TILE_COLUMNS = BASE_PROFILE["tile_columns"]
TILE_OVERLAP_PIXELS = BASE_PROFILE["tile_overlap_pixels"]
NMS_IOU_THRESHOLD = BASE_PROFILE["nms_iou_threshold"]
AREA_ROWS = BASE_PROFILE["area_rows"]
AREA_COLUMNS = BASE_PROFILE["area_columns"]
TRACK_MAX_DISTANCE = BASE_PROFILE["track_max_distance"]
TRACK_MAX_MISSED_FRAMES = BASE_PROFILE["track_max_missed_frames"]
PROGRESS_INTERVAL_FRAMES = BASE_PROFILE["progress_interval_frames"]
