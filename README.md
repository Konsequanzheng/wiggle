# Wiggly - AI-Powered 3D Interactive Animation Design Platform

Wiggle is an innovative platform that transforms user-uploaded images into custom T-shirt designs with AI-generated textures and 3D models. The platform combines computer vision, AI texture generation, and 3D modeling to create personalized apparel.

## 🚀 Features

- **AI Texture Generation**: Upload front and back images to generate seamless T-shirt textures
- **3D Model Creation**: Automatically generate 3D T-shirt models with applied textures
- **Real-time Processing**: Fast texture and model generation using Modal cloud infrastructure
- **Multiple Deployment Options**: Support for both direct API and n8n workflow integration
- **Cloud-Native Architecture**: Scalable deployment on Modal with Weaviate vector database

## 🏗️ Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Frontend      │    │   Backend API   │    │  Modal Cloud    │
│   (Next.js)     │◄──►│   (FastAPI)     │◄──►│   (Blender +    │
│                 │    │                 │    │    AI Models)   │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                              │
                              ▼
                       ┌─────────────────┐
                       │   Weaviate DB   │
                       │  (Vector Store) │
                       └─────────────────┘
```

## 📁 Project Structure

```
├── frontend/                 # Next.js frontend application
│   ├── src/
│   │   ├── app/             # App router pages
│   │   └── components/      # React components
│   └── public/              # Static assets
├── wiggle/
│   ├── backend/             # Backend API and services
│   │   ├── modal_integrated_deploy.py  # Main Modal deployment
│   │   ├── direct_api.py               # Direct API server
│   │   ├── weaviate_*.py              # Database utilities
│   │   ├── n8n_workflow.json          # N8N automation workflow
│   │   └── README.md                  # Backend documentation
│   └── frontend/            # Alternative frontend (if needed)
├── front.png               # Sample front image
├── back.png                # Sample back image
└── README.md               # This file
```

## 🛠️ Technology Stack

### Frontend
- **Next.js 14** - React framework with App Router
- **TypeScript** - Type-safe development
- **Tailwind CSS** - Utility-first styling
- **Three.js** - 3D model rendering

### Backend
- **FastAPI** - High-performance Python web framework
- **Modal** - Serverless cloud platform for AI workloads
- **Blender** - 3D modeling and texture application
- **Weaviate** - Vector database for AI embeddings
- **N8N** - Workflow automation platform

### AI/ML
- **Computer Vision** - Image processing and analysis
- **Texture Synthesis** - AI-powered texture generation
- **3D Modeling** - Automated T-shirt model creation

## 🚀 Quick Start

### Prerequisites
- Node.js 18+ and npm/bun
- Python 3.12+
- Modal account and CLI
- Weaviate cloud instance

### 1. Frontend Setup
```bash
cd frontend
npm install
npm run dev
```
The frontend will be available at `http://localhost:3000`

### 2. Backend Setup

#### Option A: Modal Cloud Deployment (Recommended)
```bash
cd wiggle/backend
pip install modal
modal token new
modal deploy modal_integrated_deploy.py
```

#### Option B: Local Development
```bash
cd wiggle/backend
pip install -r requirements_direct_api.txt
python run_direct_api.py
```

### 3. Environment Configuration
Create `.env` files with the following variables:
```env
WEAVIATE_GRPC_ENDPOINT=your_weaviate_endpoint
WEAVIATE_API_KEY=your_weaviate_key
MODAL_API_URL=your_modal_deployment_url
```

## 📡 API Endpoints

### Main API (Modal Deployment)
- **Base URL**: `https://ykzou1214--wiggle-integrated-api-fastapi-app.modal.run`

#### Endpoints:
- `POST /api/texture/generate` - Generate texture and 3D model
- `GET /api/texture/download/{filename}` - Download generated texture
- `GET /api/model/download/{filename}` - Download 3D model
- `GET /health` - Health check

#### Example Usage:
```bash
curl -X POST "https://ykzou1214--wiggle-integrated-api-fastapi-app.modal.run/api/texture/generate" \
  -F "userId=user123" \
  -F "front=@front.png" \
  -F "back=@back.png"
```

Response:
```json
{
  "status": "completed",
  "buildId": "uuid-here",
  "modelUrl": "/api/model/download/model_uuid.glb",
  "textureUrl": "/api/texture/download/texture_uuid.png",
  "message": "3D model with texture generated successfully"
}
```

## 🔄 N8N Workflow Integration

The project includes a pre-configured N8N workflow for automation:

- **File**: `wiggle/backend/n8n_workflow.json`
- **Features**: Automated texture generation, webhook integration, database storage
- **Setup**: Import the JSON file into your N8N instance

## 🧪 Testing

### Test the Complete Pipeline:
```bash
# Test texture generation
curl -X POST "https://your-modal-url/api/texture/generate" \
  -F "userId=test_user" \
  -F "front=@front.png" \
  -F "back=@back.png"

# Download generated files
curl -o model.glb "https://your-modal-url/api/model/download/model_id.glb"
curl -o texture.png "https://your-modal-url/api/texture/download/texture_id.png"
```

## 📊 Performance

- **Texture Generation**: ~30-60 seconds
- **3D Model Creation**: ~10-20 seconds
- **File Sizes**: 
  - Textures: ~200KB PNG
  - Models: ~1KB OBJ format
- **Concurrent Users**: Scales automatically with Modal

## 🔧 Development

### Local Development Setup:
```bash
# Backend
cd wiggle/backend
python -m venv venv
source venv/bin/activate  # or `venv\Scripts\activate` on Windows
pip install -r requirements_direct_api.txt
python run_direct_api.py

# Frontend
cd frontend
npm install
npm run dev
```

### Deployment:
```bash
# Deploy to Modal
modal deploy modal_integrated_deploy.py

# Build frontend
npm run build
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🆘 Support

For support and questions:
- Check the [Backend README](wiggle/backend/README.md) for detailed setup instructions
- Review the [N8N Deployment Guide](wiggle/backend/N8N_DEPLOYMENT_GUIDE.md)
- Open an issue on GitHub

## 🎯 Roadmap

- [ ] Support for additional garment types
- [ ] Advanced texture customization options
- [ ] Real-time 3D preview
- [ ] Mobile app development
- [ ] Marketplace integration

---

Built with ❤️ for the Big Berlin Hackathon
