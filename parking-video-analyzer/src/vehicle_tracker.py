from math import hypot


class VehicleTracker:
    def __init__(self, max_distance, max_missed_frames):
        self.max_distance = max_distance
        self.max_missed_frames = max_missed_frames
        self.next_vehicle_number = 1
        self.tracks = {}

    def update(self, detections, frame_index):
        old_track_ids = set(self.tracks.keys())
        assignments = self._match_detections(detections)
        assigned_track_ids = set()
        assigned_detection_indices = set()

        tracked_detections = [dict(detection) for detection in detections]

        for track_id, detection_index in assignments:
            detection = tracked_detections[detection_index]
            detection["vehicleId"] = track_id
            self._update_track(track_id, detection, frame_index)
            assigned_track_ids.add(track_id)
            assigned_detection_indices.add(detection_index)

        for detection_index, detection in enumerate(tracked_detections):
            if detection_index in assigned_detection_indices:
                continue
            track_id = self._new_vehicle_id()
            detection["vehicleId"] = track_id
            self._create_track(track_id, detection, frame_index)
            assigned_track_ids.add(track_id)

        for track_id in old_track_ids - assigned_track_ids:
            self.tracks[track_id]["missedFrames"] += 1

        self._remove_stale_tracks()
        return tracked_detections

    def _match_detections(self, detections):
        candidates = []
        for track_id, track in self.tracks.items():
            for detection_index, detection in enumerate(detections):
                distance = self._distance(track["center"], detection["center"])
                if distance <= self.max_distance:
                    candidates.append((distance, track_id, detection_index))

        candidates.sort(key=lambda item: item[0])

        assignments = []
        used_tracks = set()
        used_detections = set()
        for _, track_id, detection_index in candidates:
            if track_id in used_tracks or detection_index in used_detections:
                continue
            assignments.append((track_id, detection_index))
            used_tracks.add(track_id)
            used_detections.add(detection_index)

        return assignments

    def _create_track(self, track_id, detection, frame_index):
        self.tracks[track_id] = {
            "vehicleId": track_id,
            "label": detection["label"],
            "center": detection["center"],
            "bbox": detection["bbox"],
            "missedFrames": 0,
            "lastFrame": frame_index,
        }

    def _update_track(self, track_id, detection, frame_index):
        self.tracks[track_id].update(
            {
                "label": detection["label"],
                "center": detection["center"],
                "bbox": detection["bbox"],
                "missedFrames": 0,
                "lastFrame": frame_index,
            }
        )

    def _remove_stale_tracks(self):
        stale_track_ids = [
            track_id
            for track_id, track in self.tracks.items()
            if track["missedFrames"] > self.max_missed_frames
        ]
        for track_id in stale_track_ids:
            del self.tracks[track_id]

    def _new_vehicle_id(self):
        vehicle_id = f"vehicle_{self.next_vehicle_number}"
        self.next_vehicle_number += 1
        return vehicle_id

    @staticmethod
    def _distance(center_a, center_b):
        return hypot(center_a["x"] - center_b["x"], center_a["y"] - center_b["y"])
