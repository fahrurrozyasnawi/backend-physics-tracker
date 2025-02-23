from pydantic import BaseModel, Field
from typing import Optional, Any

class ViscosityBodyReq(BaseModel):
    distance: float
    radius: float
    densityT: float
    densityF: float


class PendulumBodyReq(BaseModel):
    time: Optional[float]
    lRope: Optional[float]
    xInit: Optional[float]
    xLast: Optional[float]
    mass: Optional[float]
    theta: Optional[float]
    type: str


class ProjectileMotionBodyReq(BaseModel):
    yVal: Optional[float]
    xVal: float
