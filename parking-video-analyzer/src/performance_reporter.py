import json


def write_performance_report(
    output_path,
    analysis_result,
    selected_parameters,
    frame_timings,
    total_wall_seconds,
):
    output_path.parent.mkdir(parents=True, exist_ok=True)
    report = build_performance_report(
        analysis_result,
        selected_parameters,
        frame_timings,
        total_wall_seconds,
    )

    with output_path.open("w", encoding="utf-8") as file:
        json.dump(report, file, ensure_ascii=False, indent=2)

    return report


def build_performance_report(
    analysis_result,
    selected_parameters,
    frame_timings,
    total_wall_seconds,
):
    frame_count = analysis_result["frameCount"]
    video_duration = analysis_result["duration"]

    return {
        "sourceJson": "output/analysis_result.json",
        "selectedParameters": selected_parameters,
        "summary": {
            "frameCount": frame_count,
            "videoDurationSeconds": video_duration,
            "wallSeconds": round(total_wall_seconds, 4),
            "processingFps": round(frame_count / total_wall_seconds, 4)
            if total_wall_seconds > 0
            else None,
            "realtimeFactor": round(video_duration / total_wall_seconds, 4)
            if total_wall_seconds > 0
            else None,
        },
        "timingsSeconds": {
            "perFrameTotal": summarize_numbers(
                [timing["frame_total_seconds"] for timing in frame_timings]
            ),
            "detection": summarize_numbers(
                [timing["detection_seconds"] for timing in frame_timings]
            ),
            "tracking": summarize_numbers(
                [timing["tracking_seconds"] for timing in frame_timings]
            ),
            "areaAndRoute": summarize_numbers(
                [timing["area_route_seconds"] for timing in frame_timings]
            ),
            "drawingAndWriting": summarize_numbers(
                [timing["draw_write_seconds"] for timing in frame_timings]
            ),
        },
        "frames": frame_timings,
    }


def summarize_numbers(values):
    values = sorted(values)
    if not values:
        return {
            "count": 0,
            "min": None,
            "average": None,
            "max": None,
        }

    return {
        "count": len(values),
        "min": round(values[0], 6),
        "average": round(sum(values) / len(values), 6),
        "max": round(values[-1], 6),
    }
