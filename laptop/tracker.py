from ultralytics import YOLO  # noqa: I001

class Person:
    def __init__(self, id, keypoints, box):
        self.id = id
        self.keypoints = keypoints
        self.box = box

class Tracker:
    def __init__(self, model_path="yolov8n-pose.pt"):
        self.model = YOLO(model_path) #filename for model

    def track(self, frame):
        people = []
        tracked_frame = self.model.track(frame, persist=True)
        result = next(iter(tracked_frame)).cpu().numpy()

        if result.boxes is None:
            return []

        if result.boxes.id is None:
            return []

        if result.keypoints is None:
            return []

        ids = result.boxes.id
        kps = result.keypoints.xy
        boxes = result.boxes.xyxy

        for person_id, box, keypoints in zip(ids, boxes, kps):
            people.append(Person(person_id, keypoints, box))

        return people

