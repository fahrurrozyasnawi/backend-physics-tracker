import os
import uuid
from typing import Dict
from collections import OrderedDict
from app.config.upload_dir import get_static_dir
from fastapi import APIRouter, HTTPException, BackgroundTasks
from fastapi.responses import StreamingResponse
from app.models.api import CustomResponse
from app.models.video import BodyExtractFrame, BodyTrackObject
from app.services.video import VideoServices
from app.services.tracker import TrackerService
from app.services.lessons import ViscosityService, HarmonicMotionService, ProjectileMotionService

router = APIRouter(
    prefix='/video',
    tags=['video'],
    responses={404: {"description": "Not Found"}}
)

task_results: Dict[str, dict] = OrderedDict()


def cleanup_old_entries():
    if len(task_results) > 7:
        for _ in range(6):
            task_results.popitem(last=False)

def tracking_object(body: BodyTrackObject, task_id):
    video_src_path = os.path.join(get_static_dir(),body.path[1:], body.filename)
    tracker_service = TrackerService(video_src_path)
    video_service = VideoServices(video_src_path)
    
    tracker_service.init_task(task_id)
    # start tracking
    tracker_service.track_object(body)

    task_progress = tracker_service.get_task_progress(task_id)
    
    formula_result = 0
    if(task_progress['progress'] == 0.8):
        bboxes = tracker_service.get_bboxes_result()      
        time = body.timeEnd - body.timeStart
        fps = video_service.get_fps()
        width, height = video_service.get_resolution()
        print('lesson type', body.lessonType)
        if(body.lessonType == 'viscosity'):
            print('calculate viscosity')
            viscosity_service = ViscosityService(body.lessonData, time)
            pointA = video_service.get_center_from_bbox_xyxy(bboxes[0])
            pointB = video_service.get_center_from_bbox_xyxy(bboxes[len(bboxes) - 1])
            points = (pointA, pointB)
            
            viscosity_service = viscosity_service.init_keypoints(points)

            velocity = viscosity_service.calculate_velocity()
            coef = viscosity_service.calculate_coefision()
            viscosity = viscosity_service.calculate_formula()
            # graph = viscosity_service.cre

            formula_result = {
                "viscosity": viscosity, 
                "velocity": velocity, 
                "coef": coef
            }
            print('calculate complete')

        if(body.lessonType == 'projectile-motion'):
            print('calculate projectile motion')
            
            projectile_motion_service = ProjectileMotionService(body.lessonData, time)

            projectile_motion_service = projectile_motion_service.init_params(bboxes, fps, height)

            elevation = projectile_motion_service.calculate_elevation()
            v0_x = projectile_motion_service.get_init_velocity_x()
            v0 = projectile_motion_service.calculate_init_velocity()
            v0_y = projectile_motion_service.get_init_velocity_y()

            vx = v0_x
            # vy = projectile_motion_service.calculate_velocity_y()
            vy = projectile_motion_service.calculate_velocity_y_v2()
            
            y = projectile_motion_service.calculate_y()
            hmax = projectile_motion_service.calculate_hmax()
            tT = projectile_motion_service.calculate_tT()
            ty_max = projectile_motion_service.calculate_ty_max()
            graph = projectile_motion_service.create_plot()

            formula_result = {
                "vx": vx, 
                "vy": vy,
                "v0_y": v0_y, 
                "v0_x": v0_x, 
                "elevation": elevation, 
                "v0": v0, 
                "y": y, 
                "hmax": hmax, 
                "tT": tT,
                # "ty_max": tT / 2,
                "ty_max": ty_max,
                "graph": graph
            }
            print('calculate complete')

        if(body.lessonType == 'pendulum'):
            print('calculate pendulum')
            type = body.lessonData.type
            harmonic_motion_service = HarmonicMotionService(body.lessonData, time)
            if type == 'bandul':
                x_positions = []
                for bbox in bboxes:
                    x1, y1, x2, y2 = bbox
                    x_positions.append((x1 + x2) / 2)

                harmonic_motion_service = harmonic_motion_service.init_pendulum_params(bboxes, x_positions, fps)
                
                amplitude = harmonic_motion_service.calculate_pendulum_amplitude()
                y = harmonic_motion_service.calculate_pendulum_y()
                F = harmonic_motion_service.calculate_pendulum_F()
                freq_deg = harmonic_motion_service.calculate_pendulum_freq_deg()
                freq = harmonic_motion_service.calculate_pendulum_freq()
                period = harmonic_motion_service.calculate_pendulum_T()
                graph = harmonic_motion_service.create_pendulum_fig_plot()

                formula_result = {
                    "y": y, 
                    "F": F, 
                    "amplitude": amplitude, 
                    "period": period,
                    "freq": 1 / period,
                    "freq_deg": freq_deg,
                    "graph": graph,
                    }

            if type == 'pegas':
                harmonic_motion_service = harmonic_motion_service.init_spring_params(bboxes, fps)

                constant = harmonic_motion_service.calculate_spring_constant()
                F = harmonic_motion_service.calculate_spring_F()
                freq_deg = harmonic_motion_service.calculate_spring_freq_deg()
                freq = harmonic_motion_service.calculate_spring_freq()
                period = harmonic_motion_service.calculate_spring_period()
                v = harmonic_motion_service.calculate_spring_v()
                v_max = harmonic_motion_service.calculate_v_max()
                k_e = harmonic_motion_service.calculate_kinetic_energy()
                p_e = harmonic_motion_service.calculate_potential_energy()
                m_e = harmonic_motion_service.calculate_total_energy()
                graph = harmonic_motion_service.create_spring_fig_plot()

                formula_result = {
                    "constant": constant,
                    "F": F,
                    "freq_deg": freq_deg,
                    "freq": 1 / period,
                    "period": period,
                    "v": v,
                    "v_max": v_max,
                    "k_e": k_e,
                    "p_e": p_e,
                    "m_e": m_e,                     
                    "graph": graph,                     
                }

            print('calculate complete')

    data = {"result": formula_result}

    tracker_service.completed_task_progress()
    task_results[task_id] = data
    cleanup_old_entries()


@router.post('/extract-frame')
async def extract_frame(body: BodyExtractFrame):
    video_path = os.path.join(get_static_dir(), body.path[1:], body.filename)
    video_service = VideoServices(video_path)
    
    frame_result = video_service.extract_frame_at_time(body.timeStart)
    # output_video_generated = video_service.generate_video_by_timeline(body.timeStart, body.timeEnd)

    data = {"frame": frame_result}
    if frame_result:
        return CustomResponse(success=True, data=data)
    else:
        return HTTPException(status_code=406, detail='Cannot extract frame')

@router.post('/track-object')
async def track_object(
    body: BodyTrackObject, 
    background_tasks: BackgroundTasks):
    id = str(uuid.uuid4())
    background_tasks.add_task(tracking_object, body, id)

    return CustomResponse(success=True, message="Success tracking", data=id)

@router.get('/formula-result/{task_id}')
async def get_formula_result(task_id: str):
    if task_id not in task_results:
        return HTTPException(status_code=404, detail="Task not found or not completed")
    formula_result = task_results[task_id]
    return CustomResponse(success=True, data=formula_result)


@router.get('/result/{path:path}')
async def stream_result(path: str):
    dst_path = os.path.join(get_static_dir(), path)
    def iterfile():
        if not os.path.exists(dst_path):  # Check if the file exists
            raise HTTPException(status_code=404, detail="File not found")
        with open(dst_path, mode='rb') as file_stream:
            yield from file_stream
    
    return StreamingResponse(iterfile(), media_type='video/mp4')

@router.get("/progress/{task_id}")
async def get_progress(task_id: str):
    tracker_service = TrackerService()
    progress = tracker_service.get_task_progress(task_id)
    if progress is None:
        return HTTPException(detail="Invalid task ID", status_code=404)
    return CustomResponse(success=True, data=progress)