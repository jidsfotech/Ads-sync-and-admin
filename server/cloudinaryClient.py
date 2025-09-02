import cloudinary
from cloudinary import CloudinaryImage
from cloudinary.uploader import upload
import cloudinary.api
import os
from dotenv import load_dotenv
from fastapi import HTTPException, status, UploadFile
load_dotenv()

cloudinary.config(
    cloud_name=os.getenv("CLOUDINARY_NAME"),
    api_key=os.getenv("CLOUDINARY_API_KEY"),
    api_secret=os.getenv("CLOUDINARY_API_SECRET"),
    secure=True
    )

# def uploadFileToloudinary(uploaded:UploadFile):
#     print(f"Uploading {uploaded} to Cloudinary...")
#     print(f"file........... {uploaded.file} to Cloudinary...")

#     try:
#         result = upload(uploaded.file)
#         return result["secure_url"]
#     except Exception as e:
#         print("Cloudinary upload failed: {e}")
#         raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Error uploading images: {e}")

def uploadFileToloudinary(uploaded:UploadFile):
    try:
        resourceType = uploaded.content_type.split("/")[0]  # "image", "video", "audio", etc.

        if resourceType not in ["video", "audio", "image"]:
            resourceType = "raw"

        print(f"Uploading {resourceType} to Cloudinary...")
        result = upload(
            uploaded.file, 
            resource_type=resourceType, 
            asset_folder="adsync"
            )
        
        return result["secure_url"]
    
    except Exception as e:
        print(f"Cloudinary upload failed: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Error uploading images: {e}")
