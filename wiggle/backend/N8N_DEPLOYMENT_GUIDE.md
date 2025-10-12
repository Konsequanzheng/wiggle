# n8n 云端部署指南

## 📋 已配置的 n8n Webhook URLs

### 测试 URL（Test URL）
```
https://inin.app.n8n.cloud/webhook-test/build-texture
```
- **用途**：测试工作流，每次点击 "Execute workflow" 按钮后只能调用一次
- **状态**：需要在 n8n 编辑器中点击 "Execute workflow" 按钮激活
- **显示**：执行会显示在 canvas 上

### 生产 URL（Production URL）
```
https://inin.app.n8n.cloud/webhook/build-texture
```
- **用途**：生产环境使用
- **状态**：需要激活工作流（使用编辑器右上角的开关）
- **显示**：执行不会显示在 canvas 上，只在执行列表中可见

## 🚀 部署步骤

### 1. 导入工作流到 n8n 云端

1. 登录到您的 n8n 云端实例：`https://inin.app.n8n.cloud`
2. 创建新工作流或打开现有工作流
3. 点击右上角的菜单（三个点）→ "Import from File"
4. 选择 `n8n_workflow.json` 文件
5. 确认导入

### 2. 部署 Weaviate API 到云端（必需）

⚠️ **重要**：由于工作流中的 HTTP 请求节点指向 `http://localhost:5001`，云端 n8n 无法直接访问本地服务。您**必须**将 Weaviate API 部署到云端。

#### 推荐方案：使用 Modal 部署（与现有服务一致）

项目中已经使用 Modal 部署了纹理生成和模型应用服务，建议也使用 Modal 部署 Weaviate API：

1. **配置 Modal Secrets**（首次部署需要）：
```bash
# 在 Modal 上创建 weaviate-credentials secret
modal secret create weaviate-credentials \
  WEAVIATE_GRPC_ENDPOINT="weaviate-6rnhd.weaviate.network:443" \
  WEAVIATE_API_KEY="your-api-key-here"
```

2. **部署到 Modal**：
```bash
modal deploy modal_weaviate_api.py
```

3. **获取部署 URL**：
   - 部署成功后，Modal 会输出类似这样的 URL：
     ```
     https://your-name--weaviate-api-asgi-app.modal.run
     ```
   - 记录这个 URL，稍后需要在 n8n 工作流中使用

4. **验证部署**：
```bash
curl https://your-name--weaviate-api-asgi-app.modal.run/health
```
应该返回：
```json
{"status": "healthy", "service": "Weaviate n8n Helper API", "timestamp": "..."}
```

#### 其他云服务选项

如果您不想使用 Modal，也可以选择：
- **Railway**：连接 GitHub 仓库自动部署
- **Fly.io**：`fly launch` 然后 `fly deploy`
- **Render**：从 GitHub 部署 web service
- **Heroku**：`heroku create && git push heroku main`

#### 本地测试方案：ngrok（仅用于开发测试）

如果只是临时测试，可以使用 ngrok：
```bash
brew install ngrok
ngrok http 5001
```
然后使用 ngrok 提供的临时 URL。**注意**：ngrok 的免费版 URL 会定期变化，不适合生产环境。

### 3. 更新工作流中的 API 端点

获得云端 API URL 后，需要在 n8n 工作流中更新三个 HTTP 请求节点的 URL。假设您的 Modal 部署 URL 是：
```
https://your-name--weaviate-api-asgi-app.modal.run
```

在 n8n 云端界面中，编辑以下节点：

1. **Create Build Record (Weaviate)** 节点
   - 找到 `URL` 字段
   - 从：`http://localhost:5001/api/builds/create`
   - 改为：`https://your-name--weaviate-api-asgi-app.modal.run/api/builds/create`

2. **Update Texture URL (Weaviate)** 节点
   - 找到 `URL` 字段
   - 从：`http://localhost:5001/api/builds/update`
   - 改为：`https://your-name--weaviate-api-asgi-app.modal.run/api/builds/update`

3. **Complete Build (Weaviate)** 节点
   - 找到 `URL` 字段
   - 从：`http://localhost:5001/api/builds/complete`
   - 改为：`https://your-name--weaviate-api-asgi-app.modal.run/api/builds/complete`

⚠️ **重要**：记得保存工作流的更改！

### 4. 激活工作流

1. 在 n8n 编辑器中，点击右上角的开关将工作流设置为 "Active"
2. 确认 Webhook 节点显示生产 URL

### 5. 测试工作流

#### 使用测试 URL 测试：

1. 在 n8n 编辑器中点击 "Execute workflow" 按钮
2. 使用 curl 或 Postman 发送测试请求：

```bash
curl -X POST https://inin.app.n8n.cloud/webhook-test/build-texture \
  -H "Content-Type: application/json" \
  -d '{
    "userId": "test-user-123",
    "frontImageUrl": "https://example.com/front.png",
    "backImageUrl": "https://example.com/back.png"
  }'
```

3. 在 n8n canvas 上查看执行结果

#### 使用生产 URL 测试：

1. 确保工作流已激活
2. 发送请求到生产 URL：

```bash
curl -X POST https://inin.app.n8n.cloud/webhook/build-texture \
  -H "Content-Type: application/json" \
  -d '{
    "userId": "user-456",
    "frontImageUrl": "https://example.com/front.png",
    "backImageUrl": "https://example.com/back.png"
  }'
```

3. 在 n8n 的 "Executions" 列表中查看结果

### 6. 集成到前端

更新前端代码，将 API 请求发送到生产 URL：

```typescript
const response = await fetch('https://inin.app.n8n.cloud/webhook/build-texture', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
  },
  body: JSON.stringify({
    userId: currentUser.id,
    frontImageUrl: uploadedFrontImage.url,
    backImageUrl: uploadedBackImage.url,
  }),
});

const modelBlob = await response.blob();
```

## 🔍 故障排查

### Webhook 404 错误

**问题**：收到 `The requested webhook "build-texture" is not registered`

**解决方案**：
- **测试 URL**：在 n8n 编辑器中点击 "Execute workflow" 按钮
- **生产 URL**：确保工作流已激活（右上角开关为绿色）

### API 连接失败

**问题**：工作流中的 HTTP Request 节点失败

**解决方案**：
1. 检查 ngrok 是否正在运行（如果使用 ngrok）
2. 检查 API 端点 URL 是否正确
3. 检查 Weaviate n8n Helper API 是否正在运行
4. 检查防火墙和网络设置

### Weaviate 连接错误

**问题**：Weaviate API 无法连接到远程集群

**解决方案**：
1. 验证 `WEAVIATE_GRPC_ENDPOINT` 和 `WEAVIATE_API_KEY` 是否正确
2. 检查 Weaviate Cloud 集群是否在运行
3. 查看 Weaviate n8n Helper API 的日志

## 📊 监控和日志

### n8n 执行日志
- 访问：`https://inin.app.n8n.cloud` → 左侧菜单 "Executions"
- 查看每次工作流执行的详细信息

### Weaviate API 日志
- 本地运行：查看终端输出
- 云端部署：使用云服务提供商的日志查看工具

### Weaviate 数据库
- 使用 `weaviate_api.py` 查询构建历史
- 访问 Weaviate Cloud 控制台查看数据

## 🎯 下一步

1. ✅ 配置并激活 n8n 工作流
2. ✅ 部署或暴露 Weaviate API
3. ✅ 测试完整的数据流
4. ✅ 集成到前端应用
5. ✅ 监控生产环境执行情况

## ✅ 快速部署检查清单

在开始使用 n8n 工作流之前，请确认以下所有步骤：

- [ ] ✅ Weaviate Cloud 集群正在运行
- [ ] ✅ 已创建 `TshirtBuild` collection（运行 `weaviate_schema.py`）
- [ ] ✅ Weaviate API 已部署到 Modal（或其他云服务）
- [ ] ✅ 已在 Modal 中配置 `weaviate-credentials` secret
- [ ] ✅ Modal 部署成功，获得了公网 URL
- [ ] ✅ 通过 `/health` 端点验证了 API 可访问
- [ ] ✅ 在 n8n 云端导入了 `n8n_workflow.json`
- [ ] ✅ 已更新工作流中所有 3 个 Weaviate API 节点的 URL
- [ ] ✅ 保存了 n8n 工作流的更改
- [ ] ✅ 激活了 n8n 工作流
- [ ] ✅ 使用测试 webhook URL 测试了完整流程

## 💡 额外提示

### 查看 Weaviate 中的构建记录

```python
import weaviate
import weaviate.classes as wvc

client = weaviate.connect_to_weaviate_cloud(
    cluster_url="weaviate-6rnhd.weaviate.network:443",
    auth_credentials=wvc.init.Auth.api_key("YOUR_API_KEY")
)

collection = client.collections.get("TshirtBuild")
builds = collection.query.fetch_objects(limit=10)

for build in builds.objects:
    print(f"Build ID: {build.properties['buildId']}")
    print(f"Status: {build.properties['status']}")
    print(f"User: {build.properties['userId']}")
    print("---")

client.close()
```

### 监控 Modal 部署

```bash
# 查看 Modal 应用日志
modal app logs weaviate-api

# 查看 Modal 应用状态
modal app list
```