# 将纹理应用到3D模型

本指南说明如何使用Blender将`texture.png`应用到`model.glb`上。

## 前提条件

需要安装Blender（3D建模软件）。

### 在macOS上安装Blender

**方法1: 使用Homebrew（推荐）**
```bash
brew install --cask blender
```

**方法2: 手动下载**
1. 访问 https://www.blender.org/download/
2. 下载macOS版本
3. 将Blender.app拖到Applications文件夹

## 使用方法

### 自动处理（推荐）

安装Blender后，运行：

```bash
# 如果通过Homebrew安装
blender --background --python apply_texture_to_model.py -- model.glb texture.png model_textured.glb

# 如果手动安装到Applications
/Applications/Blender.app/Contents/MacOS/Blender --background --python apply_texture_to_model.py -- model.glb texture.png model_textured.glb
```

### 使用便捷脚本

运行提供的shell脚本：
```bash
bash run_texture_apply.sh
```

## 脚本功能

`apply_texture_to_model.py`脚本会：

1. **加载3D模型**：导入`model.glb`文件
2. **自动UV展开**：使用智能UV投影算法自动展开UV坐标
3. **应用纹理**：将`texture.png`作为材质贴图应用到模型上
4. **导出结果**：保存为带纹理的新GLB文件`model_textured.glb`

## 输出文件

成功执行后，会生成：
- `model_textured.glb`：带有纹理贴图的3D模型文件

## 参数说明

脚本接受三个参数：
1. 输入模型路径（如`model.glb`）
2. 纹理图片路径（如`texture.png`）
3. 输出模型路径（如`model_textured.glb`）

## 故障排除

### 错误：command not found: blender

请先安装Blender（见上方安装说明）。

### 错误：模型文件不存在

确保`model.glb`和`texture.png`文件存在于backend目录中。

### UV展开效果不理想

可以调整脚本中的UV展开参数：
- `angle_limit`：角度限制（默认66.0）
- `island_margin`：UV岛间距（默认0.02）

## 技术细节

- **UV展开方法**：Smart UV Project（智能UV投影）
- **材质系统**：Principled BSDF节点
- **导出格式**：GLB（包含嵌入纹理）
- **Blender模式**：无头模式（后台运行，无GUI）