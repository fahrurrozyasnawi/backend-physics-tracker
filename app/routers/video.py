import os
import uuid
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

task_progress = {}

def tracking_object(body: BodyTrackObject, task_id):
    video_path = os.path.join(get_static_dir(), body.path[1:], body.filename)
    filename, ext = os.path.splitext(body.filename)
    generated_filename = f'{filename}-generated{ext}'
    generated_path = os.path.join(get_static_dir(), body.path[1:], generated_filename)
    # output_filename = f'{filename}-result{ext}'
    # output_path = os.path.join(get_static_dir(), body.path[1:], output_filename)

    print('video path', video_path)
    print('generated path', generated_path)
    tracker_service = TrackerService(generated_path)
    video_service = VideoServices(video_path)
    
    formula_result = 0
    task_progress[task_id] = 0
    tracker_service.init_task(task_id)
    try:
        bbox = video_service.convert_bbox_obj_to_xyxy(body.bbox)
        print('bbox',bbox)
        bboxes, keypoints = tracker_service.predict(bbox)
        tracker_result = tracker_service.generate_video_result(video_path)

        if(body.lessonType == 'viscosity'):
            viscosity_service = ViscosityService(body.lessonData)
            pointA = video_service.get_center_from_bbox_xyxy(bboxes[0])
            pointB = video_service.get_center_from_bbox_xyxy(bboxes[len(bboxes) - 1])
            time = body.timeEnd - body.timeStart

            velocity = viscosity_service.calculate_velocity(pointA, pointB, time)
            formula_result = viscosity_service.calculate_formula(velocity)

        if(body.lessonType == 'projectile-motion'):
            projectile_motion_service = ProjectileMotionService(body.lessonData)
            fps = video_service.get_fps()
            time = body.timeEnd - body.timeStart
            V0 = projectile_motion_service.calculate_init_velocity(bboxes, fps)
            elevation = projectile_motion_service.get_elevation_from_init_velocity(V0)
                        
            result_by_x = projectile_motion_service.calculate_by_x(V0, elevation, time)
            result_by_y = projectile_motion_service.calculate_by_y(V0, elevation, time)

            formula_result = {"x": result_by_x, "y": result_by_y}


        if(body.lessonType == 'pendulum'):
            pendulum_service = PendulumService(body.lessonData)
            x_positions = []
            for bbox in bboxes:
                x1, y1, x2, y2 = bbox
                x_positions.append((x1))
            
            freq = pendulum_service.calculate_freq_and_period(x_positions)
            amplitude = pendulum_service.calculate_amplitude(x_positions)

            formula_result = pendulum_service.calculate_formula(freq, amplitude=amplitude) 

        data = {"result": formula_result, "video": tracker_result}
        return data
    except:
        raise HTTPException(
            status_code=400, detail='Failed to tracking object!')


@router.post('/extract-frame')
async def extract_frame(body: BodyExtractFrame):
    video_path = os.path.join(get_static_dir(), body.path[1:], body.filename)
    video_service = VideoServices(video_path)

    frame_result = video_service.extract_frame_at_time(body.timeStart)
    output_video_generated = video_service.generate_video_by_timeline(body.timeStart, body.timeEnd)

    data = {"frame": frame_result, "output_video_path": output_video_generated}
    if frame_result:
        return CustomResponse(success=True, data=data)
    else:
        return HTTPException(status_code=406, detail='Cannot extract frame')

@router.post('/track-object')
async def track_object(body: BodyTrackObject, background_task: BackgroundTasks):
    id = str(uuid.uuid4())
    background_task.add_task(tracking_object, body, id)

    return CustomResponse(success=True, message="Success tracking", data=id)
    

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
    progress = task_progress.get(task_id, None)
    if progress is None:
        return HTTPException(detail="Invalid task ID", status_code=404)
    return CustomResponse(success=True, data=progress)