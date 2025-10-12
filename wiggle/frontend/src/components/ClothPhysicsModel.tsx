'use client';

import { useRef, useState, useEffect } from 'react';
import { useFrame, useThree } from '@react-three/fiber';
import { useGLTF } from '@react-three/drei';
import * as THREE from 'three';

export function ClothPhysicsModel() {
  const group = useRef<THREE.Group>(null);
  const { scene } = useGLTF('/model_textured.glb');
  const { viewport } = useThree();
  
  // 旋转状态
  const [isDragging, setIsDragging] = useState(false);
  const [rotation, setRotation] = useState(0);
  const [velocity, setVelocity] = useState(0);
  const previousMouseX = useRef(0);
  
  // 鼠标点击位置和旋转中心
  const clickPoint = useRef<THREE.Vector3>(new THREE.Vector3());
  const rotationCenter = useRef<THREE.Vector3>(new THREE.Vector3());
  const dragOffset = useRef<THREE.Vector3>(new THREE.Vector3());
  
  // 布料物理参数
  const meshRef = useRef<THREE.Mesh | null>(null);
  const originalPositions = useRef<Float32Array | null>(null);
  const vertexVelocities = useRef<Float32Array | null>(null);
  const timeRef = useRef(0);
  
  // 初始化顶点数据
  useEffect(() => {
    if (!scene) return;
    
    scene.traverse((child) => {
      if (child instanceof THREE.Mesh && child.geometry) {
        meshRef.current = child;
        const geometry = child.geometry;
        
        // 修复材质问题
        if (child.material) {
          const material = child.material as THREE.MeshStandardMaterial;
          // 设置双面渲染,避免穿模
          material.side = THREE.DoubleSide;
          // 调整透明度设置
          if (material.transparent) {
            material.opacity = Math.max(material.opacity, 0.95); // 确保不过度透明
          }
          // 禁用深度写入可能导致的问题
          material.depthWrite = true;
          material.depthTest = true;
          // 更新材质
          material.needsUpdate = true;
        }
        
        // 确保几何体有position属性
        if (geometry.attributes.position) {
          const positionAttribute = geometry.attributes.position;
          const count = positionAttribute.count;
          
          // 保存原始位置
          originalPositions.current = new Float32Array(positionAttribute.array);
          
          // 初始化顶点速度
          vertexVelocities.current = new Float32Array(count * 3);
          
          // 克隆几何体以便修改
          if (!geometry.attributes.position.array) {
            geometry.setAttribute('position', 
              new THREE.BufferAttribute(new Float32Array(originalPositions.current), 3)
            );
          }
        }
      }
    });
  }, [scene]);
  
  // 鼠标事件处理
  const handlePointerDown = (e: any) => {
    setIsDragging(true);
    previousMouseX.current = e.clientX;
    
    // 获取鼠标点击位置的3D坐标
    if (e.intersections && e.intersections.length > 0) {
      const intersection = e.intersections[0];
      clickPoint.current.copy(intersection.point);
      
      // 设置旋转中心为点击位置
      if (group.current) {
        // 将世界坐标转换为局部坐标
        const localPoint = group.current.worldToLocal(clickPoint.current.clone());
        rotationCenter.current.copy(localPoint);
        
        // 计算从模型中心到点击点的偏移
        dragOffset.current.copy(localPoint);
      }
    }
    
    e.stopPropagation();
  };
  
  const handlePointerMove = (e: any) => {
    if (!isDragging) return;
    
    const deltaX = e.clientX - previousMouseX.current;
    // 增强旋转速度,使甩动更明显
    const rotationSpeed = deltaX * 0.015;
    
    setRotation(prev => prev + rotationSpeed);
    setVelocity(rotationSpeed);
    
    previousMouseX.current = e.clientX;
    e.stopPropagation();
  };
  
  const handlePointerUp = () => {
    setIsDragging(false);
  };
  
  // 布料物理模拟
  useFrame((state, delta) => {
    if (!group.current || !meshRef.current || !originalPositions.current || !vertexVelocities.current) return;
    
    timeRef.current += delta;
    
    // 惯性旋转 - 降低阻尼使甩动更流畅持久
    if (!isDragging && Math.abs(velocity) > 0.001) {
      setRotation(prev => prev + velocity);
      setVelocity(prev => prev * 0.96); // 提高保留率,使惯性更强
    }
    
    // 应用旋转到group
    group.current.rotation.y = rotation;
    
    const geometry = meshRef.current.geometry;
    const positionAttribute = geometry.attributes.position;
    const positions = positionAttribute.array as Float32Array;
    const original = originalPositions.current;
    const velocities = vertexVelocities.current;
    
    // 风力参数 - 基于旋转速度的径向风力
    const rotationForce = Math.abs(velocity) * 35; // 旋转产生的离心力强度
    const dragMultiplier = isDragging ? 2.5 : 1.0; // 拖拽时增强效果
    
    // 更新每个顶点
    for (let i = 0; i < positions.length; i += 3) {
      const x = original[i];
      const y = original[i + 1];
      const z = original[i + 2];
      
      // 计算顶点相对于旋转中心的方向和距离
      const dx = x - rotationCenter.current.x;
      const dy = y - rotationCenter.current.y;
      const dz = z - rotationCenter.current.z;
      const distFromRotationCenter = Math.sqrt(dx * dx + dy * dy + dz * dz);
      
      // 归一化方向向量 (从旋转中心指向顶点)
      const radialDirX = distFromRotationCenter > 0.001 ? dx / distFromRotationCenter : 0;
      const radialDirY = distFromRotationCenter > 0.001 ? dy / distFromRotationCenter : 0;
      const radialDirZ = distFromRotationCenter > 0.001 ? dz / distFromRotationCenter : 0;
      
      // 甩动因子 - 距离旋转中心越远,受力越大
      const swingFactor = Math.min(distFromRotationCenter * 2.0, 2.5);
      
      // 计算顶点的风力影响 (越往下的顶点受风力影响越大)
      const heightFactor = Math.max(0, (y + 1) / 2);
      const waveFactor = heightFactor * 0.85 * swingFactor; // 结合甩动因子
      
      // 袖子区域检测 - 根据X坐标判断是否为袖子部分
      const isSleeveArea = Math.abs(x) > 0.3;
      const sleeveGravity = isSleeveArea ? 0.025 * (1 - y) : 0; // 袖子下垂效果
      
      // 计算到中心的距离,用于模拟褶皱和扭曲
      const distFromCenter = Math.sqrt(x * x + z * z);
      
      // 螺旋扭曲效果 - 根据旋转速度和距离产生表面扭曲
      const spiralAngle = Math.atan2(z, x); // 当前顶点的角度
      const spiralTwist = Math.abs(velocity) * distFromCenter * 8; // 扭曲强度随旋转速度增加
      const twistPhase = spiralAngle + spiralTwist * (isDragging ? 1.5 : 0.5);
      
      // 增强褶皱因子,加入扭曲效果
      const wrinkleFactor = (
        Math.sin(distFromCenter * 8 + timeRef.current * 2) * 0.15 + 
        Math.sin(twistPhase * 3) * 0.2 * Math.abs(velocity)
      ) * swingFactor;
      
      // 多层波浪效果 - 增加更多细节层次和扭曲变形
      const wave1 = Math.sin(timeRef.current * 3.5 + x * 3 + z * 3 + twistPhase) * waveFactor;
      const wave2 = Math.sin(timeRef.current * 5.2 + x * 4 - z * 2 + twistPhase * 0.5) * waveFactor * 0.6;
      const wave3 = Math.cos(timeRef.current * 2.8 + z * 3.5 + twistPhase * 0.8) * waveFactor * 0.4;
      const wave4 = Math.sin(timeRef.current * 7 + x * 5 + z * 1.5 + twistPhase * 1.2) * waveFactor * 0.35; // 高频扭曲细节
      const wave5 = Math.cos(timeRef.current * 4.3 - x * 2.5 + z * 2.5 - twistPhase * 0.6) * waveFactor * 0.4; // 褶皱扭曲细节
      
      // 飞扬效果 - 表面翻卷和飞起的感觉
      const flyingEffect = Math.sin(twistPhase * 2 + timeRef.current * 4) * Math.abs(velocity) * swingFactor * 0.25;
      const surfaceTwist = Math.cos(spiralAngle * 4 + timeRef.current * 3 + distFromCenter * 6) * Math.abs(velocity) * 0.18;
      
      // 重力效果 - 让布料有下垂感,加强袖子的自然下垂
      const gravityEffect = heightFactor * 0.02 * Math.sin(timeRef.current * 2 + x) + sleeveGravity;
      
      // 径向风力 - 沿着从旋转中心到顶点的方向施加力
      const radialForce = rotationForce * swingFactor * dragMultiplier * waveFactor;
      
      // 添加切向力分量 (垂直于径向,产生旋转拖尾效果)
      const tangentialForceX = -radialDirZ * rotationForce * 0.3 * swingFactor;
      const tangentialForceZ = radialDirX * rotationForce * 0.3 * swingFactor;
      
      // 垂直方向的波动效果
      const verticalWave = Math.sin(timeRef.current * 1.5 + x * 2) * 0.3 * waveFactor;
      
      // 综合风力作用 - 加入表面扭曲和飞扬效果
      const windForceX = (radialDirX * radialForce + tangentialForceX) * (wave1 + wave2 + wrinkleFactor) + surfaceTwist;
      const windForceY = (radialDirY * radialForce * 0.5 + verticalWave) * (wave3 + wave5) - gravityEffect + flyingEffect;
      const windForceZ = (radialDirZ * radialForce + tangentialForceZ) * (wave1 + wave3 + wrinkleFactor) + surfaceTwist * 0.8;
      
      // 弹簧力 (拉回原位) - 调整强度让布料更柔软
      const springForceX = (original[i] - positions[i]) * 0.18;
      const springForceY = (original[i + 1] - positions[i + 1]) * 0.12;
      const springForceZ = (original[i + 2] - positions[i + 2]) * 0.18;
      
      // 阻尼力 - 降低阻尼让运动更流畅
      const dampingX = velocities[i] * 0.85;
      const dampingY = velocities[i + 1] * 0.82;
      const dampingZ = velocities[i + 2] * 0.85;
      
      // 更新速度
      velocities[i] += windForceX + springForceX - dampingX;
      velocities[i + 1] += windForceY + springForceY - dampingY;
      velocities[i + 2] += windForceZ + springForceZ - dampingZ;
      
      // 更新位置
      positions[i] += velocities[i] * delta * 2.5;
      positions[i + 1] += velocities[i + 1] * delta * 2.2;
      positions[i + 2] += velocities[i + 2] * delta * 2.5;
      
      // 动态限制位移幅度 - 根据距离旋转中心的远近调整
      const maxDisplacementXZ = 0.08 + swingFactor * 0.04; // 远离中心的部分允许更大位移
      const maxDisplacementY = 0.06 + swingFactor * 0.03;
      
      positions[i] = Math.max(original[i] - maxDisplacementXZ, Math.min(original[i] + maxDisplacementXZ, positions[i]));
      positions[i + 1] = Math.max(original[i + 1] - maxDisplacementY, Math.min(original[i + 1] + maxDisplacementY, positions[i + 1]));
      positions[i + 2] = Math.max(original[i + 2] - maxDisplacementXZ, Math.min(original[i + 2] + maxDisplacementXZ, positions[i + 2]));
      
      // 添加细微的褶皱和起伏细节
      const microDetail = (wave4 + wave5) * 0.015;
      positions[i] += microDetail * Math.cos(x * 10);
      positions[i + 1] += microDetail * Math.sin(y * 8);
      positions[i + 2] += microDetail * Math.sin(z * 10);
    }
    
    // 标记需要更新
    positionAttribute.needsUpdate = true;
    
    // 重新计算法线以保持光照正确
    geometry.computeVertexNormals();
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