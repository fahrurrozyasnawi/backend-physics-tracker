from pydantic import BaseModel, Field
from typing import Optional, Any

class ViscosityBodyReq(BaseModel):
    radius: float
    densityT: float
    densityF: float


class PendulumBodyReq(BaseModel):
    time: float
    freq: float
    mass: Optional[float]


class ProjectileMotionBodyReq(BaseModel):
    yVal: float
    xVal: float
