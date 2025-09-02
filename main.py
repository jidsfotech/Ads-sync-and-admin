from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder
from fastapi.encoders import jsonable_encoder
from server import routes, websockets
from starlette.exceptions import HTTPException as StarletteHTTPException


app = FastAPI()

# WebSocket routes
app.include_router(websockets.router)

# Include routes from routes.py
app.include_router(routes.router, prefix="/api", tags=["Ads"])

@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request:Request, exc:StarletteHTTPException):
    print("StarletteHTTPException:", str(exc.detail))
    return JSONResponse(
        status_code=exc.status_code,
        content=jsonable_encoder({"detail": exc.detail}),
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    print("RequestValidationError:", str(exc))
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content=jsonable_encoder({"detail": exc.errors(), "body": exc.body}),
    )

@app.get("/")
def root():
    return {"message": "Hello, AdSync is running!"}