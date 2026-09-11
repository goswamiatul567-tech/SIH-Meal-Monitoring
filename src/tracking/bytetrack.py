import numpy as np


class ByteTrack:

    def __init__(self, iou_threshold=0.3, max_lost=30):
        self.next_id = 1
        self.tracks = {}
        self.iou_threshold = iou_threshold
        self.max_lost = max_lost

    def calculate_iou(self, box1, box2):
        x1 = max(box1[0], box2[0])
        y1 = max(box1[1], box2[1])

        x2 = min(box1[2], box2[2])
        y2 = min(box1[3], box2[3])

        intersection_width = max(0, x2 - x1)
        intersection_height = max(0, y2 - y1)

        intersection = intersection_width * intersection_height

        area1 = max(0, box1[2] - box1[0]) * max(0, box1[3] - box1[1])
        area2 = max(0, box2[2] - box2[0]) * max(0, box2[3] - box2[1])

        union = area1 + area2 - intersection

        if union == 0:
            return 0.0

        return intersection / union

    def update(self, detections):
        """
        detections:
        [[x1, y1, x2, y2], ...]

        Returns:
        [
            {
                "id": track_id,
                "box": [x1, y1, x2, y2]
            }
        ]
        """

        detections = [list(map(int, box)) for box in detections]

        results = []
        matched_tracks = set()
        matched_detections = set()

        # Match new detections with existing tracks
        for track_id, track_data in list(self.tracks.items()):

            best_iou = 0.0
            best_detection = -1

            for i, detection in enumerate(detections):

                if i in matched_detections:
                    continue

                iou = self.calculate_iou(
                    track_data["box"],
                    detection
                )

                if iou > best_iou:
                    best_iou = iou
                    best_detection = i

            if best_iou >= self.iou_threshold:
                self.tracks[track_id]["box"] = detections[best_detection]
                self.tracks[track_id]["lost"] = 0

                matched_tracks.add(track_id)
                matched_detections.add(best_detection)

                results.append({
                    "id": track_id,
                    "box": detections[best_detection]
                })

            else:
                self.tracks[track_id]["lost"] += 1

        # Create new tracks for unmatched detections
        for i, detection in enumerate(detections):

            if i in matched_detections:
                continue

            track_id = self.next_id
            self.next_id += 1

            self.tracks[track_id] = {
                "box": detection,
                "lost": 0
            }

            results.append({
                "id": track_id,
                "box": detection
            })

        # Remove tracks that have been lost too long
        for track_id in list(self.tracks.keys()):

            if self.tracks[track_id]["lost"] > self.max_lost:
                del self.tracks[track_id]

        return results