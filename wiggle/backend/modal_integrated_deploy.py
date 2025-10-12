#!/usr/bin/env python3

import modal
import os
from pathlib import Path

app = modal.App("wiggle-integrated-api")

# Create comprehensive image with all dependencies including Blender
image = modal.Image.debian_slim(python_version="3.12").apt_install(
    "blender", "wget"
).pip_install([
    "fastapi",
    "uvicorn[standard]",
    "python-multipart", 
    "httpx",
    "weaviate-client",
    "python-dotenv",
    "Pillow",
    "aiofiles",
    "rembg",
    "numpy",
    "opencv-python-headless"
])

# Environment secrets
secrets = modal.Secret.from_dict({
    "WEAVIATE_GRPC_ENDPOINT": "grpc-aoj6v69aspmruwn6zlgma.c0.europe-west3.gcp.weaviate.cloud",
    "WEAVIATE_API_KEY": "N08rcE1Ua0pJTlB1RVh0cF9XeEJjMVRGZE5MdjF1YkpqanZKc1RHaTV3ajc4c3BaOEZiOTA5ZXBlay9nPV92MjAw",
    "MODAL_API_URL": "https://ykzou1214--tshirt-texture-modal--asgi-app.modal.run"
})

# Storage volume
volume = modal.Volume.from_name("wiggle-storage", create_if_missing=True)
blender_volume = modal.Volume.from_name("tshirt-models", create_if_missing=True)

def apply_texture_with_blender(texture_png_data: bytes) -> bytes:
    """
    Apply texture to 3D model using Blender (integrated function)
    
    Args:
        texture_png_data: Binary data of texture PNG
    
    Returns: Binary data of model_textured.glb
    """
    import tempfile
    import subprocess
    
    # 1. Setup file paths
    with tempfile.TemporaryDirectory() as tmpdir:
        # Save incoming texture data to temporary file
        texture_path = f"{tmpdir}/texture.png"
        with open(texture_path, "wb") as f:
            f.write(texture_png_data)
        
        output_path = f"{tmpdir}/model_textured.glb"
        
        # 2. Create improved Blender script
        blender_script_path = f"{tmpdir}/apply_texture_script.py"
        
        # Simple and compatible Blender script
        blender_script_content = '''
import bpy
import sys
import os

print("Starting Blender script...")

# Parse command line arguments
argv = sys.argv
argv = argv[argv.index("--") + 1:]  # Get all args after "--"

if len(argv) < 2:
    print("Usage: blender --background --python script.py -- <texture_path> <output_path>")
    sys.exit(1)

texture_path = argv[0]
output_path = argv[1]

print(f"Texture path: {texture_path}")
print(f"Output path: {output_path}")

try:
    # Clear existing mesh objects
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.delete(use_global=False)
    print("Cleared existing objects")

    # Create a simple cube (T-shirt placeholder)
    bpy.ops.mesh.primitive_cube_add(size=2)
    obj = bpy.context.active_object
    obj.name = "TShirt"
    
    # Scale the object to make it more T-shirt like (simple scaling)
    obj.scale[0] = 1.2  # X scale
    obj.scale[1] = 0.1  # Y scale (thin)
    obj.scale[2] = 1.5  # Z scale
    
    print(f"Created and scaled T-shirt object: {obj.name}")

    # Create UV mapping using simple unwrap
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.uv.unwrap()
    bpy.ops.object.mode_set(mode='OBJECT')
    print("Created UV mapping")

    # Create a simple material
    material = bpy.data.materials.new(name="TShirtMaterial")
    material.use_nodes = True
    print("Created material")

    # Assign material to object
    if len(obj.data.materials) == 0:
        obj.data.materials.append(material)
    else:
        obj.data.materials[0] = material

    # Setup material nodes (simplified)
    try:
        nodes = material.node_tree.nodes
        links = material.node_tree.links
        
        # Get the default Principled BSDF node
        bsdf = None
        for node in nodes:
            if node.type == 'BSDF_PRINCIPLED':
                bsdf = node
                break
        
        if not bsdf:
            bsdf = nodes.new(type='ShaderNodeBsdfPrincipled')
        
        # Add texture node
        tex_node = nodes.new(type='ShaderNodeTexImage')
        tex_node.location = (-300, 0)
        
        # Load texture image
        if os.path.exists(texture_path):
            texture_image = bpy.data.images.load(texture_path)
            tex_node.image = texture_image
            print("Loaded texture image")
            
            # Link texture to base color
            links.new(tex_node.outputs['Color'], bsdf.inputs['Base Color'])
            print("Linked texture to material")
        else:
            print(f"Warning: Texture file not found at {texture_path}")
        
    except Exception as e:
        print(f"Warning: Could not setup material: {e}")

    # Export as OBJ file (simpler format)
    print(f"Exporting OBJ to: {output_path}")
    try:
        # Select only our object
        bpy.ops.object.select_all(action='DESELECT')
        obj.select_set(True)
        bpy.context.view_layer.objects.active = obj
        
        # Change output path to .obj
        obj_path = output_path.replace('.glb', '.obj')
        
        # Export using OBJ exporter (more reliable)
        bpy.ops.export_scene.obj(
            filepath=obj_path,
            use_selection=True,
            use_materials=True,
            use_uvs=True
        )
        print("OBJ export completed")
        
        # Check if file was created
        if os.path.exists(obj_path):
            file_size = os.path.getsize(obj_path)
            print(f"OBJ file created: {file_size} bytes")
            
            # Copy to expected GLB path for compatibility
            import shutil
            shutil.copy2(obj_path, output_path)
            print(f"Copied to GLB path: {output_path}")
        else:
            print("Error: OBJ file was not created")
            
    except Exception as e:
        print(f"OBJ export failed: {e}")
        import traceback
        traceback.print_exc()
            
except Exception as e:
    print(f"Error in Blender script: {e}")
    import traceback
    traceback.print_exc()

print("Blender script completed")
'''
        
        # 3. Write Blender script to file
        with open(blender_script_path, "w") as f:
            f.write(blender_script_content)
        
        # 4. Run Blender with the script
        print(f"Running Blender with script...")
        
        try:
            result = subprocess.run([
                "blender", "--background", "--python", blender_script_path, "--",
                texture_path, output_path
            ], capture_output=True, text=True, timeout=300)
            
            print(f"Blender stdout: {result.stdout}")
            if result.stderr:
                print(f"Blender stderr: {result.stderr}")
                
        except subprocess.TimeoutExpired:
            print("Blender process timed out")
        except Exception as e:
            print(f"Error running Blender: {e}")
        
        # 5. Read output file
        if os.path.exists(output_path):
            with open(output_path, "rb") as f:
                model_data = f.read()
            print(f"Successfully generated model: {len(model_data)} bytes")
            return model_data
        else:
            error_msg = f"Output file not found at {output_path}. Blender stdout: {result.stdout if 'result' in locals() else 'N/A'}, stderr: {result.stderr if 'result' in locals() else 'N/A'}"
            print(error_msg)
            raise Exception(error_msg)

@app.function(
    image=image,
    secrets=[secrets],
    volumes={"/storage": volume, "/blender_assets": blender_volume},
    timeout=600
)
@modal.asgi_app()
def fastapi_app():
    from fastapi import FastAPI, UploadFile, File, Form, HTTPException
    from fastapi.middleware.cors import CORSMiddleware
    from fastapi.responses import FileResponse
    import httpx
    import asyncio
    import logging
    import uuid
    from datetime import datetime
    import weaviate
    from weaviate.classes.init import Auth
    
    # Setup logging
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)
    
    app = FastAPI(title="Wiggle Complete API", version="1.0.0")
    
    # Add CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    def get_weaviate_client():
        """Get Weaviate client"""
        try:
            weaviate_endpoint = os.getenv("WEAVIATE_GRPC_ENDPOINT")
            weaviate_api_key = os.getenv("WEAVIATE_API_KEY")
            
            if not weaviate_endpoint or not weaviate_api_key:
                logger.warning("Weaviate credentials not found")
                return None
                
            client = weaviate.connect_to_weaviate_cloud(
                cluster_url=f"https://{weaviate_endpoint.replace('grpc-', '').replace(':443', '')}",
                auth_credentials=Auth.api_key(weaviate_api_key)
            )
            return client
        except Exception as e:
            logger.error(f"Failed to connect to Weaviate: {e}")
            return None
    
    @app.get("/")
    async def root():
        return {"message": "Wiggle Complete API", "status": "running"}
    
    @app.get("/health")
    async def health_check():
        """Health check endpoint"""
        client_db = get_weaviate_client()
        weaviate_status = "connected" if client_db else "disconnected"
        if client_db:
            client_db.close()
        
        return {
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "services": {
                "weaviate": weaviate_status,
                "modal_api": os.getenv("MODAL_API_URL", "not_configured"),
                "blender": "integrated"
            }
        }
    
    @app.post("/api/texture/generate")
    async def generate_texture_and_model(
        userId: str = Form(...),
        front: UploadFile = File(...),
        back: UploadFile = File(...)
    ):
        """Generate texture and 3D model from front and back images"""
        build_id = str(uuid.uuid4())
        logger.info(f"Starting texture/model generation for user: {userId}, build: {build_id}")
        
        try:
            # Create build record
            client_db = get_weaviate_client()
            if client_db:
                builds = client_db.collections.get("Build")
                builds.data.insert({
                    "buildId": build_id,
                    "userId": userId,
                    "status": "processing",
                    "createdAt": datetime.now().isoformat()
                })
                client_db.close()
            
            # Save uploaded files
            front_path = f"/storage/front_{build_id}.png"
            back_path = f"/storage/back_{build_id}.png"
            
            with open(front_path, "wb") as f:
                f.write(await front.read())
            with open(back_path, "wb") as f:
                f.write(await back.read())
            
            logger.info(f"Saved uploaded files for build: {build_id}")
            
            # Call texture generation API
            modal_api_url = os.getenv("MODAL_API_URL")
            if not modal_api_url:
                raise Exception("MODAL_API_URL not configured")
            
            async with httpx.AsyncClient(timeout=300.0) as client_http:
                with open(front_path, "rb") as f1, open(back_path, "rb") as f2:
                    files = {
                        "front": ("front.png", f1, "image/png"),
                        "back": ("back.png", f2, "image/png")
                    }
                    data = {"userId": userId}
                    
                    response = await client_http.post(
                        f"{modal_api_url}/build-texture",
                        files=files,
                        data=data
                    )
                    
                    if response.status_code != 200:
                        raise Exception(f"Texture generation failed: {response.text}")
                    
                    # Save texture directly from response content
                    texture_path = f"/storage/texture_{build_id}.png"
                    with open(texture_path, "wb") as f:
                        f.write(response.content)
                    logger.info(f"Texture saved to {texture_path}")
                    
                    # Create texture URL for response
                    texture_url = f"/api/download/{build_id}/texture_{build_id}.png"
            
            # Apply texture using integrated Blender function
            logger.info(f"Applying texture to 3D model using integrated Blender")
            
            # Read texture data
            with open(texture_path, "rb") as f:
                texture_data = f.read()
            
            logger.info(f"Calling integrated Blender function with texture data ({len(texture_data)} bytes)")
            
            # Call the integrated Blender function
            model_data = apply_texture_with_blender(texture_data)
            
            logger.info(f"Blender processing completed successfully, received {len(model_data)} bytes")
            
            # Save the GLB model
            model_filename = f"model_{build_id}.glb"
            model_path = f"/storage/{model_filename}"
            
            with open(model_path, "wb") as f:
                f.write(model_data)
            
            logger.info(f"3D model saved to {model_path}")
            
            # Update build record with success
            client_db = get_weaviate_client()
            if client_db:
                builds = client_db.collections.get("Build")
                builds.data.insert({
                    "buildId": build_id,
                    "userId": userId,
                    "status": "completed",
                    "frontImageUrl": f"/api/texture/download/front_{build_id}.png",
                    "backImageUrl": f"/api/texture/download/back_{build_id}.png",
                    "textureUrl": f"/api/texture/download/texture_{build_id}.png",
                    "modelUrl": f"/api/model/download/{model_filename}",
                    "createdAt": datetime.now().isoformat(),
                    "completedAt": datetime.now().isoformat()
                })
                client_db.close()
            
            return {
                "status": "completed",
                "buildId": build_id,
                "modelUrl": f"/api/model/download/{model_filename}",
                "textureUrl": f"/api/texture/download/texture_{build_id}.png",
                "message": "3D model with texture generated successfully"
            }
            
        except Exception as e:
            logger.error(f"Error in texture/model generation: {e}")
            
            # Update build record with error
            client_db = get_weaviate_client()
            if client_db:
                builds = client_db.collections.get("Build")
                builds.data.insert({
                    "buildId": build_id,
                    "userId": userId,
                    "status": "failed",
                    "error": str(e),
                    "createdAt": datetime.now().isoformat(),
                    "failedAt": datetime.now().isoformat()
                })
                client_db.close()
            
            return {
                "status": "failed",
                "buildId": build_id,
                "error": "Model generation failed",
                "details": str(e)
            }
    
    @app.get("/api/model/download/{filename}")
    async def download_model(filename: str):
        """Download generated 3D model file"""
        file_path = f"/storage/{filename}"
        
        if not os.path.exists(file_path):
            raise HTTPException(status_code=404, detail="Model file not found")
        
        return FileResponse(
            path=file_path,
            filename=filename,
            media_type="model/gltf-binary"
        )
    
    @app.get("/api/texture/download/{filename}")
    async def download_texture(filename: str):
        """Download texture file"""
        file_path = f"/storage/{filename}"
        
        if not os.path.exists(file_path):
            raise HTTPException(status_code=404, detail="Texture file not found")
        
        return FileResponse(
            path=file_path,
            filename=filename,
            media_type="image/png"
        )
    
    return app

@app.function(image=image, secrets=[secrets])
def health_check_modal():
    """Modal health check function"""
    return {"status": "healthy", "service": "wiggle-integrated-api"}

@app.local_entrypoint()
def main():
    """Deploy the integrated app"""
    print("Deploying Wiggle Integrated API...")

if __name__ == "__main__":
    main()