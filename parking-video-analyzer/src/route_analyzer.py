class RouteAnalyzer:
    def __init__(self):
        self.vehicles = {}

    def update(self, frame_index, detections):
        for detection in detections:
            vehicle_id = detection["vehicleId"]
            center = detection["center"]

            if vehicle_id not in self.vehicles:
                self.vehicles[vehicle_id] = {
                    "vehicleId": vehicle_id,
                    "label": detection["label"],
                    "firstFrame": frame_index,
                    "lastFrame": frame_index,
                    "route": [],
                }

            vehicle = self.vehicles[vehicle_id]
            vehicle["label"] = detection["label"]
            vehicle["lastFrame"] = frame_index
            vehicle["route"].append(
                {
                    "frameIndex": int(frame_index),
                    "x": int(center["x"]),
                    "y": int(center["y"]),
                    "areaId": detection.get("areaId", "unknown"),
                }
            )

    def build_vehicles(self):
        return sorted(self.vehicles.values(), key=lambda vehicle: self._sort_key(vehicle))

    @staticmethod
    def _sort_key(vehicle):
        vehicle_id = vehicle["vehicleId"]
        try:
            return (0, int(vehicle_id.rsplit("_", 1)[1]))
        except (IndexError, ValueError):
            return (1, vehicle_id)
