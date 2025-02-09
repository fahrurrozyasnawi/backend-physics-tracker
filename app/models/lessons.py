from pydantic import BaseModel, Field
from typing import Optional, Any

class ViscosityBodyReq(BaseModel):
    radius: float
    densityT: float
    densityF: float


class PendulumBodyReq(BaseModel):
    time: Optional[float]
    freq: float
    mass: Optional[float]


class ProjectileMotionBodyReq(BaseModel):
    yVal: float
    xVal: float
