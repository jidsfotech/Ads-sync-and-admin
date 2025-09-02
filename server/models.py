from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Interval
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from .database import Base

class Billboard(Base):
    __tablename__ = "billboards"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    location = Column(String, nullable=True)

    schedules = relationship("Schedule", back_populates="billboard")


class Ad(Base):
    __tablename__ = "ads"

    id = Column(Integer, primary_key=True, index=True)
    file_path = Column(String, nullable=False)
    file_type = Column(String, nullable=False) 
    uploaded_at = Column(DateTime(timezone=True), server_default=func.now())

    schedules = relationship("Schedule", back_populates="ad")


class Schedule(Base):
    __tablename__ = "schedules"

    id = Column(Integer, primary_key=True, index=True)
    billboard_id = Column(Integer, ForeignKey("billboards.id"))
    ad_id = Column(Integer, ForeignKey("ads.id"))
    start_time = Column(DateTime, nullable=False)
    end_time = Column(DateTime, nullable=False)
    duration = Column(Interval, nullable=True) 

    billboard = relationship("Billboard", back_populates="schedules")
    ad = relationship("Ad", back_populates="schedules")