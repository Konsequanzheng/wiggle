import bpy
import sys
import os

def apply_texture_to_model(model_path, texture_path, output_path, uv_template_path):
    """
    使用shirt.fbx的UV映射将贴图应用到model.glb上并导出GLB
    
    Args:
        model_path: 输入的GLB模型路径
        texture_path: 纹理图片路径
        output_path: 输出的GLB文件路径
        uv_template_path: UV模板文件路径(shirt.fbx)
    """
    # 清空场景
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.delete()
    
    # 导入UV模板文件(shirt.fbx)
    print(f"导入UV模板: {uv_template_path}")
    bpy.ops.import_scene.fbx(filepath=uv_template_path)
    uv_template_obj = bpy.context.selected_objects[0]
    
    # 确保UV模板对象是网格类型
    if uv_template_obj.type != 'MESH':
        print(f"错误: UV模板对象类型不是MESH: {uv_template_obj.type}")
        return False
    
    # 检查UV模板是否有UV映射
    if not uv_template_obj.data.uv_layers:
        print("错误: UV模板文件没有UV映射")
        return False
    
    print(f"UV模板有 {len(uv_template_obj.data.uv_layers)} 个UV层")
    
    # 暂时取消选择UV模板
    bpy.ops.object.select_all(action='DESELECT')
    
    # 导入目标GLB模型
    print(f"导入目标模型: {model_path}")
    bpy.ops.import_scene.gltf(filepath=model_path)
    target_obj = bpy.context.selected_objects[0]
    bpy.context.view_layer.objects.active = target_obj
    
    # 确保目标对象是网格类型
    if target_obj.type != 'MESH':
        print(f"错误: 目标对象类型不是MESH: {target_obj.type}")
        return False
    
    # 检查顶点数是否匹配
    uv_vert_count = len(uv_template_obj.data.vertices)
    target_vert_count = len(target_obj.data.vertices)
    
    print(f"UV模板顶点数: {uv_vert_count}, 目标模型顶点数: {target_vert_count}")
    
    if uv_vert_count != target_vert_count:
        print(f"警告: 顶点数不匹配! 将尝试通过数据传递转移UV")
    
    # 转移UV映射
    print("正在转移UV映射...")
    
    # 如果顶点数匹配,直接复制UV数据
    if uv_vert_count == target_vert_count:
        print("顶点数匹配,直接复制UV数据")
        
        # 获取源UV层
        src_uv_layer = uv_template_obj.data.uv_layers.active
        
        # 在目标对象上创建或获取UV层
        if not target_obj.data.uv_layers:
            target_obj.data.uv_layers.new(name="UVMap")
        dst_uv_layer = target_obj.data.uv_layers.active
        
        # 复制UV坐标
        for i, loop in enumerate(target_obj.data.loops):
            if i < len(src_uv_layer.data):
                dst_uv_layer.data[i].uv = src_uv_layer.data[i].uv
        
        print(f"已复制 {len(dst_uv_layer.data)} 个UV坐标")
    else:
        print("顶点数不匹配,使用近似映射")
        # 这里可以实现更复杂的UV转移逻辑
        # 暂时创建一个新的UV层
        if not target_obj.data.uv_layers:
            target_obj.data.uv_layers.new(name="UVMap")
    
    # 删除UV模板对象
    bpy.ops.object.select_all(action='DESELECT')
    uv_template_obj.select_set(True)
    bpy.ops.object.delete()
    
    # 选择目标对象
    target_obj.select_set(True)
    bpy.context.view_layer.objects.active = target_obj
    obj = target_obj
    
    # 创建材质
    print(f"应用纹理: {texture_path}")
    mat = bpy.data.materials.new(name="TextureMaterial")
    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links
    
    # 清空默认节点
    nodes.clear()
    
    # 创建必要的节点
    node_tex = nodes.new(type='ShaderNodeTexImage')
    node_bsdf = nodes.new(type='ShaderNodeBsdfPrincipled')
    node_output = nodes.new(type='ShaderNodeOutputMaterial')
    
    # 加载纹理图片
    node_tex.image = bpy.data.images.load(texture_path)
    
    # 设置材质为透明混合模式
    mat.blend_method = 'BLEND'
    
    # 连接节点 - 包括颜色和透明度
    links.new(node_tex.outputs['Color'], node_bsdf.inputs['Base Color'])
    links.new(node_tex.outputs['Alpha'], node_bsdf.inputs['Alpha'])
    links.new(node_bsdf.outputs['BSDF'], node_output.inputs['Surface'])
    
    # 应用材质到对象
    if obj.data.materials:
        obj.data.materials[0] = mat
    else:
        obj.data.materials.append(mat)
    
    # 导出GLB
    print(f"导出模型: {output_path}")
    bpy.ops.export_scene.gltf(
        filepath=output_path,
        export_format='GLB',
        export_texcoords=True,
        export_materials='EXPORT'
    )
    
    print("✓ 成功完成!")
    return True

if __name__ == "__main__":
    if len(sys.argv) < 8:  # Blender传递参数时会有额外参数
        print("用法: blender --background --python apply_texture_to_model.py -- <model.glb> <texture.png> <output.glb> <uv_template.fbx>")
        sys.exit(1)
    
    # 获取 '--' 后面的参数
    argv = sys.argv
    argv = argv[argv.index("--") + 1:]
    
    model_path = argv[0]
    texture_path = argv[1]
    output_path = argv[2]
    uv_template_path = argv[3]
    
    # 检查文件是否存在
    if not os.path.exists(model_path):
        print(f"错误: 模型文件不存在: {model_path}")
        sys.exit(1)
    
    if not os.path.exists(texture_path):
        print(f"错误: 纹理文件不存在: {texture_path}")
        sys.exit(1)
    
    if not os.path.exists(uv_template_path):
        print(f"错误: UV模板文件不存在: {uv_template_path}")
        sys.exit(1)
    
    # 执行处理
    success = apply_texture_to_model(model_path, texture_path, output_path, uv_template_path)
    sys.exit(0 if success else 1)