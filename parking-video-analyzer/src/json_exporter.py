import json


def export_analysis(
    output_path,
    video_file,
    fps,
    frame_count,
    duration,
    vehicles,
    frames,
    areas,
):
    output_path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "source": "mp4_video",
        "videoFile": video_file,
        "fps": normalize_number(fps),
        "frameCount": int(frame_count),
        "duration": round(float(duration), 3),
        "vehicles": vehicles,
        "frames": frames,
        "areas": areas,
    }

    with output_path.open("w", encoding="utf-8") as file:
        json.dump(payload, file, ensure_ascii=False, indent=2)

    return payload


def normalize_number(value):
    value = float(value)
    if value.is_integer():
        return int(value)
    return round(value, 3)
