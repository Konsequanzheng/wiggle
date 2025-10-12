'use client';

import { useRef, useState } from 'react';
import { useFrame, useThree } from '@react-three/fiber';
import { useGLTF } from '@react-three/drei';
import * as THREE from 'three';

export function JellyModel() {
  const group = useRef<THREE.Group>(null);
  const { scene } = useGLTF('/model_textured.glb');
  const { viewport } = useThree();
  
  // 旋转状态
  const [isDragging, setIsDragging] = useState(false);
  const [rotation, setRotation] = useState(0);
  const [velocity, setVelocity] = useState(0);
  const previousMouseX = useRef(0);
  
  // 果冻变形参数
  const [deformation, setDeformation] = useState({ x: 0, y: 0, z: 0 });
  const [targetDeformation, setTargetDeformation] = useState({ x: 0, y: 0, z: 0 });
  
  // 衣角拖曳参数
  const [hemOffset, setHemOffset] = useState({ x: 0, z: 0 });
  const hemVelocity = useRef({ x: 0, z: 0 });
  
  // 鼠标事件处理
  const handlePointerDown = (e: any) => {
    setIsDragging(true);
    previousMouseX.current = e.clientX;
    e.stopPropagation();
  };
  
  const handlePointerMove = (e: any) => {
    if (!isDragging) return;
    
    const deltaX = e.clientX - previousMouseX.current;
    const rotationSpeed = deltaX * 0.01;
    
    setRotation(prev => prev + rotationSpeed);
    setVelocity(rotationSpeed);
    
    // 根据速度设置目标变形
    const deformAmount = Math.abs(rotationSpeed) * 2;
    setTargetDeformation({
      x: Math.sin(rotation) * deformAmount,
      y: 0,
      z: Math.cos(rotation) * deformAmount
    });
    
    previousMouseX.current = e.clientX;
    e.stopPropagation();
  };
  
  const handlePointerUp = () => {
    setIsDragging(false);
  };
  
  // 动画循环
  useFrame((state, delta) => {
    if (!group.current) return;
    
    // 惯性旋转
    if (!isDragging && Math.abs(velocity) > 0.001) {
      setRotation(prev => prev + velocity);
      setVelocity(prev => prev * rotationDamping); // 阻尼
      
      // 衣角跟随效果 (延迟跟随旋转)
      setHemOffset(prev => {
        // 目标位置:根据旋转速度计算衣角应该偏移的位置
        const targetX = -velocity * hemDrag * 50; // 水平方向拖曳
        const targetZ = velocity * hemDrag * 30; // 深度方向拖曳
        
        // 计算衣角加速度 (弹簧力)
        const accelX = (targetX - prev.x) * hemSpring;
        const accelZ = (targetZ - prev.z) * hemSpring;
        
        // 更新衣角速度
        hemVelocity.current.x = (hemVelocity.current.x + accelX) * hemDamping;
        hemVelocity.current.z = (hemVelocity.current.z + accelZ) * hemDamping;
        
        // 应用速度到位置
        return {
          x: prev.x + hemVelocity.current.x,
          z: prev.z + hemVelocity.current.z
        };
      });
      
      // 惯性时的轻微变形
      const deformAmount = Math.abs(velocity) * 1.5;
      setTargetDeformation({
        x: Math.sin(rotation) * deformAmount,
        y: 0,
        z: Math.cos(rotation) * deformAmount
      });
    } else if (!isDragging) {
      // 静止时回到原形
      setTargetDeformation({ x: 0, y: 0, z: 0 });
      setHemOffset(prev => {
        hemVelocity.current.x *= hemDamping;
        hemVelocity.current.z *= hemDamping;
        return {
          x: prev.x * 0.9,
          z: prev.z * 0.9
        };
      });
    }
    
    // 物理参数 - 衣角拖曳效果
    const rotationDamping = 0.92; // 旋转阻尼
    const hemDamping = 0.88; // 衣角阻尼 (更低,让衣角更容易被带动)
    const hemSpring = 0.12; // 衣角弹簧强度 (较低,产生延迟感)
    const hemDrag = 0.3; // 衣角受旋转速度影响的强度
    const springStrength = 0.22; // 弹簧强度 (提高以加快回弹速度)
    const damping = 0.92; // 阻尼 (提高以增加流畅度)
    
    setDeformation(prev => ({
      x: (prev.x + (targetDeformation.x - prev.x) * springStrength) * damping,
      y: (prev.y + (targetDeformation.y - prev.y) * springStrength) * damping,
      z: (prev.z + (targetDeformation.z - prev.z) * springStrength) * damping
    }));
    
    // 应用旋转
    group.current.rotation.y = rotation;
    
    // 应用果冻变形 (使用scale和skew效果) - 细微形变
    const scaleX = 1 + deformation.x * 0.06;
    const scaleY = 1 - Math.abs(deformation.x) * 0.03; // Y轴压缩
    const scaleZ = 1 + deformation.z * 0.05;
    
    group.current.scale.set(scaleX, scaleY, scaleZ);
    
    // 衣角拖曳效果:通过倾斜和位置偏移来模拟衣角被拖动
    group.current.rotation.z = hemOffset.x * 0.08; // 左右倾斜
    group.current.rotation.x = hemOffset.z * 0.06; // 前后倾斜
    group.current.position.x = hemOffset.x * 0.02; // 轻微位移
    group.current.position.z = hemOffset.z * 0.015;
  });
  
  return (
    <group
      ref={group}
      onPointerDown={handlePointerDown}
      onPointerMove={handlePointerMove}
      onPointerUp={handlePointerUp}
      onPointerLeave={handlePointerUp}
    >
      <primitive object={scene} />
    </group>
  );
}

// 预加载模型
useGLTF.preload('/model_textured.glb');