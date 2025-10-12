import bpy
import sys

# 清空场景
bpy.ops.wm.read_factory_settings(use_empty=True)

# 导入GLB文件
glb_path = '/Users/yongkangzou/Desktop/Hackathons/Big Berlin hackathon/wiggle/frontend/public/model_with_skeleton.glb'
bpy.ops.import_scene.gltf(filepath=glb_path)

print("\n=== Model Structure ===")
for obj in bpy.data.objects:
    print(f"Object: {obj.name}, Type: {obj.type}")
    if obj.type == 'MESH':
        print(f"  - Has {len(obj.data.vertices)} vertices")
        if obj.modifiers:
            print(f"  - Modifiers: {[m.type for m in obj.modifiers]}")
    elif obj.type == 'ARMATURE':
        print(f"  - Has {len(obj.data.bones)} bones")
        for bone in obj.data.bones:
            print(f"    * Bone: {bone.name}")

print("\n=== Checking SkinnedMesh ===")
for obj in bpy.data.objects:
    if obj.type == 'MESH':
        if obj.parent and obj.parent.type == 'ARMATURE':
            print(f"Mesh '{obj.name}' is parented to armature '{obj.parent.name}'")
            for mod in obj.modifiers:
                if mod.type == 'ARMATURE':
                    print(f"  - Has Armature modifier pointing to '{mod.object.name}'")
        else:
            print(f"Mesh '{obj.name}' is NOT parented to any armature")