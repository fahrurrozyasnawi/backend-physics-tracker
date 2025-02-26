from app.models.lessons import ViscosityBodyReq, PendulumBodyReq, ProjectileMotionBodyReq
from scipy.signal import find_peaks
import numpy as np
import matplotlib.pyplot as plt
import math
import io
import base64

class LessonsService:
    def __init__(self):
        self.scale_factor = 0.01

    def euclidean_distance(self, pointA, pointB):
        self.pointA = pointA
        self.pointB = pointB

        return math.sqrt((pointB[0] - pointA[0]) ** 2 + (pointB[1] - pointA[1]) ** 2)
    
    def real_distance(self, pixel_distance):
        scale_factor = 0.01
        return pixel_distance * scale_factor

class HarmonicMotionService(LessonsService):
    def __init__(self, body: PendulumBodyReq, time):
        self.body = body
        self.time = time
        self.g = 9.8
    # Spring
    def init_spring_params(self, bbox, fps):
        self.init_bbox = bbox[0]
        self.rest_bbox = bbox[1:]
        self.fps = fps

        return self

    def __calculate_vertical_length(self, bbox):
        x,y,x1,y1 = self.init_bbox
        init_pixel_L = y1 - y

        x,y,x1,y1 = bbox
        current_pixel_L = y1 - y
        
        scale = init_pixel_L / self.body.xLast
        current_L = current_pixel_L * scale

        return current_L
    
    def get_list_L_bboxes(self):
        list_bboxes = self.rest_bbox
        L_list = [self.__calculate_vertical_length(bbox) for bbox in list_bboxes]

        return L_list
    
    def create_spring_fig_plot(self):
        time = self.time
        N = len(self.rest_bbox)
        # time_list = [i / self.fps for i in range(N)]
        time_list = np.linspace(0, time, N)

        L_list = self.get_list_L_bboxes()

        plt.figure(figsize=(8, 4))
        plt.plot(time_list, L_list, marker='o', linestyle='-', color='blue', label='Panjang Pegas')
        plt.xlabel('Waktu (detik)')
        plt.ylabel('Panjang Pegas (cm)')
        plt.title('Grafik Panjang Pegas Vertikal terhadap Waktu')
        plt.legend()
        plt.grid(True)

        ioBytes = io.BytesIO()
        plt.savefig(ioBytes, format='png')
        ioBytes.seek(0)
        base64Data = base64.b64encode(ioBytes.read()).decode()

        return base64Data
    
    def calculate_oscilation_counts(self):
        time = self.time
        N = len(self.rest_bbox)
        time_list = np.linspace(0, time ,N)
        L_list = self.get_list_L_bboxes()

        peaks, _ = find_peaks(L_list)
        peak_times = time_list[peaks]

        if len(peak_times) > 1:
            periods = np.diff(peak_times)
            avg_period = np.mean(periods)
            oscilation_count = time / avg_period
        else:
            avg_period = None
            oscilation_count = 0

        return oscilation_count

    def get_spring_A_and_range_max(self):
        # L_eq = self.body.xLast
        L_values = self.get_list_L_bboxes()

        L_max = max(L_values)
        L_min = min(L_values)

        A = (L_max - L_min) / 2
        range_max = L_max - L_min
        return (A, range_max)
      
    def calculate_spring_constant(self):
        F = self.__calculate_spring_F()
        deltaX = self.body.xLast - self.body.xInit
        
        constant = F / deltaX

        return constant
    
    def __calculate_spring_F(self):
        mass = self.body.mass
        g = self.g

        F = mass *g

        return F
    
    def calculate_spring_F(self):
        constant = self.calculate_spring_constant()
        deltaX = self.body.xLast - self.body.xInit

        F = - constant * deltaX

        return F
    
    def calculate_spring_freq_deg(self):
        constant = self.calculate_spring_constant()
        mass = self.body.mass

        freq_deg = math.sqrt(constant / mass)

        return freq_deg
    
    def calculate_v_max(self):
        A, _ = self.get_spring_A_and_range_max()
        constant = self.calculate_spring_constant()
        mass = self.body.mass

        v_max = A * math.sqrt(constant / mass)

        return v_max
    
    def calculate_spring_y(self):
        A, _ = self.get_spring_A_and_range_max()
        fred_deg = self.calculate_spring_freq_deg()
        time = self.time

        y = A * math.sin(math.radians(fred_deg * time))

        return y

    def calculate_spring_v(self):
        A, _ = self.get_spring_A_and_range_max()
        freq_deg = self.calculate_spring_freq_deg()
        time = self.time

        v = A * freq_deg * math.cos(freq_deg * time)

        return v
    
    def calculate_kinetic_energy(self):
        mass = self.body.mass
        v = self.calculate_spring_v()

        k_e = 1 / 2 * mass * math.pow(v, 2)

        return k_e
    
    def calculate_potential_energy(self):
        constant = self.calculate_spring_constant()
        y = self.calculate_spring_y()

        e_p = 1 / 2 * constant * math.pow(y, 2)

        return e_p
    
    def calculate_total_energy(self):
        e_p = self.calculate_potential_energy()
        e_k = self.calculate_kinetic_energy()

        e_m = e_p + e_k

        return e_m
    
    def calculate_spring_period(self):        
        mass = self.body.mass
        constant = self.calculate_spring_constant()

        T = 2 * math.pi * math.sqrt(mass / constant)
        
        return T
    
    def calculate_spring_freq(self):        
        freq_deg = self.calculate_spring_freq_deg()

        freq = ((1 / 2) * math.pi) * freq_deg

        return freq

############################################################################

    # Pendulum
    def calculate_pendulum_F(self):
        mass = self.body.mass
        g = self.g

        F = -mass * g * math.sin(math.radians(self.body.theta))

        return F
    
    def calculate_pendulum_freq_deg(self):
        L = self.body.lRope
        g = self.g

        freq_deg = math.sqrt(g / L)
        
        return freq_deg
    
    def calculate_pendulum_freq(self):
        freq_deg = self.calculate_pendulum_freq_deg()

        freq = (1 / 2 * math.pi) * freq_deg

        return freq
    
    def calculate_pendulum_T(self):
        L = self.body.lRope
        g = self.g

        T = 2 * math.pi * math.sqrt(L / g)

        return T
    
    def calculate_pendulum_y(self):
        A = self.calculate_pendulum_amplitude()
        theta = self.body.theta

        y = A * math.sin(math.radians(theta))

        return y
    
    def init_pendulum_params(self, bboxes, positions, fps):
        self.bboxes = bboxes
        self.positions = positions
        self.fps = fps

        return self
    
    def calculate_pendulum_amplitude(self):
        centers = np.array(self.positions)
        center_max = max(centers)
        center_min = min(centers)
        amplitude_pixels = (center_max - center_min) / 2.0
        
        return amplitude_pixels
    
    def calculate_pendulum_theta0(self):
        theta = self.body.theta
        time = self.time
        freq_deg = self.calculate_pendulum_freq_deg()

        theta0 = theta / freq_deg * time

        return theta0
    
    def calculate_pendulum_v(self):
        freq_deg = self.calculate_pendulum_freq_deg()
        A = self.calculate_pendulum_amplitude()
        theta = self.body.theta

        v = freq_deg * A * math.cos(theta)

        return  v
    
    def calculate_pendulum_a(self):
        freq_deg = self.calculate_pendulum_freq_deg()
        y = self.calculate_pendulum_y()

        a = - math.pow(freq_deg, 2) * y

        return a
    
    def create_pendulum_fig_plot(self):
        time = self.time
        fps = self.fps

        x_centers = [(box[0] + box[2]) / 2 for box in self.bboxes]
        N = len(self.bboxes)
        time_plot = np.linspace(0, time, N)

        plt.figure(figsize=(12, 6))
        plt.plot(time_plot, x_centers, 'b-', linewidth=2)
        plt.title('Grafik Gerak Harmonik Bandul')
        plt.xlabel('Waktu (detik)')
        plt.ylabel('Posisi Horizontal (pixel)')
        plt.grid(True)

        ioBytes = io.BytesIO()
        plt.savefig(ioBytes, format='png')
        ioBytes.seek(0)
        base64Data = base64.b64encode(ioBytes.read()).decode()

        return base64Data

    
class ProjectileMotionService:
    def __init__(self, body: ProjectileMotionBodyReq, time):
        self.x_val = body.xVal
        self.g = 9.8
        self.time = time
    
    def calculate_elevation(self):
        distance = self.x_val
        centers = self.__get_list_centers()

        pixel_dist = abs(centers[-1, 0] - centers[0,0])
        convertion = distance / pixel_dist

        centers_world = centers.copy()
        centers_world[:, 0] = centers[:, 0] * convertion
         
        video_height = self.height
        centers_world[:, 1] = (video_height - centers[:, 1]) * convertion

        x = centers_world[:, 0]
        y = centers_world[:, 1]

        koef = np.polyfit(x, y, 2)

        x0 = x[0]
        deriv_start = 2 * koef[0] * x0 + koef[1]
        elevation_angle_rad = np.arctan(deriv_start)
        elevation_angle_deg = np.degrees(elevation_angle_rad)

        return abs(elevation_angle_deg)

    def init_params(self, bboxes, fps, frame_height):
        self.bboxes = bboxes
        self.fps = fps
        self.height = frame_height

        return self
    
    def create_plot(self):
        time = self.time
        distance = self.x_val
        centers = self.__get_list_centers()

        pixel_dist = abs(centers[-1, 0] - centers[0,0])
        convertion = distance / pixel_dist

        centers_world = centers.copy()
        centers_world[:, 0] = centers[:, 0] * convertion

        video_height = self.height
        centers_world[:, 1] = (video_height - centers[:, 1]) * convertion
        # centers_world[:, 1] = centers[:, 1] * convertion

        n_frames = len(self.bboxes)
        time_plot = np.linspace(0, time, n_frames)

        x = centers_world[:, 0]
        y = centers_world[:, 1]

        coef = np.polyfit(x,y,2)
        p_parabolic = np.poly1d(coef)

        x_fit = np.linspace(x.min(), x.max(), 100)
        y_fit = p_parabolic(x_fit)

        plt.figure(figsize=(8, 6))
        plt.scatter(x, y, color='blue', label='Titik Deteksi')
        plt.plot(x_fit, y_fit, color='red', linewidth=2, label='Fitting Parabola')
        plt.xlabel('Jarak Horizontal (meter)')
        plt.ylabel('Ketinggian (meter)')
        plt.title('Grafik Parabola Pergerakan Bola')
        plt.legend()
        plt.grid(True)

        ioBytes = io.BytesIO()
        plt.savefig(ioBytes, format='png')
        ioBytes.seek(0)
        base64Data = base64.b64encode(ioBytes.read()).decode()

        return base64Data

    def __get_list_centers(self):
        bboxes = self.bboxes
        centers = []

        for bbox in bboxes:
            x_center = (bbox[0] + bbox[2]) / 2
            y_center = (bbox[1] + bbox[3]) / 2
            centers.append([x_center, y_center])
        
        centers = np.array(centers)

        return centers

    def get_init_velocity_y(self):
        elevation = self.calculate_elevation()
        vo = self.calculate_init_velocity()

        sin_theta = math.sin(math.radians(elevation))
        vo_y = vo * sin_theta

        return vo_y
    
    def calculate_hmax(self):
        elevation = self.calculate_elevation()
        v0 = self.calculate_init_velocity()
        g = self.g

        # hmax = (math.pow(v0, 2) * math.sin(math.radians(math.pow(elevation, 2)))) / 2.0 * g
        first_line = math.pow(v0 * math.sin(math.radians(elevation)), 2)
        second_line = 2 * g
        hmax = first_line / second_line

        return hmax
    
    def calculate_velocity_y(self):
        v0_y = self.get_init_velocity_y()
        time = self.time
        g = self.g
        Vy = v0_y - (g * time)

        return Vy
    
    def calculate_real_t(self):
        tx_max = self.calculate_tT()
        duration = self.time

        real_duration = tx_max / duration

        return real_duration

    
    def calculate_velocity_y_v2(self):
        v0_y = self.get_init_velocity_y()
        time = self.time
        g = self.g

        # Vy = v0_y - (g * time)
        Vy = f"{v0_y} - {g}t"

        return Vy
    
    def calculate_tT(self):
        elevation = self.calculate_elevation()
        v0 = self.calculate_init_velocity()
        g = self.g

        first_line = 2 * v0 * math.sin(math.radians(elevation))
        tT = first_line / g

        return tT
    
    def calculate_ty_max(self):
        tx_max = self.calculate_tT()

        ty_max = tx_max / 2

        return ty_max
   
    # def calculate_tT(self):
    #     elevation = self.calculate_elevation()
    #     v0 = self.calculate_init_velocity()
    #     g = self.g

    #     tT = (2.0 * v0 * math.sin(math.radians(elevation))) / g

    #     return tT
    
    def get_init_velocity(self):
        g = self.g
        distance = self.x_val
        centers = self.__get_list_centers()

        pixel_dist = abs(centers[-1, 0] - centers[0,0])
        convertion = distance / pixel_dist

        centers_world = centers.copy()
        centers_world[:, 0] = centers[:, 0] * convertion
         
        video_height = self.height
        centers_world[:, 1] = (video_height - centers[:, 1]) * convertion

        x = centers_world[:, 0]
        y = centers_world[:, 1]

        koef = np.polyfit(x, y, 2)

        x0 = x[0]
        # Turunan dari y terhadap x: dy/dx = 2a*x + b
        deriv_start = 2 * koef[0] * x0 + koef[1]
        elevation_angle_rad = np.arctan(deriv_start)

        if koef[0] < 0:
            v0 = np.sqrt(-g / (2 * koef[0] * (np.cos(elevation_angle_rad)**2)))
            print("Kecepatan awal v0: {:.2f} m/s".format(v0))
        else:
            v0 = 0
            print("Koefisien parabola a tidak valid (harus negatif) untuk perhitungan v0.")
        
        return v0
    
    def calculate_init_velocity(self):
        time = self.time
        xmax = self.x_val
        g = self.g
        elevation = self.calculate_elevation()

        first_line = xmax * g
        second_line = math.sin(math.radians(2 * elevation))

        v0 = math.sqrt(first_line / second_line)
        
        return v0
    
    # def calculate_init_velocity(self):
    #     time = self.time
    #     g = self.g
    #     elevation = self.calculate_elevation()

    #     v0 = (time * g) / (2 * math.sin(math.radians(elevation)))
        
    #     return v0

    def get_init_velocity_x(self):
        v0 = self.calculate_init_velocity()
        elevation = self.calculate_elevation()

        v0_x = v0 * math.cos(math.radians(elevation))

        return v0_x
    
    def calculate_velocity_x(self):
        return self.get_init_velocity_x()
    
    def calculate_total_velocity(self):
        vx = self.calculate_velocity_x()
        vy = self.calculate_velocity_y()

        v_total = math.sqrt(math.pow(vx, 2) + math.pow(vy, 2))
        
        return v_total

    def calculate_y(self):
        time = self.time
        v0_y = self.get_init_velocity_y()

        g = self.g
        y = v0_y * time - (g * time**2) / 2
        # y = vo * math.sin(theta) * time - g * time

        return y

class ViscosityService(LessonsService):
    def __init__(self, body: ViscosityBodyReq, time):
        self.distance = body.distance
        self.radius = body.radius
        self.density_t = body.densityT
        self.density_f = body.densityF
        self.time = time

    def calculate_formula(self):
        velocity = self.calculate_velocity()
        coef = self.calculate_coefision()

        viscosity = 6 * math.pi * coef * self.radius * velocity

        return viscosity
    
    def calculate_coefision(self):
        velocity = self.calculate_velocity()
        result = (2 * math.pow(self.radius, 2) * 9.8 * (self.density_t - self.density_f)) / (9 * velocity)

        return result

    def init_keypoints(self, keypoints):
        self.keypoints = keypoints

        return self

    def calculate_velocity(self):
        time = self.time
        dist = self.distance
        # keypoint_A, keypoint_B = self.keypoints

        # euc_dist = super().euclidean_distance(keypoint_A, keypoint_B)
        # dist = super().real_distance(euc_dist)

        velocity = dist / time

        return velocity
    
