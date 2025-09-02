from fastapi import APIRouter, Depends, UploadFile, File, Request, status
from sqlalchemy.orm import Session
from . import models, schemas, service, database

models.Base.metadata.create_all(bind=database.engine)

router = APIRouter()

# Dependency
def get_db():
    db = database.SessionLocal()
    try:
        yield db
    finally:
        db.close()
        
# Billboard
@router.post("/billboards/", response_model=schemas.Billboard)
def createBillboard(billboard: schemas.BillboardCreate, db: Session = Depends(get_db)):
    return service.createBillboard(db=db, billboard=billboard)

@router.get("/billboards/", response_model=list[schemas.Billboard])
def listBillboards(skip: int = 0, limit: int = 10, id: int = 0, db: Session = Depends(get_db)):
    return service.getBillboards(db, skip=skip, limit=limit, id=id)


# Ad upload
@router.post("/upload-ad/", response_model=schemas.Ad)
def uploadAd(uploaded: UploadFile = File(...), db: Session = Depends(get_db)):

    if not uploaded:
      raise Exception("No file uploaded")
    try:
        print(f"Received file of type: {uploaded.content_type}")
        return service.createAd(db, uploaded, file_type=uploaded.content_type)
    except Exception as e:
     print(f"Error processing file: {e}")
     raise

@router.get("/ads/", response_model=list[schemas.Ad])
def listAds(skip: int = 0, limit: int = 10, db: Session = Depends(get_db)):
    return service.getAds(db, skip=skip, limit=limit)


# Schedule
@router.post("/schedules/", response_model=schemas.Schedule)
async def createSchedule(schedule: schemas.ScheduleCreate, db: Session = Depends(get_db)):
    return await service.createSchedule(db=db, schedule=schedule)

@router.get("/schedules/", response_model=list[schemas.Schedule])
def listSchedules(skip: int = 0, limit: int = 10, db: Session = Depends(get_db)):
    schedule = service.getSchedules(db, skip=skip, limit=limit)
    print("Schedules fetched:", schedule)
    return schedule
