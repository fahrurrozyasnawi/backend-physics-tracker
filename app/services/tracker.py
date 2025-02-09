import os
import cv2
from app.config.base_dir import get_base_dir
from app.models.video import BodyTrackObject
import sieve
from typing import Dict
from collections import OrderedDict
import json
import scipy
import numpy as np

class TrackerService:
    # set task_progreass as global
    task_progress: Dict[str, dict] = OrderedDict()

    def __init__(self, source = None, model='large'):
        self.model = model
        self.source = source

    def init_task(self, task_id):
        self.task_id = task_id
        TrackerService.task_progress[task_id] = {"status": "Initialize", "progress": 0}

        if len(TrackerService.task_progress) > 10:
            for _ in range(8):
                TrackerService.task_progress.popitem(last=False)

        return self
    
    def reset_task_progress(self):
        TrackerService.task_progress: Dict[str, dict] = OrderedDict()
    
    def get_task_progress(self, task_id):
        return TrackerService.task_progress[task_id]
    
    def get_total_frames(self):
        cap = cv2.VideoCapture(self.source)
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        cap.release()

        return total_frames
    
    def __get_frame_val(self, timestep):
        cap = cv2.VideoCapture(self.source)
        fps = cap.get(cv2.CAP_PROP_FPS)

        frame_num = int(fps * timestep)
        cap.release()

        return frame_num
    
    def __convert_to_xyxy_format(self, bbox):
        x = int(bbox.x)
        y = int(bbox.y)
        w = int(bbox.width)
        h = int(bbox.height)

        x2 = x + w
        y2 = y + h
        
        return [x, y, x2, y2]

    # async def predict(self, body: BodyTrackObject):
    #     url = 'https://mango.sievedata.com/v2/push'
    #     headers = {"Content-Type": "application/json", "X-API-Key": os.getenv['API_KEY']}

    #     box = self.__convert_to_xyxy_format(body.bbox)
    #     frame_start = self.__get_frame_val(body.timeStart)
    #     frame_end = self.__get_frame_val(body.timeEnd)

    #     prompt = [{ # Bounding Box Prompt
    #     "frame_index": frame_start, # the index of the frame to apply the prompt to
    #     "object_id": 1, # the id of the object to track
    #     "box": box, # xmin, ymin, xmax, ymax
    #     }]
    #     payload = {
    #         "function": "sieve/sam2",
    #         "inputs": {
    #             "file": self.source,
    #             "model_type": self.model,
    #             "prompts": prompt,
    #             "debug_masks": False,
    #             "multimask_output": False,
    #             "bbox_tracking": True,
    #             "pixel_confidences": False,
    #             "start_frame": frame_start,
    #             "end_frame": frame_end,
    #             "preview": False,
    #         }
    #     }
        
    #     self.boxes_result = []
        
    #     try:
    #         async with httpx.AsyncClient() as client:
    #             self.task_progress[self.task_id] = "Processing"

    #             response = await client.post(url, json=payload, headers=headers)
    #             response.raise_for_status()
    #             self.task_progress[self.task_id] = "Almost Done"

    #             debug_video, outputs = response.json()
    #             self.boxes_result = outputs['bbox_tracking']

    #             self.task_progress[self.task_id] = "Completed"

    #     except Exception as e:
    #         self.task_progress[self.task_id] = "Failed"
    #         raise Exception(e)
    
    def track_object(self, body: BodyTrackObject):
        file = sieve.File(self.source)
        box = self.__convert_to_xyxy_format(body.bbox)
        frame_start = self.__get_frame_val(body.timeStart)
        # frame_end = self.__get_frame_val(body.timeEnd)

        print('box', box)
        prompts = [{ # Bounding Box Prompt
        "frame_index": frame_start, # the index of the frame to apply the prompt to
        "object_id": 1, # the id of the object to track
        "box": box, # xmin, ymin, xmax, ymax
        }]

        # self.task_progress[self.task_id] = "In Progress"
        TrackerService.task_progress[self.task_id] = {"status": "Start Tracking", "progress": 0.2}
        print('running sam2')
        sam2 = sieve.function.get('sieve/sam2')
        outputs = sam2.push(
            file=file,
            model_type=self.model,
            prompts=prompts,
            start_frame=-1,
            end_frame=-1,
            bbox_tracking=True, 
            preview=False, 
            debug_masks=False, 
            pixel_confidences=False
        )

        outputs = outputs.result()
        output_path = outputs['bbox_tracking'].path

        with open(output_path, 'r') as json_file:
            data = json.load(json_file)

        if isinstance(data, list):
            bboxes_list = data
        else:
            bboxes_list = data

        # print('type bboxes', type(bboxes_list))

        self.boxes_result = self.__get_bbox_by_object_id(data=bboxes_list)
        # self.task_progress[self.task_id] = "Almost Done"
        TrackerService.task_progress[self.task_id] = {"status": "Tracking completed", " progress": 0.5}

        timeline = (body.timeStart, body.timeEnd)
        print('running generate video result')
        self.generate_video_result(timeline)

    def __get_center_point(self, bbox):
        x_min, y_min, x_max, y_max = bbox
        cx = int((x_min + x_max) / 2)
        cy = int((y_min + y_max) / 2)
        return (cx, cy)
    
    def __get_bbox_by_object_id(self, data, object_id: int = 1):
        bboxes = []
        for frame_key, frame_objects in data.items():
            for obj in frame_objects:
                if obj["object_id"] == object_id:
                    # data = {"bbox": obj['bbox'], "frame"}
                    bboxes.append(obj)
        return bboxes
    
    def __get_by_frame_index(self, data, frame_index):
        for obj in data:
            if obj['frame_index'] == frame_index:
                return obj
            
        return None
    
    def completed_task_progress(self):
        TrackerService.task_progress[self.task_id] = {"status": "Done", "progress": 1}

    def get_bboxes_result(self):
        if len(self.boxes_result) > 0:
            bboxes = []
            for obj in self.boxes_result:
                bboxes.append(obj['bbox'])
            return bboxes
        else :
            raise Exception("Bboxes is empty")
    
    def get_keypoints_result(self):
        keypoints = []
        for obj in self.boxes_result:
            keypoint = self.__get_center_point(obj['bbox'])
            keypoints.append(keypoint)
        return keypoints
    
    def generate_video_result(self, timeline):
        cap = cv2.VideoCapture(self.source)
        file_name = os.path.join(self.source)
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
        track_frame = 0
        trajectory = []
        boxes = self.get_bboxes_result()

        TrackerService.task_progress[self.task_id] = {"status": "Generating video", "progress": 0.6}
        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                break
            
            if current_frame >= frame_start:
                try:
                    bbox = boxes[track_frame]
                except:
                    bbox = None

                if bbox is not None:
                    keypoint = self.__get_center_point(bbox)
                    trajectory.append(keypoint)
                    cv2.circle(frame, keypoint, 5, (0, 255, 0), 5)
                                    
                track_frame += 1
            
            if len(trajectory) > 5:
                smoothed_trajectory = np.array(trajectory)
                smoothed_trajectory[:, 0] = scipy.ndimage.gaussian_filter1d(smoothed_trajectory[:, 0], sigma=2)
                smoothed_trajectory[:, 1] = scipy.ndimage.gaussian_filter1d(smoothed_trajectory[:, 1], sigma=2)
            
                # Gambar lintasan bola
                for i in range(1, len(smoothed_trajectory)):
                    cv2.line(frame, tuple(smoothed_trajectory[i-1]), tuple(smoothed_trajectory[i]), (0, 255, 0), 5)
                        
            current_frame += 1
            out.write(frame)
            
        cap.release()
        out.release()
        cv2.destroyAllWindows() 

        # self.task_progress[self.task_id] = "Completed"
        print('complete generate')
        TrackerService.task_progress[self.task_id] = {"status": "Calculate formula", "progress": 0.8}
        # return output_result
