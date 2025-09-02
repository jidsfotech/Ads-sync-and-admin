from sqlalchemy.orm import Session, joinedload
from . import cloudinaryClient, models, schemas, websockets
import os 
from dotenv import load_dotenv
from fastapi import HTTPException, status, UploadFile
from fastapi.encoders import jsonable_encoder



load_dotenv()


# -------- Billboard --------
def createBillboard(db: Session, billboard: schemas.BillboardCreate):
    db_billboard = models.Billboard(name=billboard.name, location=billboard.location)
    db.add(db_billboard)
    db.commit()
    db.refresh(db_billboard)
    return db_billboard

def getBillboards(db: Session, skip: int = 0, limit: int = 10, id: int = 0):
    query = db.query(models.Billboard).offset(skip).limit(limit)
    return query.all()


# -------- Ad (upload to Cloudinary) --------
def createAd(db: Session, uploaded:UploadFile, file_type: str): 
    try:  
        # Upload file first
        file_url = cloudinaryClient.uploadFileToloudinary (uploaded)
        db_ad = models.Ad(
            file_path=file_url,
            file_type=file_type
            )
        db.add(db_ad)
        db.commit()
        db.refresh(db_ad)
        return db_ad
    except HTTPException as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=e)

def getAds(db: Session, skip: int = 0, limit: int = 10):
    return db.query(models.Ad).offset(skip).limit(limit).all()

# -------- Schedule --------
async def createSchedule(db: Session, schedule: schemas.ScheduleCreate):
    ad = db.query(models.Ad).filter(models.Ad.id == schedule.ad_id).first()
    billboard = db.query(models.Billboard).filter(models.Billboard.id == schedule.billboard_id).first()

    if not ad or not billboard:
        raise HTTPException(status_code=400, detail="Invalid ad_id or billboard_id")
    
    db_schedule = models.Schedule(
        billboard_id=schedule.billboard_id,
        ad_id=schedule.ad_id,
        start_time=schedule.start_time,
        end_time=schedule.end_time,
        duration=schedule.duration
    )
    db.add(db_schedule)
    db.commit()
    db.refresh(db_schedule)

    await websockets.broadcast({"type": "new_schedule_created", "schedule": jsonable_encoder(db_schedule)})
    return db_schedule

def getSchedules(db: Session, skip: int = 0, limit: int = 10):
    return (
        db.query(models.Schedule)
        .options(
            joinedload(models.Schedule.ad),      
            joinedload(models.Schedule.billboard)
        )
        .offset(skip)
        .limit(limit)
        .all()
    )

