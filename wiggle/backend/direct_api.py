"""
Direct API for Cloth Physics Simulation
Replaces n8n workflow with FastAPI endpoints
"""

from fastapi import FastAPI, File, UploadFile, Form, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
import httpx
import weaviate
import weaviate.classes as wvc
from weaviate.classes.query import Filter
import uuid
import os
import tempfile
import shutil
from datetime import datetime
from typing import Optional, List
import asyncio
import logging
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Wiggle Cloth Physics API",
    description="Direct API for 3D cloth physics simulation and texture generation",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configuration
WEAVIATE_GRPC_ENDPOINT = os.getenv("WEAVIATE_GRPC_ENDPOINT", "grpc-aoj6v69aspmruwn6zlgma.c0.europe-west3.gcp.weaviate.cloud")
WEAVIATE_API_KEY = os.getenv("WEAVIATE_API_KEY", "N08rcE1Ua0pJTlB1RVh0cF9XeEJjMVRGZE5MdjF1YkpqanZKc1RHaTV3ajc4c3BaOEZiOTA5ZXBlay9nPV92MjAw")
MODAL_API_URL = "https://ykzou1214--tshirt-texture-modal--asgi-app.modal.run"
BLENDER_API_URL = "https://ykzou1214--tshirt-blender-service-apply-texture-to-model.modal.run"

# Global variables for file storage
UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)

def get_weaviate_client():
    """Get Weaviate client connection"""
    return weaviate.connect_to_weaviate_cloud(
        cluster_url=f"https://{WEAVIATE_GRPC_ENDPOINT.replace('grpc-', '')}",
        auth_credentials=wvc.init.Auth.api_key(WEAVIATE_API_KEY)
    )

@app.get("/")
async def root():
    """Health check endpoint"""
    return {"message": "Wiggle Cloth Physics API is running", "version": "1.0.0"}

@app.get("/health")
async def health_check():
    """Detailed health check"""
    try:
        # Test Weaviate connection
        client = get_weaviate_client()
        client.close()
        weaviate_status = "connected"
    except Exception as e:
        weaviate_status = f"error: {str(e)}"
    
    # Test Modal API connection
    try:
        async with httpx.AsyncClient() as http_client:
            response = await http_client.get(f"{MODAL_API_URL}/health", timeout=5.0)
            modal_status = "connected" if response.status_code == 200 else f"error: {response.status_code}"
    except Exception as e:
        modal_status = f"error: {str(e)}"
    
    return {
        "status": "healthy",
        "services": {
            "weaviate": weaviate_status,
            "modal": modal_status
        },
        "timestamp": datetime.now().isoformat()
    }

@app.post("/api/builds/create")
async def create_build_record(
    userId: str = Form(...),
    frontImageUrl: str = Form(default=""),
    backImageUrl: str = Form(default="")
):
    """Create a new build record in Weaviate"""
    try:
        build_id = str(uuid.uuid4())
        
        client = get_weaviate_client()
        collection = client.collections.get("TshirtBuild")
        
        # Create build record
        build_data = {
            "buildId": build_id,
            "userId": userId,
            "frontImageUrl": frontImageUrl,
            "backImageUrl": backImageUrl,
            "status": "pending",
            "createdAt": datetime.now().isoformat(),
            "updatedAt": datetime.now().isoformat()
        }
        
        collection.data.insert(build_data)
        client.close()
        
        logger.info(f"Created build record: {build_id}")
        return {"buildId": build_id, "status": "created"}
        
    except Exception as e:
        logger.error(f"Error creating build record: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to create build record: {str(e)}")

@app.post("/api/builds/update")
async def update_build_record(
    buildId: str = Form(...),
    status: str = Form(default=""),
    textureUrl: str = Form(default=""),
    errorMessage: str = Form(default="")
):
    """Update build record status and details"""
    try:
        client = get_weaviate_client()
        collection = client.collections.get("TshirtBuild")
        
        # Find and update the build record
        response = collection.query.fetch_objects(
            filters=Filter.by_property("buildId").equal(buildId),
            limit=1
        )
        
        if not response.objects:
            client.close()
            raise HTTPException(status_code=404, detail="Build record not found")
        
        # Update the record
        update_data = {
            "status": status,
            "updatedAt": datetime.now().isoformat()
        }
        
        if textureUrl:
            update_data["textureUrl"] = textureUrl
        if errorMessage:
            update_data["errorMessage"] = errorMessage
            
        collection.data.update(
            uuid=response.objects[0].uuid,
            properties=update_data
        )
        
        client.close()
        logger.info(f"Updated build record: {buildId}")
        return {"buildId": buildId, "status": "updated"}
        
    except Exception as e:
        logger.error(f"Error updating build record: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to update build record: {str(e)}")

@app.post("/api/texture/generate")
async def generate_texture(
    background_tasks: BackgroundTasks,
    userId: str = Form(...),
    front: UploadFile = File(...),
    back: UploadFile = File(...)
):
    """
    Generate complete 3D model with texture from front and back images
    This endpoint now handles the full pipeline: texture generation + 3D model creation
    """
    build_id = str(uuid.uuid4())
    temp_files = []
    
    try:
        logger.info(f"Starting complete model generation for user: {userId}, build: {build_id}")
        
        # Step 1: Create build record in Weaviate
        client = get_weaviate_client()
        collection = client.collections.get("TshirtBuild")
        
        build_data = {
            "buildId": build_id,
            "userId": userId,
            "status": "processing",
            "frontImageUrl": f"/api/uploads/{build_id}_front_{front.filename}",
            "backImageUrl": f"/api/uploads/{build_id}_back_{back.filename}",
            "createdAt": datetime.now().isoformat(),
            "updatedAt": datetime.now().isoformat()
        }
        
        collection.data.insert(build_data)
        client.close()
        
        # Step 2: Save uploaded files temporarily
        front_path = UPLOAD_DIR / f"{build_id}_front_{front.filename}"
        back_path = UPLOAD_DIR / f"{build_id}_back_{back.filename}"
        temp_files = [front_path, back_path]
        
        with open(front_path, "wb") as f:
            shutil.copyfileobj(front.file, f)
        with open(back_path, "wb") as f:
            shutil.copyfileobj(back.file, f)
        
        # Step 3: Call Modal API for texture generation
        logger.info(f"Step 1/2: Generating texture using Modal API for build: {build_id}")
        
        texture_data = None
        try:
            async with httpx.AsyncClient(timeout=300.0) as http_client:  # Increased timeout for Modal cold start
                with open(front_path, "rb") as f_front, open(back_path, "rb") as f_back:
                    files = {
                        "front": (front.filename, f_front, front.content_type),
                        "back": (back.filename, f_back, back.content_type)
                    }
                    data = {
                        "style": "preserve"  # Add default style parameter
                    }
                    
                    logger.info(f"Calling Modal API: {MODAL_API_URL}/build-texture")
                    texture_response = await http_client.post(
                        f"{MODAL_API_URL}/build-texture",
                        files=files,
                        data=data
                    )
                    
                    logger.info(f"Modal API response status: {texture_response.status_code}")
            
            if texture_response.status_code != 200:
                error_msg = f"Texture generation failed with status {texture_response.status_code}: {texture_response.text}"
                logger.error(error_msg)
                raise Exception(error_msg)
                
        except httpx.TimeoutException as e:
            error_msg = f"Modal API timeout: {str(e)}"
            logger.error(error_msg)
            raise Exception(error_msg)
        except httpx.RequestError as e:
            error_msg = f"Modal API request error: {str(e)}"
            logger.error(error_msg)
            raise Exception(error_msg)
        except Exception as e:
            error_msg = f"Modal API call failed: {str(e)}"
            logger.error(error_msg)
            raise Exception(error_msg)
        
        texture_data = texture_response.content
        logger.info(f"Texture generated successfully, size: {len(texture_data)} bytes")
        
        # Step 4: Update status to texture_generated
        client = get_weaviate_client()
        collection = client.collections.get("TshirtBuild")
        
        response_query = collection.query.fetch_objects(
            filters=Filter.by_property("buildId").equal(build_id),
            limit=1
        )
        
        if response_query.objects:
            collection.data.update(
                uuid=response_query.objects[0].uuid,
                properties={
                    "status": "texture_generated",
                    "updatedAt": datetime.now().isoformat()
                }
            )
        client.close()
        
        # Step 5: Call Blender Modal function for 3D model generation
        logger.info(f"Step 2/2: Applying texture to 3D model using Blender Modal function for build: {build_id}")
        
        try:
            # Import the Blender app and function directly
            from blender_app import app as blender_app, apply_texture_to_model
            
            logger.info(f"Calling Blender Modal function with texture data ({len(texture_data)} bytes)")
            
            # Call the Modal function with texture data using proper app context
            with blender_app.run():
                model_data = apply_texture_to_model.remote(texture_data)
            
            logger.info(f"Blender Modal function completed successfully, received {len(model_data)} bytes")
                
        except Exception as e:
            error_msg = f"Blender Modal function call failed: {str(e)}"
            logger.error(error_msg)
            raise Exception(error_msg)
        
        # Step 6: Save generated 3D model
        model_filename = f"{build_id}_model.glb"
        model_path = UPLOAD_DIR / model_filename
        temp_files.append(model_path)
        
        with open(model_path, "wb") as f:
            f.write(model_data)
        
        logger.info(f"3D model generated successfully, size: {len(model_data)} bytes")
        
        # Step 7: Update build record with final success
        client = get_weaviate_client()
        collection = client.collections.get("TshirtBuild")
        
        response_query = collection.query.fetch_objects(
            filters=Filter.by_property("buildId").equal(build_id),
            limit=1
        )
        
        if response_query.objects:
            collection.data.update(
                uuid=response_query.objects[0].uuid,
                properties={
                    "status": "completed",
                    "modelUrl": f"/api/model/download/{model_filename}",
                    "updatedAt": datetime.now().isoformat()
                }
            )
        
        client.close()
        
        # Schedule cleanup of temporary files (keep model file for download)
        cleanup_files = [front_path, back_path]  # Don't cleanup model file immediately
        background_tasks.add_task(cleanup_temp_files, cleanup_files)
        
        logger.info(f"Complete model generation finished for build: {build_id}")
        
        return {
            "buildId": build_id,
            "status": "completed",
            "modelUrl": f"/api/model/download/{model_filename}",
            "message": "3D model with texture generated successfully"
        }
        
    except Exception as e:
        logger.error(f"Error in model generation: {str(e)}")
        
        # Update build record with error status
        if build_id:
            try:
                client = get_weaviate_client()
                collection = client.collections.get("TshirtBuild")
                
                response_query = collection.query.fetch_objects(
                    filters=Filter.by_property("buildId").equal(build_id),
                    limit=1
                )
                
                if response_query.objects:
                    collection.data.update(
                        uuid=response_query.objects[0].uuid,
                        properties={
                            "status": "failed",
                            "errorMessage": str(e),
                            "updatedAt": datetime.now().isoformat()
                        }
                    )
                
                client.close()
            except Exception as update_error:
                logger.error(f"Failed to update error status: {str(update_error)}")
        
        # Schedule cleanup of temporary files
        if temp_files:
            background_tasks.add_task(cleanup_temp_files, temp_files)
        
        raise HTTPException(status_code=500, detail=f"Model generation failed: {str(e)}")

@app.get("/api/texture/download/{filename}")
async def download_texture(filename: str):
    """Download generated texture file"""
    file_path = UPLOAD_DIR / filename
    
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Texture file not found")
    
    return FileResponse(
        path=file_path,
        filename=filename,
        media_type="image/png"
    )

@app.get("/api/model/download/{filename}")
async def download_model(filename: str):
    """Download generated 3D model file"""
    file_path = UPLOAD_DIR / filename
    
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Model file not found")
    
    return FileResponse(
        path=file_path,
        filename=filename,
        media_type="model/gltf-binary"
    )

@app.get("/api/builds")
async def get_builds(
    user_id: Optional[str] = None,
    status: Optional[str] = None,
    limit: int = 10,
    offset: int = 0
):
    """Get build records with optional filtering"""
    try:
        client = get_weaviate_client()
        collection = client.collections.get("TshirtBuild")
        
        # Build query filters
        filters = []
        if user_id:
            filters.append(Filter.by_property("userId").equal(user_id))
        if status:
            filters.append(Filter.by_property("status").equal(status))
        
        # Combine filters
        where_filter = None
        if filters:
            where_filter = filters[0]
            for f in filters[1:]:
                where_filter = where_filter & f
        
        # Execute query
        response = collection.query.fetch_objects(
            filters=where_filter,
            limit=min(limit, 100),
            offset=offset
        )
        
        builds = []
        for obj in response.objects:
            build = obj.properties
            build["id"] = str(obj.uuid)
            builds.append(build)
        
        client.close()
        
        return {
            "builds": builds,
            "total": len(builds),
            "limit": limit,
            "offset": offset
        }
        
    except Exception as e:
        logger.error(f"Error fetching builds: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch builds: {str(e)}")

@app.get("/api/builds/{build_id}")
async def get_build(build_id: str):
    """Get specific build record by ID"""
    try:
        client = get_weaviate_client()
        collection = client.collections.get("TshirtBuild")
        
        response = collection.query.fetch_objects(
            filters=Filter.by_property("buildId").equal(build_id),
            limit=1
        )
        
        if not response.objects:
            client.close()
            raise HTTPException(status_code=404, detail="Build not found")
        
        build = response.objects[0].properties
        build["id"] = str(response.objects[0].uuid)
        
        client.close()
        return build
        
    except Exception as e:
        logger.error(f"Error fetching build {build_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch build: {str(e)}")

async def cleanup_temp_files(file_paths: List[Path]):
    """Background task to clean up temporary files"""
    for file_path in file_paths:
        try:
            if file_path.exists():
                file_path.unlink()
                logger.info(f"Cleaned up temp file: {file_path}")
        except Exception as e:
            logger.error(f"Failed to cleanup {file_path}: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)