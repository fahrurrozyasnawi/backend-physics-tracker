import os
import cv2
import base64
import numpy as np


class VideoServices:
    def __init__(self, video_path):
        self.video_path = video_path

    def extract_frame_at_time(self, timecode):
        cap = cv2.VideoCapture(self.video_path)
        fps = cap.get(cv2.CAP_PROP_FPS)  # Get frames per second
        # Calculate the frame number at the given timecode
        frame_number = int(fps * timecode)

        # Set the position of the video to the desired frame
        cap.set(cv2.CAP_PROP_POS_FRAMES, frame_number)
        ret, frame = cap.read()
        ret, buffer = cv2.imencode('.jpg', frame)
        base64_image = base64.b64encode(buffer).decode('utf-8')

        cap.release()

        if ret:
            return base64_image
        else:
            print(f"Failed to extract frame at {timecode} seconds")
            return None

    def generate_video_by_timeline(self, timeStart, timeEnd):
        cap = cv2.VideoCapture(self.video_path)
        file_name = os.path.basename(self.video_path)
        file_path = os.path.dirname(self.video_path)
        filename, ext = os.path.splitext(file_name)
        
        fps = cap.get(cv2.CAP_PROP_FPS)
        frame_start = int(fps * timeStart)
        frame_end = int(fps * timeEnd)
        frame_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        frame_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

        fourcc = cv2.VideoWriter_fourcc(*'mp4v')  # Codec for .mp4
        output_video_filename = f'{filename}-generated{ext}'
        output_video_path = os.path.join(file_path, output_video_filename)
        
        out = cv2.VideoWriter(output_video_path, fourcc, fps, (frame_width, frame_height))

        current_frame = 0
        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                break
            
            if frame_start <= current_frame < frame_end:
                out.write(frame)  # Write the frame to the output video

            current_frame += 1
            if current_frame >= frame_end:
                break

        cap.release()
        out.release()
        cv2.destroyAllWindows()

        return output_video_path
    
    def convert_bbox_obj_to_xyxy(self, bbox):
        x,y,w,h = bbox
        # x = bbox['x']
        # y = bbox['y']
        # w = bbox['width']
        # h = bbox['height']

        x2 = x + w
        y2 = y + h
        
        return [x, y, x2, y2]
    
    def convert_bbox_to_xyxy(self, bbox):
        x, y, w, h = bbox
        x2 = x + w
        y2 = y + h
        
        return [x, y, x2, y2]

    def get_center_from_bbox(self, bbox):
        x, y, w, h = bbox
        center_x = x + w / 2
        center_y = y + h / 2

        return (center_x, center_y)
    
    def get_center_from_bbox_xyxy(self, bbox):
        x1, y1, x2, y2 = bbox
        center_x = (x1 + x2) /2
        center_y = (y1 + y2) /2

        return (center_x, center_y)
    
    def get_real_distances(self, point_A, point_B):
        scale = 0.01
        distances = np.linalg.norm(np.array(point_A) - np.array(point_B))

        return distances * scale
    
    def get_fps(self):
        cap = cv2.VideoCapture(self.video_path)
        fps = cap.get(cv2.CAP_PROP_FPS)
        return fps

    def init_output_file(self, output_file):
        self.output_file = output_file
        return self
    
