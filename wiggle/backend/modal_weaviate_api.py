"""Modal deployment script for Weaviate n8n Helper API

This script deploys the Weaviate n8n integration API to Modal,
making it accessible from cloud n8n instances without needing ngrok or local hosting.

Deploy with: modal deploy modal_weaviate_api.py
"""

import modal
import os
from datetime import datetime

# Create Modal app
app = modal.App("weaviate-api")

# Define the image with required dependencies
image = modal.Image.debian_slim().pip_install(
    "flask",
    "weaviate-client==4.17.0",
    "flask-cors"
)

# Weaviate Cloud credentials (set as Modal secrets)
WEAVIATE_GRPC_ENDPOINT = os.getenv("WEAVIATE_GRPC_ENDPOINT", "weaviate-6rnhd.weaviate.network:443")
WEAVIATE_API_KEY = os.getenv("WEAVIATE_API_KEY", "")

@app.function(
    image=image,
    secrets=[modal.Secret.from_name("weaviate-credentials")],  # You need to create this secret in Modal
)
@modal.asgi_app()
def asgi_app():
    from flask import Flask, request, jsonify
    from flask_cors import CORS
    import weaviate
    import weaviate.classes as wvc
    import uuid
    
    app = Flask(__name__)
    CORS(app)
    
    def get_weaviate_client():
        """Create and return a Weaviate client"""
        return weaviate.connect_to_weaviate_cloud(
            cluster_url=WEAVIATE_GRPC_ENDPOINT,
            auth_credentials=wvc.init.Auth.api_key(WEAVIATE_API_KEY)
        )
    
    @app.route('/health', methods=['GET'])
    def health_check():
        """Health check endpoint"""
        return jsonify({
            "status": "healthy",
            "service": "Weaviate n8n Helper API",
            "timestamp": datetime.utcnow().isoformat()
        })
    
    @app.route('/api/builds/create', methods=['POST'])
    def create_build():
        """Create a new T-shirt build record in Weaviate"""
        try:
            data = request.json
            
            # Validate required fields
            required_fields = ['userId', 'frontImageUrl', 'backImageUrl']
            for field in required_fields:
                if field not in data:
                    return jsonify({"error": f"Missing required field: {field}"}), 400
            
            client = get_weaviate_client()
            try:
                collection = client.collections.get("TshirtBuild")
                
                # Generate unique build ID
                build_id = str(uuid.uuid4())
                
                # Create build record
                result = collection.data.insert(
                    properties={
                        "buildId": build_id,
                        "userId": data['userId'],
                        "timestamp": datetime.utcnow().isoformat(),
                        "frontImageUrl": data['frontImageUrl'],
                        "backImageUrl": data['backImageUrl'],
                        "status": "initialized"
                    }
                )
                
                return jsonify({
                    "success": True,
                    "buildId": build_id,
                    "uuid": str(result)
                }), 201
            finally:
                client.close()
                
        except Exception as e:
            return jsonify({"error": str(e)}), 500
    
    @app.route('/api/builds/update', methods=['POST'])
    def update_build():
        """Update a build record with texture URL and status"""
        try:
            data = request.json
            
            # Validate required fields
            if 'buildId' not in data:
                return jsonify({"error": "Missing required field: buildId"}), 400
            
            client = get_weaviate_client()
            try:
                collection = client.collections.get("TshirtBuild")
                
                # Find the build by buildId
                response = collection.query.fetch_objects(
                    filters=wvc.query.Filter.by_property("buildId").equal(data['buildId']),
                    limit=1
                )
                
                if not response.objects:
                    return jsonify({"error": "Build not found"}), 404
                
                build_uuid = response.objects[0].uuid
                
                # Prepare update properties
                update_props = {}
                if 'textureUrl' in data:
                    update_props['textureUrl'] = data['textureUrl']
                if 'status' in data:
                    update_props['status'] = data['status']
                
                # Update the build
                collection.data.update(
                    uuid=build_uuid,
                    properties=update_props
                )
                
                return jsonify({
                    "success": True,
                    "buildId": data['buildId'],
                    "updated": update_props
                })
            finally:
                client.close()
                
        except Exception as e:
            return jsonify({"error": str(e)}), 500
    
    @app.route('/api/builds/complete', methods=['POST'])
    def complete_build():
        """Mark a build as complete with model URL"""
        try:
            data = request.json
            
            # Validate required fields
            required_fields = ['buildId', 'modelUrl']
            for field in required_fields:
                if field not in data:
                    return jsonify({"error": f"Missing required field: {field}"}), 400
            
            client = get_weaviate_client()
            try:
                collection = client.collections.get("TshirtBuild")
                
                # Find the build by buildId
                response = collection.query.fetch_objects(
                    filters=wvc.query.Filter.by_property("buildId").equal(data['buildId']),
                    limit=1
                )
                
                if not response.objects:
                    return jsonify({"error": "Build not found"}), 404
                
                build_uuid = response.objects[0].uuid
                build = response.objects[0].properties
                
                # Calculate processing time if we have the timestamp
                processing_time = None
                if 'timestamp' in build:
                    try:
                        start_time = datetime.fromisoformat(build['timestamp'].replace('Z', '+00:00'))
                        end_time = datetime.utcnow()
                        processing_time = int((end_time - start_time).total_seconds() * 1000)
                    except:
                        pass
                
                # Update the build
                update_props = {
                    'modelUrl': data['modelUrl'],
                    'status': 'completed'
                }
                if processing_time is not None:
                    update_props['processingTimeMs'] = processing_time
                
                collection.data.update(
                    uuid=build_uuid,
                    properties=update_props
                )
                
                return jsonify({
                    "success": True,
                    "buildId": data['buildId'],
                    "status": "completed",
                    "processingTimeMs": processing_time
                })
            finally:
                client.close()
                
        except Exception as e:
            return jsonify({"error": str(e)}), 500
    
    @app.route('/api/builds/<build_id>', methods=['GET'])
    def get_build(build_id):
        """Get a build by ID"""
        try:
            client = get_weaviate_client()
            try:
                collection = client.collections.get("TshirtBuild")
                
                response = collection.query.fetch_objects(
                    filters=wvc.query.Filter.by_property("buildId").equal(build_id),
                    limit=1
                )
                
                if not response.objects:
                    return jsonify({"error": "Build not found"}), 404
                
                build = response.objects[0].properties
                return jsonify(build)
            finally:
                client.close()
                
        except Exception as e:
            return jsonify({"error": str(e)}), 500
    
    @app.route('/api/builds', methods=['GET'])
    def list_builds():
        """List all builds (with optional user filter)"""
        try:
            user_id = request.args.get('userId')
            limit = int(request.args.get('limit', 10))
            
            client = get_weaviate_client()
            try:
                collection = client.collections.get("TshirtBuild")
                
                if user_id:
                    response = collection.query.fetch_objects(
                        filters=wvc.query.Filter.by_property("userId").equal(user_id),
                        limit=limit
                    )
                else:
                    response = collection.query.fetch_objects(limit=limit)
                
                builds = [obj.properties for obj in response.objects]
                return jsonify({
                    "builds": builds,
                    "count": len(builds)
                })
            finally:
                client.close()
                
        except Exception as e:
            return jsonify({"error": str(e)}), 500
    
    return app