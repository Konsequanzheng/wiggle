"use client";

import { useRef, useEffect } from "react";
import { Canvas, useFrame } from "@react-three/fiber";
import {
  useGLTF,
  OrbitControls,
  Environment,
  useTexture,
} from "@react-three/drei";
import * as THREE from "three";

function Model({ url }: { url: string }) {
  const { scene } = useGLTF(url);
  const meshRef = useRef<THREE.Group>(null);
  const texture = useTexture("/white-large-diffuse.webp");

  useEffect(() => {
    if (scene && texture) {
      // Flip the texture's Y-axis using transform
      texture.flipY = false;
      texture.needsUpdate = true;

      // Traverse the scene to find all meshes and apply the texture
      scene.traverse((child) => {
        if (child instanceof THREE.Mesh) {
          // Create a new material with the texture
          const material = new THREE.MeshStandardMaterial({
            map: texture,
            // You can adjust these properties as needed
            roughness: 0.5,
            metalness: 0.1,
            side: THREE.DoubleSide, // Render on both sides
          });

          // Apply the material to the mesh
          child.material = material;

          // Alternative approach: modify UV coordinates to flip Y
          if (child.geometry.attributes.uv) {
            const uvAttribute = child.geometry.attributes.uv;
            const uvArray = uvAttribute.array;

            // Flip the V coordinates (Y-axis in UV space)
            for (let i = 1; i < uvArray.length; i += 2) {
              uvArray[i] = 1 - uvArray[i];
            }

            uvAttribute.needsUpdate = true;
          }
        }
      });
    }
  }, [scene, texture]);

  useFrame((state) => {
    if (meshRef.current) {
      meshRef.current.rotation.y =
        Math.sin(state.clock.elapsedTime * 0.5) * 0.1;
    }
  });

  return (
    <group ref={meshRef}>
      <primitive object={scene} scale={1} />
    </group>
  );
}

export default function ModelViewer() {
  return (
    <div className="w-full h-screen bg-gray-100">
      <Canvas camera={{ position: [0, 0, 5], fov: 75 }}>
        <ambientLight intensity={0.3} />
        <directionalLight position={[10, 10, 5]} intensity={0.2} />
        <Model url="/model.glb" />
        <OrbitControls
          enablePan={true}
          enableZoom={true}
          enableRotate={true}
          autoRotate={false}
        />
        <Environment preset="studio" />
      </Canvas>
    </div>
  );
}
