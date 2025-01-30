import os
import uvicorn
from dotenv import load_dotenv
from fastapi import FastAPI, APIRouter
from fastapi.middleware.cors import CORSMiddleware
from config.upload_dir import static_dir_instance
from routers import video, upload

load_dotenv()

# create uploads dir if doesn't exist
os.makedirs('uploads', exist_ok=True)

app = FastAPI()
api_router = APIRouter(prefix='/api')

origins = ["*"]
app.add_middleware(CORSMiddleware,
                   allow_origins=origins,
                   allow_credentials=True,
                   allow_methods=["*"],
                   allow_headers=["*"],)


app.mount('/uploads', static_dir_instance, name='uploads')

# register routes
api_router.include_router(video.router)
api_router.include_router(upload.router)

app.include_router(api_router)


@app.get("/")
async def root():
    return {"message": "Hello World"}

PORT = int(os.getenv('PORT'))

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=PORT, reload=True)
