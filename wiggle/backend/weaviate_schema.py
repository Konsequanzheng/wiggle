"""Weaviate Schema定义文件

用于定义T恤构建元数据的存储结构，支持向量搜索和元数据查询。

使用方法:
1. 启动Weaviate实例: docker run -d -p 8080:8080 -p 50051:50051 semitechnologies/weaviate:latest
2. 运行此脚本创建schema: python weaviate_schema.py
"""

import weaviate
import weaviate.classes as wvc
from datetime import datetime
import os

# Weaviate连接配置
WEAVIATE_GRPC_ENDPOINT = os.getenv("WEAVIATE_GRPC_ENDPOINT", "grpc-aoj6v69aspmruwn6zlgma.c0.europe-west3.gcp.weaviate.cloud")
WEAVIATE_API_KEY = os.getenv("WEAVIATE_API_KEY", "N08rcE1Ua0pJTlB1RVh0cF9XeEJjMVRGZE5MdjF1YkpqanZKc1RHaTV3ajc4c3BaOEZiOTA5ZXBlay9nPV92MjAw")

def create_schema():
    """创建Weaviate schema"""
    
    # 连接到Weaviate Cloud
    client = weaviate.connect_to_weaviate_cloud(
        cluster_url=f"https://{WEAVIATE_GRPC_ENDPOINT.replace('grpc-', '')}",
        auth_credentials=wvc.init.Auth.api_key(WEAVIATE_API_KEY)
    )
    
    try:
        # 检查集合是否已存在
        if client.collections.exists("TshirtBuild"):
            print("⚠️  TshirtBuild集合已存在，跳过创建")
            return client
        
        # 创建TshirtBuild集合
        print("📝 正在创建TshirtBuild集合...")
        tshirt_build = client.collections.create(
            name="TshirtBuild",
            description="存储T恤纹理构建的元数据和向量",
            
            # 定义属性
            properties=[
                wvc.config.Property(
                    name="buildId",
                    description="构建的唯一标识符",
                    data_type=wvc.config.DataType.TEXT,
                    skip_vectorization=True
                ),
                wvc.config.Property(
                    name="userId",
                    description="用户ID",
                    data_type=wvc.config.DataType.TEXT,
                    skip_vectorization=True
                ),
                wvc.config.Property(
                    name="timestamp",
                    description="构建创建时间",
                    data_type=wvc.config.DataType.DATE
                ),
                wvc.config.Property(
                    name="frontImageUrl",
                    description="前面图片的URL（可以是临时URL）",
                    data_type=wvc.config.DataType.TEXT
                ),
                wvc.config.Property(
                    name="backImageUrl",
                    description="后面图片的URL（可以是临时URL）",
                    data_type=wvc.config.DataType.TEXT
                ),
                wvc.config.Property(
                    name="textureUrl",
                    description="生成的纹理图片URL（24小时过期）",
                    data_type=wvc.config.DataType.TEXT,
                    skip_vectorization=True
                ),
                wvc.config.Property(
                    name="modelUrl",
                    description="生成的带纹理模型URL（24小时过期）",
                    data_type=wvc.config.DataType.TEXT,
                    skip_vectorization=True
                ),
                wvc.config.Property(
                    name="status",
                    description="构建状态: pending/processing/completed/failed",
                    data_type=wvc.config.DataType.TEXT,
                    skip_vectorization=True
                ),
                wvc.config.Property(
                    name="processingTimeMs",
                    description="处理时间（毫秒）",
                    data_type=wvc.config.DataType.NUMBER
                ),
                wvc.config.Property(
                    name="errorMessage",
                    description="错误信息（如果失败）",
                    data_type=wvc.config.DataType.TEXT,
                    skip_vectorization=True
                ),
            ],
            
            # 注意：远程集群可能不支持multi2vec-clip，改为使用none（不自动向量化）
            # 如需向量搜索功能，请在集群中启用相应的向量化模块
            vectorizer_config=wvc.config.Configure.Vectorizer.none(),
            
            # 配置向量索引
            vector_index_config=wvc.config.Configure.VectorIndex.hnsw(
                distance_metric=wvc.config.VectorDistances.COSINE,
                ef_construction=128,
                max_connections=64
            )
        )
        
        print("✅ TshirtBuild集合创建成功")
        
        # 打印schema信息
        collection = client.collections.get("TshirtBuild")
        print(f"\n📊 集合信息:")
        print(f"   名称: {collection.name}")
        print(f"   向量化器: multi2vec_clip")
        
        return client
        
    except Exception as e:
        print(f"❌ 创建schema失败: {e}")
        raise

def add_sample_data(client):
    """添加示例数据"""
    print("\n📝 添加示例数据...")
    
    collection = client.collections.get("TshirtBuild")
    
    sample_builds = [
        {
            "buildId": "build_001",
            "userId": "user_123",
            "timestamp": datetime.now(),
            "frontImageUrl": "https://example.com/front.png",
            "backImageUrl": "https://example.com/back.png",
            "textureUrl": "https://temp.storage/texture_001.png",
            "modelUrl": "https://temp.storage/model_001.glb",
            "status": "completed",
            "processingTimeMs": 5230,
            "errorMessage": None
        },
        {
            "buildId": "build_002",
            "userId": "user_456",
            "timestamp": datetime.now(),
            "frontImageUrl": "https://example.com/design2_front.png",
            "backImageUrl": "https://example.com/design2_back.png",
            "textureUrl": "https://temp.storage/texture_002.png",
            "modelUrl": "https://temp.storage/model_002.glb",
            "status": "completed",
            "processingTimeMs": 4890,
            "errorMessage": None
        }
    ]
    
    for build in sample_builds:
        collection.data.insert(build)
    
    print(f"✅ 成功添加 {len(sample_builds)} 条示例数据")

def query_examples(client):
    """查询示例"""
    print("\n🔍 查询示例...")
    
    collection = client.collections.get("TshirtBuild")
    
    # 示例1: 查询特定用户的所有构建
    print("\n1️⃣ 查询用户 user_123 的所有构建:")
    response = collection.query.fetch_objects(
        filters=wvc.query.Filter.by_property("userId").equal("user_123"),
        limit=10
    )
    for obj in response.objects:
        print(f"   - {obj.properties['buildId']}: {obj.properties['status']}")
    
    # 示例2: 查询所有已完成的构建
    print("\n2️⃣ 查询所有已完成的构建:")
    response = collection.query.fetch_objects(
        filters=wvc.query.Filter.by_property("status").equal("completed"),
        limit=10
    )
    print(f"   找到 {len(response.objects)} 个已完成的构建")
    
    # 示例3: 统计信息
    print("\n3️⃣ 统计信息:")
    response = collection.aggregate.over_all()
    print(f"   总构建数: {response.total_count}")

if __name__ == "__main__":
    print("🚀 开始设置Weaviate Schema...\n")
    
    try:
        # 创建schema
        client = create_schema()
        
        # 添加示例数据
        add_sample_data(client)
        
        # 运行查询示例
        query_examples(client)
        
        print("\n✅ 所有操作完成！")
        print("\n💡 提示:")
        print("   - Weaviate控制台: http://localhost:8080")
        print("   - 使用 weaviate_n8n_helper.py 启动n8n集成API")
        print("   - 使用 weaviate_api.py 启动查询API")
        
        client.close()
        
    except Exception as e:
        print(f"\n❌ 错误: {e}")
        import traceback
        traceback.print_exc()