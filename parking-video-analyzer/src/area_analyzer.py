class AreaAnalyzer:
    def __init__(self, frame_width, frame_height, rows, columns):
        self.frame_width = frame_width
        self.frame_height = frame_height
        self.rows = rows
        self.columns = columns
        self.areas = self._build_areas()

    def get_area_id(self, center):
        x = center["x"]
        y = center["y"]

        for area in self.areas:
            bounds = area["bounds"]
            if (
                bounds["x1"] <= x < bounds["x2"]
                and bounds["y1"] <= y < bounds["y2"]
            ):
                return area["areaId"]

        if x == self.frame_width:
            return self.get_area_id({"x": x - 1, "y": y})
        if y == self.frame_height:
            return self.get_area_id({"x": x, "y": y - 1})
        return "unknown"

    def count_by_area(self, detections):
        counts = self.empty_counts()
        for detection in detections:
            area_id = detection.get("areaId", "unknown")
            if area_id not in counts:
                counts[area_id] = 0
            counts[area_id] += 1
        return counts

    def empty_counts(self):
        return {area["areaId"]: 0 for area in self.areas}

    def summarize(self, area_count_history):
        summaries = []
        total_frames = len(area_count_history)

        for area in self.areas:
            area_id = area["areaId"]
            counts = [frame_counts.get(area_id, 0) for frame_counts in area_count_history]
            max_car_count = max(counts) if counts else 0
            average_car_count = sum(counts) / total_frames if total_frames else 0.0
            congestion_score = average_car_count * 10 + max_car_count * 5

            summaries.append(
                {
                    "areaId": area_id,
                    "name": area["name"],
                    "bounds": area["bounds"],
                    "averageCarCount": round(average_car_count, 3),
                    "maxCarCount": int(max_car_count),
                    "congestionScore": round(congestion_score, 3),
                    "heatLevel": self.heat_level(congestion_score),
                }
            )

        return summaries

    @staticmethod
    def heat_level(congestion_score):
        if congestion_score <= 30:
            return "low"
        if congestion_score <= 60:
            return "medium"
        return "high"

    def _build_areas(self):
        areas = []
        area_number = 1

        for row in range(self.rows):
            y1 = round(row * self.frame_height / self.rows)
            y2 = round((row + 1) * self.frame_height / self.rows)
            if row == self.rows - 1:
                y2 = self.frame_height

            for column in range(self.columns):
                x1 = round(column * self.frame_width / self.columns)
                x2 = round((column + 1) * self.frame_width / self.columns)
                if column == self.columns - 1:
                    x2 = self.frame_width

                area_id = f"area_{area_number}"
                areas.append(
                    {
                        "areaId": area_id,
                        "name": f"Area {area_number}",
                        "bounds": {
                            "x1": int(x1),
                            "y1": int(y1),
                            "x2": int(x2),
                            "y2": int(y2),
                        },
                    }
                )
                area_number += 1

        return areas
