class VehicleDetector:
    def __init__(
        self,
        model_name,
        target_labels,
        confidence_threshold,
        label_aliases=None,
        image_size=None,
        bbox_filter=None,
        enable_full_frame_detection=True,
        enable_tiled_detection=False,
        tile_rows=1,
        tile_columns=1,
        tile_overlap_pixels=0,
        nms_iou_threshold=0.45,
    ):
        try:
            from ultralytics import YOLO
        except ImportError as exc:
            raise RuntimeError(
                "Ultralytics is not installed. Run: pip install -r requirements.txt"
            ) from exc

        self.model = YOLO(model_name)
        self.target_labels = set(target_labels)
        self.confidence_threshold = confidence_threshold
        self.label_aliases = label_aliases or {}
        self.image_size = image_size
        self.bbox_filter = bbox_filter or {}
        self.enable_full_frame_detection = enable_full_frame_detection
        self.enable_tiled_detection = enable_tiled_detection
        self.tile_rows = tile_rows
        self.tile_columns = tile_columns
        self.tile_overlap_pixels = tile_overlap_pixels
        self.nms_iou_threshold = nms_iou_threshold

    def detect(self, frame):
        detections = []
        if self.enable_full_frame_detection:
            detections.extend(self._detect_image(frame, 0, 0))

        if self.enable_tiled_detection:
            for tile, offset_x, offset_y in self._iter_tiles(frame):
                detections.extend(self._detect_image(tile, offset_x, offset_y))

        return self._nms(detections)

    def _detect_image(self, image, offset_x, offset_y):
        predict_options = {
            "source": image,
            "conf": self.confidence_threshold,
            "verbose": False,
        }
        if self.image_size:
            predict_options["imgsz"] = self.image_size

        results = self.model.predict(**predict_options)

        if not results:
            return []

        result = results[0]
        if result.boxes is None:
            return []

        detections = []
        boxes = result.boxes

        for index in range(len(boxes)):
            class_id = int(boxes.cls[index].item())
            label = self._label_for_class(class_id)
            if label not in self.target_labels:
                continue

            confidence = float(boxes.conf[index].item())
            if confidence < self.confidence_threshold:
                continue
            output_label = self.label_aliases.get(label, label)

            x1, y1, x2, y2 = boxes.xyxy[index].tolist()
            bbox = {
                "x1": int(round(x1 + offset_x)),
                "y1": int(round(y1 + offset_y)),
                "x2": int(round(x2 + offset_x)),
                "y2": int(round(y2 + offset_y)),
            }
            if not self._passes_bbox_filter(bbox):
                continue

            center = {
                "x": int(round((bbox["x1"] + bbox["x2"]) / 2.0)),
                "y": int(round((bbox["y1"] + bbox["y2"]) / 2.0)),
            }

            detections.append(
                {
                    "label": output_label,
                    "sourceLabel": label,
                    "labelAliasApplied": output_label != label,
                    "confidence": round(confidence, 4),
                    "bbox": bbox,
                    "center": center,
                }
            )

        return detections

    def _iter_tiles(self, frame):
        height, width = frame.shape[:2]

        for row in range(self.tile_rows):
            base_y1 = round(row * height / self.tile_rows)
            base_y2 = round((row + 1) * height / self.tile_rows)
            y1 = max(0, base_y1 - self.tile_overlap_pixels)
            y2 = min(height, base_y2 + self.tile_overlap_pixels)

            for column in range(self.tile_columns):
                base_x1 = round(column * width / self.tile_columns)
                base_x2 = round((column + 1) * width / self.tile_columns)
                x1 = max(0, base_x1 - self.tile_overlap_pixels)
                x2 = min(width, base_x2 + self.tile_overlap_pixels)
                yield frame[y1:y2, x1:x2], x1, y1

    def _passes_bbox_filter(self, bbox):
        width = bbox["x2"] - bbox["x1"]
        height = bbox["y2"] - bbox["y1"]
        if width <= 0 or height <= 0:
            return False

        area = width * height
        aspect_ratio = width / height

        return (
            width >= self.bbox_filter.get("min_width", 0)
            and width <= self.bbox_filter.get("max_width", float("inf"))
            and height >= self.bbox_filter.get("min_height", 0)
            and height <= self.bbox_filter.get("max_height", float("inf"))
            and area >= self.bbox_filter.get("min_area", 0)
            and area <= self.bbox_filter.get("max_area", float("inf"))
            and aspect_ratio >= self.bbox_filter.get("min_aspect_ratio", 0)
            and aspect_ratio <= self.bbox_filter.get("max_aspect_ratio", float("inf"))
        )

    def _nms(self, detections):
        detections = sorted(
            detections,
            key=lambda detection: detection["confidence"],
            reverse=True,
        )
        kept = []

        for detection in detections:
            if any(
                self._iou(detection["bbox"], kept_detection["bbox"])
                > self.nms_iou_threshold
                for kept_detection in kept
            ):
                continue
            kept.append(detection)

        return kept

    @staticmethod
    def _iou(bbox_a, bbox_b):
        x1 = max(bbox_a["x1"], bbox_b["x1"])
        y1 = max(bbox_a["y1"], bbox_b["y1"])
        x2 = min(bbox_a["x2"], bbox_b["x2"])
        y2 = min(bbox_a["y2"], bbox_b["y2"])

        intersection_width = max(0, x2 - x1)
        intersection_height = max(0, y2 - y1)
        intersection_area = intersection_width * intersection_height
        if intersection_area == 0:
            return 0.0

        area_a = (bbox_a["x2"] - bbox_a["x1"]) * (bbox_a["y2"] - bbox_a["y1"])
        area_b = (bbox_b["x2"] - bbox_b["x1"]) * (bbox_b["y2"] - bbox_b["y1"])
        return intersection_area / (area_a + area_b - intersection_area)

    def _label_for_class(self, class_id):
        names = self.model.names
        if isinstance(names, dict):
            return names.get(class_id, str(class_id))
        return names[class_id]
