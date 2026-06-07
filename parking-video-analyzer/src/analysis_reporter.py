import json
import math
from collections import Counter


def write_tuning_report(output_path, analysis_result, selected_parameters):
    output_path.parent.mkdir(parents=True, exist_ok=True)
    report = build_tuning_report(analysis_result, selected_parameters)

    with output_path.open("w", encoding="utf-8") as file:
        json.dump(report, file, ensure_ascii=False, indent=2)

    return report


def build_tuning_report(analysis_result, selected_parameters):
    frames = analysis_result["frames"]
    vehicles = analysis_result["vehicles"]
    detections = [
        detection
        for frame in frames
        for detection in frame["detections"]
    ]

    widths = [
        detection["bbox"]["x2"] - detection["bbox"]["x1"]
        for detection in detections
    ]
    heights = [
        detection["bbox"]["y2"] - detection["bbox"]["y1"]
        for detection in detections
    ]
    bbox_areas = [
        width * height
        for width, height in zip(widths, heights)
    ]
    confidences = [detection["confidence"] for detection in detections]
    detections_per_frame = [len(frame["detections"]) for frame in frames]
    track_lifetimes = [len(vehicle["route"]) for vehicle in vehicles]
    label_counts = Counter(detection["label"] for detection in detections)
    source_label_counts = Counter(
        detection.get("sourceLabel", detection["label"])
        for detection in detections
    )
    alias_counts = Counter(
        (
            detection.get("sourceLabel", detection["label"]),
            detection["label"],
        )
        for detection in detections
        if detection.get("labelAliasApplied")
    )

    return {
        "sourceJson": "output/analysis_result.json",
        "selectedParameters": selected_parameters,
        "summary": {
            "frameCount": analysis_result["frameCount"],
            "duration": analysis_result["duration"],
            "totalDetections": len(detections),
            "totalVehicles": len(vehicles),
            "areaCount": len(analysis_result["areas"]),
        },
        "confidence": summarize_numbers(confidences),
        "labels": {
            "final": dict(sorted(label_counts.items())),
            "source": dict(sorted(source_label_counts.items())),
            "aliases": [
                {
                    "sourceLabel": source_label,
                    "label": label,
                    "count": count,
                }
                for (source_label, label), count in sorted(alias_counts.items())
            ],
        },
        "bbox": {
            "width": summarize_numbers(widths),
            "height": summarize_numbers(heights),
            "area": summarize_numbers(bbox_areas),
        },
        "detectionsPerFrame": summarize_numbers(detections_per_frame),
        "trackLifetimeFrames": summarize_numbers(track_lifetimes),
        "shortLivedVehicles": {
            "maxFrames5": sum(1 for lifetime in track_lifetimes if lifetime <= 5),
            "maxFrames15": sum(1 for lifetime in track_lifetimes if lifetime <= 15),
        },
        "areas": analysis_result["areas"],
    }


def summarize_numbers(values):
    values = sorted(values)
    if not values:
        return {
            "count": 0,
            "min": None,
            "p5": None,
            "p10": None,
            "p25": None,
            "median": None,
            "p75": None,
            "p90": None,
            "p95": None,
            "max": None,
            "average": None,
        }

    return {
        "count": len(values),
        "min": round(values[0], 4),
        "p5": round(percentile(values, 5), 4),
        "p10": round(percentile(values, 10), 4),
        "p25": round(percentile(values, 25), 4),
        "median": round(percentile(values, 50), 4),
        "p75": round(percentile(values, 75), 4),
        "p90": round(percentile(values, 90), 4),
        "p95": round(percentile(values, 95), 4),
        "max": round(values[-1], 4),
        "average": round(sum(values) / len(values), 4),
    }


def percentile(values, percent):
    if len(values) == 1:
        return values[0]

    index = (len(values) - 1) * percent / 100
    lower_index = math.floor(index)
    upper_index = math.ceil(index)

    if lower_index == upper_index:
        return values[lower_index]

    lower_weight = upper_index - index
    upper_weight = index - lower_index
    return values[lower_index] * lower_weight + values[upper_index] * upper_weight
