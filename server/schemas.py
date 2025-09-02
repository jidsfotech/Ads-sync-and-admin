from pydantic import BaseModel
from datetime import datetime, timedelta
from typing import Optional

# -------- Billboard --------
class BillboardBase(BaseModel):
    name: str
    location: Optional[str] = None

class BillboardCreate(BillboardBase):
    pass

class Billboard(BillboardBase):
    id: int
    class Config:
        orm_mode = True


# -------- Ad --------
class AdBase(BaseModel):
    file_path: str
    file_type: str

class Ad(AdBase):
    id: int
    uploaded_at: datetime
    class Config:
        orm_mode = True

class GetAd(Ad):
    skip: int = 0
    limit: int = 1

# -------- Schedule --------
class ScheduleBase(BaseModel):
    ad: AdBase              
    billboard: BillboardBase
    billboard_id: int
    ad_id: int
    start_time: datetime
    end_time: datetime
    duration: Optional[timedelta] = None

class ScheduleCreate(BaseModel):
     billboard_id: int
     ad_id: int
     start_time: datetime
     end_time: datetime
     duration: Optional[timedelta] = None

class Schedule(ScheduleBase):
    id: int
    class Config:
        orm_mode = True
