from pydantic import BaseModel
from typing import Union
from models.lessons import PendulumBodyReq, ProjectileMotionBodyReq, ViscosityBodyReq

class BodyExtractFrame(BaseModel):
    filename: str
    path: str
    timeStart: float
    timeEnd: float

class Bbox(BaseModel):
    x: float
    y: float
    width: float
    height: float

class BodyTrackObject(BaseModel):
    lessonData: Union[PendulumBodyReq, ProjectileMotionBodyReq, ViscosityBodyReq]
    lessonType: str
    videoSrc: str
    filename: str
    path: str
    bbox: Bbox
    timeStart: float
    timeEnd: float

class BodyStream(BaseModel):
    videoSrc: str
