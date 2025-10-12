import bpy
import math

# 清空场景
bpy.ops.wm.read_factory_settings(use_empty=True)

# 导入原始模型
glb_path = '/Users/yongkangzou/Desktop/Hackathons/Big Berlin hackathon/wiggle/backend/model_textured.glb'
bpy.ops.import_scene.gltf(filepath=glb_path)

# 查找mesh对象
mesh_obj = None
for obj in bpy.data.objects:
    if obj.type == 'MESH':
        mesh_obj = obj
        break

if mesh_obj is None:
    print("Error: No mesh found in the model")
    exit(1)

# 确保mesh在原点
mesh_obj.location = (0, 0, 0)

# 创建骨架
bpy.ops.object.armature_add(enter_editmode=True, location=(0, 0, 0))
armature_obj = bpy.context.active_object
armature_obj.name = "ShirtArmature"
armature = armature_obj.data
armature.name = "ShirtArmature"

# 进入编辑模式创建骨骼
bpy.ops.object.mode_set(mode='EDIT')

# 删除默认骨骼
for bone in armature.edit_bones:
    armature.edit_bones.remove(bone)

# 创建脊柱骨骼链 (5个骨骼)
spine_bones = []
for i in range(5):
    bone = armature.edit_bones.new(f'Spine_{i:02d}')
    bone.head = (0, 0, i * 0.3)
    bone.tail = (0, 0, (i + 1) * 0.3)
    
    if i > 0:
        bone.parent = spine_bones[i - 1]
    
    spine_bones.append(bone)

# 创建左袖子骨骼
left_sleeve = armature.edit_bones.new('Sleeve_L')
left_sleeve.head = (0, 0, 1.2)  # 从脊柱中上部开始
left_sleeve.tail = (-0.8, 0, 1.0)  # 向左延伸
left_sleeve.parent = spine_bones[3]

# 创建右袖子骨骼
right_sleeve = armature.edit_bones.new('Sleeve_R')
right_sleeve.head = (0, 0, 1.2)
right_sleeve.tail = (0.8, 0, 1.0)  # 向右延伸
right_sleeve.parent = spine_bones[3]

# 退出编辑模式
bpy.ops.object.mode_set(mode='OBJECT')

# 选择mesh和armature
mesh_obj.select_set(True)
armature_obj.select_set(True)
bpy.context.view_layer.objects.active = armature_obj

# 将mesh设置为armature的子对象
mesh_obj.parent = armature_obj

# 选择mesh进行权重绘制
bpy.context.view_layer.objects.active = mesh_obj
bpy.ops.object.mode_set(mode='OBJECT')
mesh_obj.select_set(True)
armature_obj.select_set(True)
bpy.context.view_layer.objects.active = armature_obj

# 添加Armature修改器到mesh
mod = mesh_obj.modifiers.new(name='Armature', type='ARMATURE')
mod.object = armature_obj

# 自动权重绑定
bpy.ops.object.parent_set(type='ARMATURE_AUTO')

print("\n=== Skeleton Created ===")
print(f"Armature: {armature_obj.name}")
print(f"Bones: {len(armature.bones)}")
for bone in armature.bones:
    print(f"  - {bone.name}")

print(f"\nMesh '{mesh_obj.name}' bound to armature with automatic weights")

# 导出为GLB
output_path = '/Users/yongkangzou/Desktop/Hackathons/Big Berlin hackathon/wiggle/frontend/public/model_with_skeleton.glb'

# 确保只导出mesh和armature
bpy.ops.object.select_all(action='DESELECT')
mesh_obj.select_set(True)
armature_obj.select_set(True)

bpy.ops.export_scene.gltf(
    filepath=output_path,
    export_format='GLB',
    use_selection=True,
    export_extras=True,
    export_animations=True,
    export_skins=True,
    export_morph=True,
    export_apply=False
)

print(f"\nModel exported to: {output_path}")