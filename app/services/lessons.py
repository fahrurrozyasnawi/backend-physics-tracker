from .models.lessons import ViscosityBodyReq, PendulumBodyReq, ProjectileMotionBodyReq
from scipy.signal import find_peaks
import numpy as np
import math

class LessonsService:
    def __init__(self):
        self.scale_factor = 0.01

    def euclidean_distance(self, pointA, pointB):
        self.pointA = pointA
        self.pointB = pointB

        return math.sqrt((pointB[0] - pointA[0]) ** 2 + (pointB[1] - pointA[1]) ** 2)
    
    def real_distance(self, pixel_distance):
        return pixel_distance * self.scale_factor

class PendulumService(LessonsService):
    def __init__(self, body: PendulumBodyReq):
        self.time = body.time
        self.freq = body.freq
        if(body.mass is not None):
            self.mass = body.mass

    def calculate_formula(self, freq: float = None, period: float = None, amplitude: float = None):
        if(period is not None):
            y = amplitude * math.sin(2 * math.pi / period * self.time)
            return y
        if(freq is not None):
            y = amplitude * math.sin(2 * math.pi * freq * self.time)
            return y       

    def calculate_freq_and_period(self, positions):
         np_positions = np.array(positions)

         peaks, _ = find_peaks(np_positions)
         periods = np.diff(peaks)
         mean_perioods = np.mean(periods)

         freq = 1/mean_perioods

         return (mean_perioods, freq)
    
    def calculate_amplitude(self, positions):
        np_positions = np.array(positions)
        x_eq = np.mean(np_positions)
        amplitude = np.max(np_positions) - x_eq

        return amplitude

class ProjectileMotionService:
    def __init__(self, body: ProjectileMotionBodyReq):
        self.x_val = body.xVal
        self.y_val = body.yVal


    def calculate_elevation(self, bboxes, height):
        centers = []
        for bbox in bboxes:
            xmin, ymin, xmax, ymax = bbox
            x = (xmin + xmax) / 2
            y = (ymin + ymax) / 2
            y = height - y

            centers.append((x,y))
        
        x1,y1 = centers[0]
        x2,y2 = centers[len(centers) - 1]

        dx = x2 - x1
        dy = y2 - y1

        angle_rad = math.atan2(dy, dx)
        angle_deg = math.degrees(angle_rad)

        return angle_deg
    
    def get_elevation_from_init_velocity(self):
        theta = math.atan2(self.Vy, self.Vx)
        theta_deg = math.degrees(theta)

        return theta_deg
    
    def calculate_init_velocity(self, bboxes, frame_rate):
        x1, y1 = bboxes[0]
        x2, y2 = bboxes[1]

        delta_t = 1 / frame_rate

        self.Vx = (x2-x1) / delta_t
        self.Vy = (y2-y1) / delta_t

        Vo = math.sqrt(self.Vx**2 + self.Vy**2)

        return Vo

    def calculate_by_x(self, vo, theta, time):
        # Vx = vo * math.cos(theta) * time
        Vx = vo * math.cos(theta)
        return Vx

    def calculate_by_y(self, vo, theta, time):
        g = 9.8
        # Vy = vo * math.sin(theta) * time - (g * time**2) / 2
        Vy = vo * math.sin(theta) * time - g * time

        return Vy

class ViscosityService(LessonsService):
    def __init__(self, body: ViscosityBodyReq):
        self.radius = body.radius
        self.density_t = body.densityT
        self.density_f = body.densityF

    def calculate_formula(self, velocity):
        result = (2 * math.pow(self.radius, 2) * 9.8 * (self.density_t - self.density_f)) / (9 * velocity)

        return result 

    def calculate_velocity(self, keypoints, time):
        keypoint_A, keypoint_B = keypoints

        euc_dist = super().euclidean_distance(keypoint_A, keypoint_B)
        dist = super().real_distance(euc_dist)

        velocity = dist / time

        return velocity
    
