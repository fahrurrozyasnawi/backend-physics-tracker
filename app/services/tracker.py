import os
import cv2
from ultralytics.models.sam import SAM2VideoPredictor
from ultralytics import SAM
from config.base_dir import get_base_dir

class TrackerService:
    def __init__(self, source, imgsz=640, conf=0.25, model='sam2_t.pt'):
        self.model = model
        self.source = source

        model_path = os.path.join(get_base_dir(),'app', 'models', 'ml', model)
        overrides = dict(conf=conf, task="segment", mode="predict", imgsz=imgsz, model=model_path)
        self.predictor = SAM2VideoPredictor(overrides=overrides)

        mobile_sam = os.path.join(get_base_dir(),'app', 'models', 'ml', 'mobile_sam.pt')
        self.mobile_sam = SAM(mobile_sam)

    def predict(self, bbox, task_progress):
        cap = cv2.VideoCapture(self.source)
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        cap.release()

        results = self.predictor(source=self.source, bboxes=bbox, labels=1, stream=True)
        # results = self.mobile_sam.predict(self.source, bboxes=[bbox], labels=1, stream=True)
        print('success', results)

        self.boxes_result = []
        self.keypoints = []

        for result in results:
            print('result', result)
            self.boxes_result.append(result.boxes)
            self.keypoints.append(result.keypoints)
            task_progress = (task_progress/total_frames)
        
        print("Predictor finished")
        return (self.boxes_result, self.keypoints)
    
    def get_bboxes_result(self):
        return self.boxes_result
    
    def get_keypoints_result(self):
        return self.keypoints
    
    def generate_video_result(self, path_video_ori, timeline):
        cap = cv2.VideoCapture(path_video_ori)
        file_name = os.path.join(path_video_ori)
        file_path = os.path.dirname(file_name)

        filename, ext = os.path.splitext(file_name)

        time_start, time_end = timeline
        fps = cap.get(cv2.CAP_PROP_FPS)
        frame_start = int(fps * time_start)
        frame_end = int(fps * time_end)
        frame_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        frame_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

        fourcc = cv2.VideoWriter_fourcc(*"mp4v")
        output_result_name = f'{filename}-result{ext}'
        output_result = os.path.join(file_path, output_result_name)

        out = cv2.VideoWriter(output_result, fourcc, fps, (frame_width, frame_height))

        current_frame = 0
        current_keypoint = 0
        prev_keypoint = None

        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                break
            
            if(frame_start <= current_frame < frame_end):
                keypoint = self.keypoints[current_keypoint]
                if(prev_keypoint is not None):
                    cv2.line(frame, prev_keypoint, keypoint, (0, 255, 0), 2)
                prev_keypoint = keypoint
                current_keypoint += 1
            
            current_frame += 1

            out.write(frame)

        cap.release()
        out.release()
        cv2.destroyAllWindows()

        return output_result
