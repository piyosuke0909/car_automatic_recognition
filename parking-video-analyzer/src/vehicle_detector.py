class VehicleDetector:
    def __init__(self, model_name, target_labels, confidence_threshold):
        try:
            from ultralytics import YOLO
        except ImportError as exc:
            raise RuntimeError(
                "Ultralytics is not installed. Run: pip install -r requirements.txt"
            ) from exc

        self.model = YOLO(model_name)
        self.target_labels = set(target_labels)
        self.confidence_threshold = confidence_threshold

    def detect(self, frame):
        results = self.model.predict(
            frame,
            conf=self.confidence_threshold,
            verbose=False,
        )

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

            x1, y1, x2, y2 = boxes.xyxy[index].tolist()
            bbox = {
                "x1": int(round(x1)),
                "y1": int(round(y1)),
                "x2": int(round(x2)),
                "y2": int(round(y2)),
            }
            center = {
                "x": int(round((x1 + x2) / 2.0)),
                "y": int(round((y1 + y2) / 2.0)),
            }

            detections.append(
                {
                    "label": label,
                    "confidence": round(confidence, 4),
                    "bbox": bbox,
                    "center": center,
                }
            )

        return detections

    def _label_for_class(self, class_id):
        names = self.model.names
        if isinstance(names, dict):
            return names.get(class_id, str(class_id))
        return names[class_id]
