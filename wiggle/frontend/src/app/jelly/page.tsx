'use client';

import { Canvas } from '@react-three/fiber';
import { OrbitControls, Environment, PerspectiveCamera } from '@react-three/drei';
import { SkeletonClothPhysics } from '@/components/SkeletonClothPhysics';
import { Suspense } from 'react';

export default function JellyPage() {
  return (
    <div className="w-screen h-screen bg-gradient-to-b from-purple-100 to-pink-100">
      <div className="absolute top-8 left-1/2 -translate-x-1/2 z-10 text-center">
        <h1 className="text-4xl font-bold text-purple-800 mb-2">🦴 Skeleton-Driven Cloth Physics</h1>
        <p className="text-purple-600">Drag the model to experience organic elastic motion</p>
      </div>
      
      <Canvas
        shadows
        gl={{ antialias: true, alpha: true }}
        dpr={[1, 2]}
      >
        <PerspectiveCamera makeDefault position={[0, 0, 5]} fov={50} />
        
        {/* Lighting setup */}
        <ambientLight intensity={0.5} />
        <directionalLight
          position={[5, 5, 5]}
          intensity={1}
          castShadow
          shadow-mapSize-width={1024}
          shadow-mapSize-height={1024}
        />
        <pointLight position={[-5, 5, 5]} intensity={0.5} />
        <spotLight
          position={[0, 10, 0]}
          angle={0.3}
          penumbra={1}
          intensity={0.5}
          castShadow
        />
        
        {/* Environment reflection */}
        <Environment preset="sunset" />
        
        {/* 3D Model - Skeleton Physics */}
        <Suspense fallback={null}>
          <SkeletonClothPhysics />
        </Suspense>
        
        {/* Disable default OrbitControls since we implemented custom dragging */}
      </Canvas>
      
      {/* Instructions */}
      <div className="absolute bottom-8 left-1/2 -translate-x-1/2 bg-white/80 backdrop-blur-sm px-6 py-4 rounded-2xl shadow-lg">
        <div className="flex items-center gap-4 text-sm text-gray-700">
          <div className="flex items-center gap-2">
            <span className="text-2xl">👆</span>
            <span>Drag to Rotate</span>
          </div>
          <div className="w-px h-6 bg-gray-300"></div>
          <div className="flex items-center gap-2">
            <span className="text-2xl">🎯</span>
            <span>Observe Jelly Effect</span>
          </div>
          <div className="w-px h-6 bg-gray-300"></div>
          <div className="flex items-center gap-2">
            <span className="text-2xl">✨</span>
            <span>Release to See Bounce</span>
          </div>
        </div>
      </div>
    </div>
  );
}