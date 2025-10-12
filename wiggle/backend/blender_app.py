# blender_app.py - Modal deployment for Blender model fusion
from modal import Image, App, method, Volume
import subprocess
import os

app = App("tshirt-blender-service")

# Install Blender in Modal image
blender_image = (
    Image.debian_slim()
    .apt_install("blender", "wget")
    .pip_install("boto3")  # For S3 upload if needed
)

# Persistent storage for model files
volume = Volume.from_name("tshirt-models", create_if_missing=True)

@app.function(
    image=blender_image,
    volumes={"/assets": volume},
    timeout=600  # 10 minutes timeout
)
def apply_texture_to_model(
    texture_png_data: bytes
):
    """
    Apply texture to model using Blender
    Args:
        texture_png_data: Binary data of texture.png (passed from n8n)
    Returns: Binary data of model_textured.glb
    
    Note: model.glb and shirt.fbx are read from Modal Volume
    """
    import tempfile
    
    # 1. Setup file paths
    with tempfile.TemporaryDirectory() as tmpdir:
        # Read static files from Modal Volume
        model_path = "/assets/model.glb"
        uv_template_path = "/assets/shirt.fbx"
        
        # Save incoming texture data to temporary file
        texture_path = f"{tmpdir}/texture.png"
        with open(texture_path, "wb") as f:
            f.write(texture_png_data)
        
        output_path = f"{tmpdir}/model_textured.glb"
        
        # 2. Copy Blender script to temp directory
        # The apply_texture_to_model.py script should be included in the image
        blender_script_path = f"{tmpdir}/apply_texture_script.py"
        
        # Embed the Blender script inline
        blender_script_content = '''
import bpy
import sys
import os

# Parse command line arguments
argv = sys.argv
argv = argv[argv.index("--") + 1:]  # Get all args after "--"

if len(argv) < 4:
    print("Usage: blender --background --python script.py -- <model_path> <texture_path> <output_path> <uv_template_path>")
    sys.exit(1)

model_path = argv[0]
texture_path = argv[1]
output_path = argv[2]
uv_template_path = argv[3]

# Check file existence
for path in [model_path, texture_path, uv_template_path]:
    if not os.path.exists(path):
        print(f"Error: File not found: {path}")
        sys.exit(1)

# Clear the scene
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete()

# Import UV template (FBX)
bpy.ops.import_scene.fbx(filepath=uv_template_path)
uv_template_obj = bpy.context.selected_objects[0]

if uv_template_obj.type != 'MESH':
    print("Error: UV template is not a mesh")
    sys.exit(1)

if not uv_template_obj.data.uv_layers:
    print("Error: UV template has no UV layers")
    sys.exit(1)

# Import target model (GLB)
bpy.ops.import_scene.gltf(filepath=model_path)
target_obj = bpy.context.selected_objects[0]

if target_obj.type != 'MESH':
    print("Error: Target model is not a mesh")
    sys.exit(1)

# Transfer UV map
if len(uv_template_obj.data.vertices) == len(target_obj.data.vertices):
    # Direct copy if vertex count matches
    uv_layer = uv_template_obj.data.uv_layers.active
    new_uv_layer = target_obj.data.uv_layers.new(name="TransferredUV")
    for i, loop in enumerate(target_obj.data.loops):
        new_uv_layer.data[i].uv = uv_layer.data[i].uv
else:
    # Create new UV layer
    new_uv_layer = target_obj.data.uv_layers.new(name="TransferredUV")

# Delete UV template
bpy.data.objects.remove(uv_template_obj, do_unlink=True)

# Create material with texture
mat = bpy.data.materials.new(name="TexturedMaterial")
mat.use_nodes = True
nodes = mat.node_tree.nodes
links = mat.node_tree.links

# Clear default nodes
for node in nodes:
    nodes.remove(node)

# Create nodes
tex_image = nodes.new(type='ShaderNodeTexImage')
principled = nodes.new(type='ShaderNodeBsdfPrincipled')
output = nodes.new(type='ShaderNodeOutputMaterial')

# Load texture
tex_image.image = bpy.data.images.load(texture_path)

# Set blend mode
mat.blend_method = 'BLEND'

# Link nodes
links.new(tex_image.outputs['Color'], principled.inputs['Base Color'])
links.new(tex_image.outputs['Alpha'], principled.inputs['Alpha'])
links.new(principled.outputs['BSDF'], output.inputs['Surface'])

# Assign material to object
if target_obj.data.materials:
    target_obj.data.materials[0] = mat
else:
    target_obj.data.materials.append(mat)

# Export as GLB
bpy.ops.export_scene.gltf(
    filepath=output_path,
    export_format='GLB',
    export_texcoords=True,
    export_materials='EXPORT'
)

print(f"Successfully exported to {output_path}")
'''
        
        with open(blender_script_path, 'w') as f:
            f.write(blender_script_content)
        
        # 3. Run Blender script
        cmd = [
            "blender", "--background", "--python", blender_script_path, "--",
            model_path, texture_path, output_path, uv_template_path
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode != 0:
            raise Exception(f"Blender failed: {result.stderr}")
        
        # 4. Read output file and return as bytes
        # Can be uploaded to S3/R2 or returned directly
        with open(output_path, "rb") as f:
            glb_bytes = f.read()
        
        return glb_bytes

@app.local_entrypoint()
def main():
    # Test entry point - Provide actual texture.png file for testing
    # Make sure to upload model.glb and shirt.fbx to Modal Volume first:
    # modal volume put tshirt-models model.glb /model.glb
    # modal volume put tshirt-models shirt.fbx /shirt.fbx
    
    # Example test code:
    # with open("texture.png", "rb") as f:
    #     texture_data = f.read()
    # result = apply_texture_to_model.remote(texture_data)
    # with open("output_model.glb", "wb") as f:
    #     f.write(result)
    # print(f"Generated GLB: {len(result)} bytes")
    
    print("Blender app deployed successfully!")
    print("\nBefore testing, upload static files to Modal Volume:")
    print("  modal volume put tshirt-models model.glb /model.glb")
    print("  modal volume put tshirt-models shirt.fbx /shirt.fbx")
    print("\nThen test with: apply_texture_to_model.remote(texture_png_bytes)")