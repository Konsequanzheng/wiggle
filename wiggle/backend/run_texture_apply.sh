#!/bin/bash

# 自动检测Blender并应用纹理到模型

set -e

echo "🔍 检测Blender安装..."

# 检查常见的Blender安装位置
BLENDER_CMD=""

if command -v blender &> /dev/null; then
    BLENDER_CMD="blender"
    echo "✓ 找到Blender: $(which blender)"
elif [ -f "/Applications/Blender.app/Contents/MacOS/Blender" ]; then
    BLENDER_CMD="/Applications/Blender.app/Contents/MacOS/Blender"
    echo "✓ 找到Blender: $BLENDER_CMD"
else
    echo "❌ 错误: 未找到Blender"
    echo ""
    echo "请先安装Blender:"
    echo "  方法1: brew install --cask blender"
    echo "  方法2: 从 https://www.blender.org/download/ 下载"
    exit 1
fi

# 检查输入文件
if [ ! -f "model.glb" ]; then
    echo "❌ 错误: model.glb 文件不存在"
    exit 1
fi

if [ ! -f "texture.png" ]; then
    echo "❌ 错误: texture.png 文件不存在"
    exit 1
fi

echo "📦 输入文件:"
echo "  - model.glb"
echo "  - texture.png"
echo ""
echo "🚀 开始处理..."
echo ""

# 运行Blender脚本
"$BLENDER_CMD" --background --python apply_texture_to_model.py -- model.glb texture.png model_textured.glb

if [ $? -eq 0 ]; then
    echo ""
    echo "✅ 成功! 输出文件: model_textured.glb"
    
    # 显示文件信息
    if [ -f "model_textured.glb" ]; then
        SIZE=$(ls -lh model_textured.glb | awk '{print $5}')
        echo "📊 文件大小: $SIZE"
    fi
else
    echo ""
    echo "❌ 处理失败"
    exit 1
fi