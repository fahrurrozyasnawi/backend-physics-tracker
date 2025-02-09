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
from app.services.lessons import ViscosityService, PendulumService, ProjectileMotionService

router = APIRouter(
    prefix='/video',
    tags=['video'],
    responses={404: {"description": "Not Found"}}
)

task_results: Dict[str, dict] = OrderedDict()

# def tracking_object(body: BodyTrackObject, task_id):
#     video_path = os.path.join(get_static_dir(), body.path[1:], body.filename)
#     filename, ext = os.path.splitext(body.filename)
#     generated_filename = f'{filename}-generated{ext}'
#     generated_path = os.path.join(get_static_dir(), body.path[1:], generated_filename)
#     # output_filename = f'{filename}-result{ext}'
#     # output_path = os.path.join(get_static_dir(), body.path[1:], output_filename)

#     print('video path', video_path)
#     print('generated path', generated_path)
#     tracker_service = TrackerService(generated_path)
#     video_service = VideoServices(video_path)
    
#     formula_result = 0
#     task_progress[task_id] = 0
#     tracker_service.init_task(task_id)
#     try:
#         bbox = video_service.convert_bbox_obj_to_xyxy(body.bbox)
#         print('bbox',bbox)
#         bboxes, keypoints = tracker_service.predict(bbox)
#         tracker_result = tracker_service.generate_video_result(video_path)

#         if(body.lessonType == 'viscosity'):
#             viscosity_service = ViscosityService(body.lessonData)
#             pointA = video_service.get_center_from_bbox_xyxy(bboxes[0])
#             pointB = video_service.get_center_from_bbox_xyxy(bboxes[len(bboxes) - 1])
#             time = body.timeEnd - body.timeStart

#             velocity = viscosity_service.calculate_velocity(pointA, pointB, time)
#             formula_result = viscosity_service.calculate_formula(velocity)

#         if(body.lessonType == 'projectile-motion'):
#             projectile_motion_service = ProjectileMotionService(body.lessonData)
#             fps = video_service.get_fps()
#             time = body.timeEnd - body.timeStart
#             V0 = projectile_motion_service.calculate_init_velocity(bboxes, fps)
#             elevation = projectile_motion_service.get_elevation_from_init_velocity(V0)
                        
#             result_by_x = projectile_motion_service.calculate_by_x(V0, elevation, time)
#             result_by_y = projectile_motion_service.calculate_by_y(V0, elevation, time)

#             formula_result = {"x": result_by_x, "y": result_by_y}


#         if(body.lessonType == 'pendulum'):
#             pendulum_service = PendulumService(body.lessonData)
#             x_positions = []
#             for bbox in bboxes:
#                 x1, y1, x2, y2 = bbox
#                 x_positions.append((x1))
            
#             freq = pendulum_service.calculate_freq_and_period(x_positions)
#             amplitude = pendulum_service.calculate_amplitude(x_positions)

#             formula_result = pendulum_service.calculate_formula(freq, amplitude=amplitude) 

#         data = {"result": formula_result, "video": tracker_result}
#         return data
#     except:
#         raise HTTPException(
#             status_code=400, detail='Failed to tracking object!')

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
        print('lesson type', body.lessonType)
        if(body.lessonType == 'viscosity'):
            print('calculate viscosity')
            viscosity_service = ViscosityService(body.lessonData)
            pointA = video_service.get_center_from_bbox_xyxy(bboxes[0])
            pointB = video_service.get_center_from_bbox_xyxy(bboxes[len(bboxes) - 1])
            points = (pointA, pointB)
            time = body.timeEnd - body.timeStart

            velocity = viscosity_service.calculate_velocity(points, time)
            viscosity = viscosity_service.calculate_formula(velocity)

            formula_result = {"viscosity": viscosity, "velocity": velocity}
            print('calculate complete')

        if(body.lessonType == 'projectile-motion'):
            print('calculate projectile motion')
            projectile_motion_service = ProjectileMotionService(body.lessonData)
            # fps = video_service.get_fps()
            time = body.timeEnd - body.timeStart

            vy = projectile_motion_service.calculate_velocity_y(time)
            vx = projectile_motion_service.calculate_velocity_x(time)
            elevation = projectile_motion_service.get_elevation(vx,vy)

            v0_y = projectile_motion_service.get_init_velocity_y(time)
            v0 = projectile_motion_service.get_init_velocity(elevation, v0_y=v0_y)
            # v0 = projectile_motion_service.calculate_init_velocity(bboxes, fps)
            # elevation = projectile_motion_service.get_elevation_from_init_velocity(v0)
                        
            # result_by_x = projectile_motion_service.calculate_by_x(v0, elevation, time)
            # result_by_y = projectile_motion_service.calculate_by_y(v0, elevation, time)

            formula_result = {"vx": vx, "vy": vy, "elevation": elevation, "v0": v0}
            print('calculate complete')

        if(body.lessonType == 'pendulum'):
            print('calculate pendulum')
            pendulum_service = PendulumService(body.lessonData)
            x_positions = []
            for bbox in bboxes:
                x1, y1, x2, y2 = bbox
                x_positions.append((x1))
            
            freq = pendulum_service.calculate_freq_and_period(x_positions)
            amplitude = pendulum_service.calculate_amplitude(x_positions)

            result = pendulum_service.calculate_formula(freq, amplitude=amplitude) 

            formula_result = {"result": result, "amplitude": amplitude, "period": 1/body.lessonData.freq}
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