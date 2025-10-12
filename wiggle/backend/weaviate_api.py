"""Weaviate查询API

提供RESTful API用于查询T恤构建历史记录，支持:
- 按用户ID查询
- 按构建状态过滤
- 向量相似度搜索
- 时间范围查询
"""

from flask import Flask, jsonify, request
import weaviate
import weaviate.classes as wvc
from weaviate.classes.query import Filter
from datetime import datetime, timedelta
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

@app.route('/api/builds', methods=['GET'])
def get_builds():
    """获取构建列表
    
    Query参数:
    - user_id: 用户ID（可选）
    - status: 状态过滤 pending/processing/completed/failed（可选）
    - limit: 返回数量限制（默认10，最大100）
    - offset: 偏移量（默认0）
    - days: 时间范围（天数，默认7）
    """
    user_id = request.args.get('user_id')
    status = request.args.get('status')
    limit = min(int(request.args.get('limit', 10)), 100)
    offset = int(request.args.get('offset', 0))
    days = int(request.args.get('days', 7))
    
    try:
        client = get_weaviate_client()
        collection = client.collections.get("TshirtBuild")
        
        # 构建过滤条件
        filters = []
        
        # 时间范围过滤
        start_date = datetime.now() - timedelta(days=days)
        filters.append(
            Filter.by_property("timestamp").greater_or_equal(start_date)
        )
        
        # 用户ID过滤
        if user_id:
            filters.append(
                Filter.by_property("userId").equal(user_id)
            )
        
        # 状态过滤
        if status:
            filters.append(
                Filter.by_property("status").equal(status)
            )
        
        # 组合过滤条件
        combined_filter = filters[0]
        for f in filters[1:]:
            combined_filter = combined_filter & f
        
        # 查询
        result = collection.query.fetch_objects(
            filters=combined_filter,
            limit=limit,
            offset=offset
        )
        
        # 格式化结果
        builds = []
        for obj in result.objects:
            builds.append({
                'id': str(obj.uuid),
                'buildId': obj.properties.get('buildId'),
                'userId': obj.properties.get('userId'),
                'timestamp': obj.properties.get('timestamp'),
                'frontImageUrl': obj.properties.get('frontImageUrl'),
                'backImageUrl': obj.properties.get('backImageUrl'),
                'textureUrl': obj.properties.get('textureUrl'),
                'modelUrl': obj.properties.get('modelUrl'),
                'status': obj.properties.get('status'),
                'processingTimeMs': obj.properties.get('processingTimeMs'),
                'errorMessage': obj.properties.get('errorMessage')
            })
        
        client.close()
        
        return jsonify({
            'success': True,
            'data': builds,
            'count': len(builds),
            'limit': limit,
            'offset': offset
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/builds/<build_id>', methods=['GET'])
def get_build(build_id):
    """获取单个构建详情"""
    try:
        client = get_weaviate_client()
        collection = client.collections.get("TshirtBuild")
        
        result = collection.query.fetch_objects(
            filters=Filter.by_property("buildId").equal(build_id),
            limit=1
        )
        
        if not result.objects:
            client.close()
            return jsonify({
                'success': False,
                'error': 'Build not found'
            }), 404
        
        obj = result.objects[0]
        build = {
            'id': str(obj.uuid),
            'buildId': obj.properties.get('buildId'),
            'userId': obj.properties.get('userId'),
            'timestamp': obj.properties.get('timestamp'),
            'frontImageUrl': obj.properties.get('frontImageUrl'),
            'backImageUrl': obj.properties.get('backImageUrl'),
            'textureUrl': obj.properties.get('textureUrl'),
            'modelUrl': obj.properties.get('modelUrl'),
            'status': obj.properties.get('status'),
            'processingTimeMs': obj.properties.get('processingTimeMs'),
            'errorMessage': obj.properties.get('errorMessage')
        }
        
        client.close()
        
        return jsonify({
            'success': True,
            'data': build
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/builds/search/similar', methods=['POST'])
def search_similar_builds():
    """通过图片向量相似度搜索
    
    Body:
    {
        "image_url": "https://example.com/image.png",
        "limit": 5,
        "certainty": 0.7
    }
    """
    data = request.json
    image_url = data.get('image_url')
    limit = min(int(data.get('limit', 5)), 20)
    certainty = float(data.get('certainty', 0.7))
    
    if not image_url:
        return jsonify({
            'success': False,
            'error': 'image_url is required'
        }), 400
    
    try:
        client = get_weaviate_client()
        collection = client.collections.get("TshirtBuild")
        
        # 向量搜索
        result = collection.query.near_image(
            near_image=image_url,
            limit=limit,
            certainty=certainty
        )
        
        # 格式化结果
        builds = []
        for obj in result.objects:
            builds.append({
                'id': str(obj.uuid),
                'buildId': obj.properties.get('buildId'),
                'userId': obj.properties.get('userId'),
                'timestamp': obj.properties.get('timestamp'),
                'frontImageUrl': obj.properties.get('frontImageUrl'),
                'backImageUrl': obj.properties.get('backImageUrl'),
                'textureUrl': obj.properties.get('textureUrl'),
                'modelUrl': obj.properties.get('modelUrl'),
                'status': obj.properties.get('status'),
                'similarity': obj.metadata.certainty if hasattr(obj.metadata, 'certainty') else None
            })
        
        client.close()
        
        return jsonify({
            'success': True,
            'data': builds,
            'count': len(builds)
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/builds/stats', methods=['GET'])
def get_stats():
    """获取构建统计信息
    
    Query参数:
    - user_id: 用户ID（可选）
    - days: 时间范围（天数，默认30）
    """
    user_id = request.args.get('user_id')
    days = int(request.args.get('days', 30))
    
    try:
        client = get_weaviate_client()
        collection = client.collections.get("TshirtBuild")
        
        # 时间范围过滤
        start_date = datetime.now() - timedelta(days=days)
        filters = Filter.by_property("timestamp").greater_or_equal(start_date)
        
        if user_id:
            filters = filters & Filter.by_property("userId").equal(user_id)
        
        # 获取所有记录
        result = collection.query.fetch_objects(
            filters=filters,
            limit=1000  # 假设不会超过1000条
        )
        
        # 计算统计信息
        total = len(result.objects)
        completed = sum(1 for obj in result.objects if obj.properties.get('status') == 'completed')
        failed = sum(1 for obj in result.objects if obj.properties.get('status') == 'failed')
        processing = sum(1 for obj in result.objects if obj.properties.get('status') == 'processing')
        pending = sum(1 for obj in result.objects if obj.properties.get('status') == 'pending')
        
        # 平均处理时间
        processing_times = [obj.properties.get('processingTimeMs') for obj in result.objects 
                          if obj.properties.get('processingTimeMs') is not None]
        avg_processing_time = sum(processing_times) / len(processing_times) if processing_times else 0
        
        client.close()
        
        return jsonify({
            'success': True,
            'data': {
                'total': total,
                'completed': completed,
                'failed': failed,
                'processing': processing,
                'pending': pending,
                'successRate': round(completed / total * 100, 2) if total > 0 else 0,
                'avgProcessingTimeMs': round(avg_processing_time, 2),
                'timeRangeDays': days
            }
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/health', methods=['GET'])
def health_check():
    """健康检查"""
    try:
        client = get_weaviate_client()
        is_ready = client.is_ready()
        client.close()
        
        return jsonify({
            'status': 'healthy' if is_ready else 'unhealthy',
            'weaviate': 'connected' if is_ready else 'disconnected'
        }), 200 if is_ready else 503
        
    except Exception as e:
        return jsonify({
            'status': 'unhealthy',
            'error': str(e)
        }), 503

if __name__ == '__main__':
    print("🚀 启动Weaviate查询API")
    print(f"📍 Weaviate: {WEAVIATE_HOST}:{WEAVIATE_PORT}")
    print("\n可用端点:")
    print("  GET  /api/builds - 获取构建列表")
    print("  GET  /api/builds/<build_id> - 获取构建详情")
    print("  POST /api/builds/search/similar - 向量相似度搜索")
    print("  GET  /api/builds/stats - 获取统计信息")
    print("  GET  /health - 健康检查")
    print("\n" + "=" * 50)
    
    app.run(host='0.0.0.0', port=5001, debug=True)