# Wiggle Backend

AI-powered T-shirt texture generation and 3D modeling service with multiple deployment options.

## Architecture

```
Frontend → Backend API → Modal Cloud → Texture + 3D Model
                ↓
         Weaviate Database
```

- **`modal_integrated_deploy.py`**: Main Modal deployment with texture generation and 3D modeling
- **`direct_api.py`**: Local FastAPI server for development
- **`weaviate_*.py`**: Database utilities and helpers
- **`n8n_workflow.json`**: N8N automation workflow

---

## 1. Current Deployments ✅

### Main Integrated API (Recommended)
```
https://ykzou1214--wiggle-integrated-api-fastapi-app.modal.run
```

**Endpoints:**
- `POST /api/texture/generate` - Generate texture and 3D model
- `GET /api/texture/download/{filename}` - Download texture
- `GET /api/model/download/{filename}` - Download 3D model
- `GET /health` - Health check

### Redeploy (if needed)
```bash
modal deploy modal_integrated_deploy.py
```

### View Deployment
https://modal.com/apps/ykzou1214/main/deployed/wiggle-integrated-api

---

## 2. Test Integrated API

### Quick Test - Complete Pipeline

**Generate texture and 3D model**:
```bash
curl -X POST "https://ykzou1214--wiggle-integrated-api-fastapi-app.modal.run/api/texture/generate" \
  -F "userId=test_user" \
  -F "front=@../../front.png" \
  -F "back=@../../back.png"
```

**Download generated files**:
```bash
# Download 3D model (OBJ format)
curl -o model.glb "https://ykzou1214--wiggle-integrated-api-fastapi-app.modal.run/api/model/download/model_id.glb"

# Download texture
curl -o texture.png "https://ykzou1214--wiggle-integrated-api-fastapi-app.modal.run/api/texture/download/texture_id.png"
```

### Local Development Server

**Start local API server**:
```bash
python run_direct_api.py
```

**Test local server**:
```bash
curl -X POST "http://localhost:5001/api/texture/generate" \
  -F "userId=test_user" \
  -F "front=@../../front.png" \
  -F "back=@../../back.png"
```

---

## 3. Configure n8n Workflow

In your n8n workflow, update the **"HTTP Request - Build Texture"** node:

- **URL**: `https://ykzou1214--tshirt-texture-modal--asgi-app.modal.run/build-texture`
- **Method**: POST
- **Send Body**: Yes
- **Body Content Type**: Form-Data Multipart
- **Specify Body**: Using Fields
- **Body Parameters**:
  - Name: `front`, Value: `={{ $binary.front }}`
  - Name: `back`, Value: `={{ $binary.back }}`

---

## 4. Test Complete Workflow (n8n → Modal)

### Run Full Pipeline Test

**Test mode (n8n editor)**:
```bash
uv run test_n8n_workflow.py --front ../../front.png --back ../../back.png
```

**Production mode**:
```bash
uv run test_n8n_workflow.py --front ../../front.png --back ../../back.png --production
```

**Custom output filename**:
```bash
uv run test_n8n_workflow.py --front ../../front.png --back ../../back.png --out my_texture.png
```

This will:
1. Send images to your n8n webhook
2. n8n forwards to Modal API  
3. Modal generates texture
4. Returns `texture.png`

### Legacy Test Script
```bash
uv run test_webhook.py --front ../../front.png --back ../../back.png
```

---

## API Details

### Main Endpoint: `POST /api/texture/generate`

**Parameters**:
- `userId` (string): Unique user identifier
- `front` (file): Front T-shirt image
- `back` (file): Back T-shirt image

**Response**: JSON with download URLs
```json
{
  "status": "completed",
  "buildId": "uuid-here",
  "modelUrl": "/api/model/download/model_uuid.glb",
  "textureUrl": "/api/texture/download/texture_uuid.png",
  "message": "3D model with texture generated successfully"
}
```

### Download Endpoints:
- `GET /api/texture/download/{filename}` - Download generated texture (PNG, 1024x1024)
- `GET /api/model/download/{filename}` - Download 3D model (OBJ format)

**Features**:
- ✅ Automatic background removal (rembg)
- ✅ AI-powered texture generation
- ✅ 3D T-shirt model creation with Blender
- ✅ Seamless texture application
- ✅ Cloud storage and retrieval
- ✅ Weaviate database integration

---

## Files

### Core Files
- **`modal_integrated_deploy.py`**: Main Modal deployment with texture generation and 3D modeling
- **`direct_api.py`**: Local FastAPI server for development
- **`run_direct_api.py`**: Script to run local development server
- **`n8n_workflow.json`**: N8N workflow configuration for automation

### Database & Utilities
- **`weaviate_api.py`**: Weaviate database API utilities
- **`weaviate_schema.py`**: Database schema definitions
- **`weaviate_n8n_helper.py`**: N8N integration helper
- **`app.py`**: Legacy texture-only Modal service
- **`apply_texture_to_model.py`**: 3D model texture application utility

### Configuration
- **`pyproject.toml`**: Python dependencies
- **`requirements_direct_api.txt`**: Direct API dependencies
- **Sample images**: `../../front.png`, `../../back.png`

---

## Summary

✅ **Integrated API deployed**: https://ykzou1214--wiggle-integrated-api-fastapi-app.modal.run

✅ **Features**:
- Complete texture generation pipeline
- 3D T-shirt model creation with Blender
- Automatic background removal
- Cloud storage and file management
- Weaviate database integration
- N8N workflow automation support

✅ **Testing**:
```bash
# Test complete pipeline
curl -X POST "https://ykzou1214--wiggle-integrated-api-fastapi-app.modal.run/api/texture/generate" \
  -F "userId=test_user" \
  -F "front=@../../front.png" \
  -F "back=@../../back.png"

# Local development
python run_direct_api.py
```

✅ **Deployment Options**:
- **Production**: Modal cloud deployment (recommended)
- **Development**: Local FastAPI server
- **Automation**: N8N workflow integration
