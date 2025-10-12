"""Weaviate n8n集成辅助函数

提供简单的函数供n8n的Code节点调用，用于:
- 创建构建记录
- 更新构建状态
- 查询构建记录

在n8n的Code节点中使用:
```javascript
const response = await $http.request({
  method: 'POST',
  url: 'http://localhost:5001/api/builds/create',
  body: {
    buildId: $json.build_id,
    userId: $json.user_id,
    frontImageUrl: $json.front_url,
    backImageUrl: $json.back_url
  }
});
```
"""

from flask import Flask, jsonify, request
import weaviate
import weaviate.classes as wvc
from datetime import datetime
import uuid
import os

app = Flask(__name__)

# Weaviate配置
WEAVIATE_GRPC_ENDPOINT = os.getenv("WEAVIATE_GRPC_ENDPOINT", "grpc-aoj6v69aspmruwn6zlgma.c0.europe-west3.gcp.weaviate.cloud")
WEAVIATE_API_KEY = os.getenv("WEAVIATE_API_KEY", "N08rcE1Ua0pJTlB1RVh0cF9XeEJjMVRGZE5MdjF1YkpqanZKc1RHaTV3ajc4c3BaOEZiOTA5ZXBlay9nPV92MjAw")

def get_weaviate_client():
    """获取Weaviate客户端"""
    return weaviate.connect_to_weaviate_cloud(
        cluster_url=f"https://{WEAVIATE_GRPC_ENDPOINT.replace('grpc-', '')}",
        auth_credentials=wvc.init.Auth.api_key(WEAVIATE_API_KEY)
    )

@app.route('/api/builds/create', methods=['POST'])
def create_build():
    """创建新的构建记录
    
    Body:
    {
        "buildId": "build_123",  # 可选，不提供则自动生成
        "userId": "user_001",
        "frontImageUrl": "https://...",
        "backImageUrl": "https://..."
    }
    """
    data = request.json
    
    # 验证必需字段
    if not data.get('userId'):
        return jsonify({
            'success': False,
            'error': 'userId is required'
        }), 400
    
    if not data.get('frontImageUrl') or not data.get('backImageUrl'):
        return jsonify({
            'success': False,
            'error': 'frontImageUrl and backImageUrl are required'
        }), 400
    
    try:
        client = get_weaviate_client()
        collection = client.collections.get("TshirtBuild")
        
        # 生成buildId（如果未提供）
        build_id = data.get('buildId', f"build_{uuid.uuid4().hex[:12]}")
        
        # 构建数据对象
        build_data = {
            "buildId": build_id,
            "userId": data['userId'],
            "timestamp": datetime.now(),
            "frontImageUrl": data['frontImageUrl'],
            "backImageUrl": data['backImageUrl'],
            "textureUrl": None,
            "modelUrl": None,
            "status": "pending",
            "processingTimeMs": None,
            "errorMessage": None
        }
        
        # 插入数据
        obj_uuid = collection.data.insert(build_data)
        
        client.close()
        
        return jsonify({
            'success': True,
            'data': {
                'uuid': str(obj_uuid),
                'buildId': build_id,
                'status': 'pending'
            }
        }), 201
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/builds/update', methods=['POST'])
def update_build():
    """更新构建状态
    
    Body:
    {
        "buildId": "build_123",
        "status": "completed",  # 可选
        "textureUrl": "https://...",  # 可选
        "modelUrl": "https://...",  # 可选
        "processingTimeMs": 3500,  # 可选
        "errorMessage": "error details"  # 可选
    }
    """
    data = request.json
    build_id = data.get('buildId')
    
    if not build_id:
        return jsonify({
            'success': False,
            'error': 'buildId is required'
        }), 400
    
    try:
        client = get_weaviate_client()
        collection = client.collections.get("TshirtBuild")
        
        # 查找对象
        result = collection.query.fetch_objects(
            filters=wvc.query.Filter.by_property("buildId").equal(build_id),
            limit=1
        )
        
        if not result.objects:
            client.close()
            return jsonify({
                'success': False,
                'error': 'Build not found'
            }), 404
        
        obj_uuid = result.objects[0].uuid
        
        # 构建更新数据
        update_data = {}
        if 'status' in data:
            update_data['status'] = data['status']
        if 'textureUrl' in data:
            update_data['textureUrl'] = data['textureUrl']
        if 'modelUrl' in data:
            update_data['modelUrl'] = data['modelUrl']
        if 'processingTimeMs' in data:
            update_data['processingTimeMs'] = data['processingTimeMs']
        if 'errorMessage' in data:
            update_data['errorMessage'] = data['errorMessage']
        
        # 更新对象
        collection.data.update(
            uuid=obj_uuid,
            properties=update_data
        )
        
        client.close()
        
        return jsonify({
            'success': True,
            'data': {
                'buildId': build_id,
                'updated': list(update_data.keys())
            }
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/builds/update-status', methods=['POST'])
def update_build_status():
    """快速更新构建状态（简化版）
    
    Body:
    {
        "buildId": "build_123",
        "status": "processing"  # pending/processing/completed/failed
    }
    """
    data = request.json
    build_id = data.get('buildId')
    status = data.get('status')
    
    if not build_id or not status:
        return jsonify({
            'success': False,
            'error': 'buildId and status are required'
        }), 400
    
    if status not in ['pending', 'processing', 'completed', 'failed']:
        return jsonify({
            'success': False,
            'error': 'Invalid status. Must be one of: pending, processing, completed, failed'
        }), 400
    
    return update_build()

@app.route('/api/builds/complete', methods=['POST'])
def complete_build():
    """标记构建为完成状态
    
    Body:
    {
        "buildId": "build_123",
        "textureUrl": "https://...",
        "modelUrl": "https://...",
        "processingTimeMs": 3500
    }
    """
    data = request.json
    
    if not all(key in data for key in ['buildId', 'textureUrl', 'modelUrl']):
        return jsonify({
            'success': False,
            'error': 'buildId, textureUrl, and modelUrl are required'
        }), 400
    
    # 添加completed状态
    data['status'] = 'completed'
    
    return update_build()

@app.route('/api/builds/fail', methods=['POST'])
def fail_build():
    """标记构建为失败状态
    
    Body:
    {
        "buildId": "build_123",
        "errorMessage": "Error details..."
    }
    """
    data = request.json
    
    if not data.get('buildId'):
        return jsonify({
            'success': False,
            'error': 'buildId is required'
        }), 400
    
    # 添加failed状态
    data['status'] = 'failed'
    
    return update_build()

@app.route('/health', methods=['GET'])
def health_check():
    """健康检查"""
    try:
        client = get_weaviate_client()
        is_ready = client.is_ready()
        client.close()
        
        return jsonify({
            'status': 'healthy' if is_ready else 'unhealthy',
            'service': 'weaviate-n8n-helper',
            'weaviate': 'connected' if is_ready else 'disconnected'
        }), 200 if is_ready else 503
        
    except Exception as e:
        return jsonify({
            'status': 'unhealthy',
            'error': str(e)
        }), 503

if __name__ == '__main__':
    print("🚀 启动Weaviate n8n辅助服务")
    print(f"📍 Weaviate Cloud: {WEAVIATE_GRPC_ENDPOINT}")
    print(f"🌐 服务端口: 5001")
    print("\n可用端点:")
    print("  POST /api/builds/create - 创建构建记录")
    print("  POST /api/builds/update - 更新构建记录")
    print("  POST /api/builds/update-status - 更新状态")
    print("  POST /api/builds/complete - 标记完成")
    print("  POST /api/builds/fail - 标记失败")
    print("  GET  /health - 健康检查")
    print("\n💡 n8n集成示例:")
    print("""\n  在n8n的HTTP Request节点中:
  - URL: http://localhost:5001/api/builds/create
  - Method: POST
  - Body: { "userId": "{{$json.user_id}}", "frontImageUrl": "...", "backImageUrl": "..." }
  """)
    print("\n" + "=" * 50)
    
    app.run(host='0.0.0.0', port=5001, debug=True)