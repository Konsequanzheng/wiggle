'use client';

import { useRef, useState, useEffect } from 'react';
import { useFrame, useThree } from '@react-three/fiber';
import { useGLTF } from '@react-three/drei';
import * as THREE from 'three';

/**
 * 骨骼驱动的布料物理组件
 * 实现有机的弹性运动效果
 */
export function SkeletonClothPhysics() {
  const group = useRef<THREE.Group>(null);
  const { scene } = useGLTF('/model_textured.glb');
  const threeState = useThree();
  const { viewport, camera, raycaster } = threeState || {};
  
  // 拖拽状态
  const [isDragging, setIsDragging] = useState(false);
  const [velocity, setVelocity] = useState(0);
  const [rotation, setRotation] = useState(0);
  const [dragOffset, setDragOffset] = useState(new THREE.Vector3(0, 0, 0)); // 拖拽位置偏移
  const [tiltAngle, setTiltAngle] = useState(0); // 倾斜角度
  const previousMouseX = useRef(0);
  
  // Mesh引用
  const meshRef = useRef<THREE.Mesh | null>(null);
  
  // 虚拟骨骼系统
  const virtualBones = useRef<{
    position: THREE.Vector3;
    velocity: THREE.Vector3;
    angularVelocity: THREE.Euler;
    restRotation: THREE.Euler;
    rotation: THREE.Euler;
    influence: number; // 影响半径
  }[]>([]);
  
  // 顶点物理数据
  const originalPositions = useRef<Float32Array | null>(null);
  const vertexVelocities = useRef<Float32Array | null>(null);
  const vertexAccelerations = useRef<Float32Array | null>(null);
  const timeRef = useRef(0);
  
  // 拖拽交互状态
  const dragPoint = useRef<THREE.Vector3 | null>(null);
  const dragRadius = useRef(0.3); // 拖拽影响半径
  
  // 物理参数 - 自然垂坠的布料模拟
  const physics = {
    // 基础物理
    damping: 0.92,           // 提高阻尼以减少过度振荡,使运动更稳定
    mass: 0.12,              // 增加质量让布料更有重量感
    
    // 重力和外力
    gravity: new THREE.Vector3(0, -0.025, 0),  // 增强重力,让布料自然下垂
    windStrength: 0.002,     // 减弱风力,避免过度飘动
    windFrequency: 1.2,      // 降低风频率使风更柔和
    
    // 弹簧约束(模拟布料的结构)
    structuralStiffness: 0.15,  // 大幅降低结构刚度,使布料更柔软易垂坠
    shearStiffness: 0.08,       // 降低剪切刚度,允许更自然的折叠
    bendStiffness: 0.05,        // 降低弯曲刚度,让布料更容易产生自然褶皱
    
    // 拖拽交互
    dragStiffness: 0.6,      // 保持拖拽力度
    dragDamping: 0.7,        // 保持拖拽阻尼
    dragRadius: 0.45,        // 保持拖拽影响范围
    
    // 碰撞
    groundHeight: -0.6,      // 地面高度
    groundRestitution: 0.2,  // 降低地面反弹,使落地更自然
  }
  
  // 初始化网格和虚拟骨骼系统
  useEffect(() => {
    if (!scene) return;
    
    scene.traverse((child) => {
      if (child instanceof THREE.Mesh) {
        meshRef.current = child;
        const geometry = child.geometry;
        
        // 修复材质
        if (child.material) {
          const material = child.material as THREE.MeshStandardMaterial;
          material.side = THREE.DoubleSide;
          if (material.transparent) {
            material.opacity = Math.max(material.opacity, 0.95);
          }
          material.depthWrite = true;
          material.depthTest = true;
          material.needsUpdate = true;
        }
        
        // 保存原始顶点位置
        const positionAttr = geometry.getAttribute('position');
        const vertexCount = positionAttr.count;
        originalPositions.current = new Float32Array(positionAttr.array);
        
        // 初始化顶点速度和加速度
        vertexVelocities.current = new Float32Array(vertexCount * 3);
        vertexAccelerations.current = new Float32Array(vertexCount * 3);
        
        console.log(`Cloth physics initialized with ${vertexCount} vertices`);
        console.log('Advanced vertex-level physics enabled');
        
        // 创建虚拟骨骼 - 模拟T恤的骨骼结构
        // 沿着Y轴创建5个脊柱骨骼
        const numSpineBones = 5;
        for (let i = 0; i < numSpineBones; i++) {
          const t = i / (numSpineBones - 1); // 0 to 1
          virtualBones.current.push({
            position: new THREE.Vector3(0, -0.5 + t * 1.0, 0), // 沿Y轴分布
            velocity: new THREE.Vector3(),
            angularVelocity: new THREE.Euler(),
            restRotation: new THREE.Euler(),
            rotation: new THREE.Euler(),
            influence: 0.4 // 影响半径
          });
        }
        
        // 添加两个袖子骨骼
        virtualBones.current.push(
          {
            position: new THREE.Vector3(-0.5, 0.2, 0), // 左袖
            velocity: new THREE.Vector3(),
            angularVelocity: new THREE.Euler(),
            restRotation: new THREE.Euler(),
            rotation: new THREE.Euler(),
            influence: 0.35
          },
          {
            position: new THREE.Vector3(0.5, 0.2, 0), // 右袖
            velocity: new THREE.Vector3(),
            angularVelocity: new THREE.Euler(),
            restRotation: new THREE.Euler(),
            rotation: new THREE.Euler(),
            influence: 0.35
          }
        );
        
        console.log(`Virtual skeleton initialized with ${virtualBones.current.length} bones`);
        console.log(`Mesh has ${vertexCount} vertices`);
      }
    });
  }, [scene]);
  
  // 鼠标事件处理 - 精确拖拽
  const handlePointerDown = (e: any) => {
    if (!meshRef.current || !camera || !raycaster) return;
    
    setIsDragging(true);
    previousMouseX.current = e.clientX;
    
    // 使用射线检测获取点击点的世界坐标
    const canvas = (e.nativeEvent?.target || document.querySelector('canvas')) as HTMLElement;
    if (!canvas) return;
    const rect = canvas.getBoundingClientRect();
    const x = ((e.clientX - rect.left) / rect.width) * 2 - 1;
    const y = -((e.clientY - rect.top) / rect.height) * 2 + 1;
    
    raycaster.setFromCamera(new THREE.Vector2(x, y), camera);
    const intersects = raycaster.intersectObject(meshRef.current);
    
    if (intersects.length > 0) {
      // 保存拖拽点的局部坐标
      const point = intersects[0].point;
      dragPoint.current = meshRef.current.worldToLocal(point.clone());
    }
    
    e.stopPropagation();
  };
  
  const handlePointerMove = (e: any) => {
    if (!isDragging || !meshRef.current || !camera || !raycaster) return;
    
    const deltaX = e.clientX - previousMouseX.current;
    const rotationSpeed = 0.015;
    const newVelocity = deltaX * rotationSpeed;
    
    setVelocity(newVelocity);
    setRotation(prev => prev + newVelocity);
    
    // 计算拖拽偏移 - 产生强烈的拉扯感
    const dragForce = 0.8; // 拖拽力度系数,越大偏移越明显
    const offsetX = deltaX * dragForce * 0.01; // 水平偏移
    const offsetZ = Math.abs(deltaX) * dragForce * 0.008; // 向前拉扯
    
    setDragOffset(prev => new THREE.Vector3(
      prev.x + offsetX * 0.3,
      prev.y,
      prev.z - offsetZ * 0.3
    ));
    
    // 根据拖拽方向产生倾斜
    const maxTilt = 0.4; // 最大倾斜角度(弧度)
    const tiltSpeed = 0.05;
    const targetTilt = Math.sign(deltaX) * Math.min(Math.abs(deltaX) * 0.01, maxTilt);
    setTiltAngle(prev => prev + (targetTilt - prev) * tiltSpeed);
    
    previousMouseX.current = e.clientX;
    
    // 更新拖拽点位置
    if (dragPoint.current) {
      const canvas = (e.nativeEvent?.target || document.querySelector('canvas')) as HTMLElement;
      if (!canvas) return;
      const rect = canvas.getBoundingClientRect();
      const x = ((e.clientX - rect.left) / rect.width) * 2 - 1;
      const y = -((e.clientY - rect.top) / rect.height) * 2 + 1;
      
      raycaster.setFromCamera(new THREE.Vector2(x, y), camera);
      const intersects = raycaster.intersectObject(meshRef.current);
      
      if (intersects.length > 0) {
        const point = intersects[0].point;
        dragPoint.current = meshRef.current.worldToLocal(point.clone());
      }
    }
    
    e.stopPropagation();
  };
  
  const handlePointerUp = () => {
    setIsDragging(false);
    dragPoint.current = null;
    // 不立即重置偏移,让它自然回弹
  };
  
  // 高级顶点级布料物理模拟
  useFrame((state, delta) => {
    if (!group.current || !meshRef.current || !originalPositions.current || 
        !vertexVelocities.current || !vertexAccelerations.current) return;
    
    const mesh = meshRef.current;
    const geometry = mesh.geometry;
    const positionAttr = geometry.getAttribute('position');
    const time = state.clock.elapsedTime;
    timeRef.current = time;
    
    const vertexCount = positionAttr.count;
    const dt = Math.min(delta, 0.033); // 限制时间步长
    
    // 重置加速度
    for (let i = 0; i < vertexCount * 3; i++) {
      vertexAccelerations.current[i] = 0;
    }
    
    // 1. 应用外力 (重力、风力)
    for (let i = 0; i < vertexCount; i++) {
      const idx = i * 3;
      
      // 重力
      vertexAccelerations.current[idx] += physics.gravity.x;
      vertexAccelerations.current[idx + 1] += physics.gravity.y;
      vertexAccelerations.current[idx + 2] += physics.gravity.z;
      
      // 风力 (使用噪声模拟自然风)
      const windX = Math.sin(time * physics.windFrequency + i * 0.1) * physics.windStrength;
      const windZ = Math.cos(time * physics.windFrequency * 0.7 + i * 0.15) * physics.windStrength;
      vertexAccelerations.current[idx] += windX;
      vertexAccelerations.current[idx + 2] += windZ;
      
      // 局部微观褶皱扰动 (自然松弛效果)
      const wrinkleFreq = 3.0; // 降低褶皱频率,使表面更平滑
      const wrinkleAmp = 0.0008; // 大幅降低褶皱幅度,让表面更自然松弛
      const wrinkleX = Math.sin(time * 1.5 + i * wrinkleFreq + positionAttr.array[idx] * 5) * wrinkleAmp;
      const wrinkleY = Math.cos(time * 1.2 + i * wrinkleFreq * 0.8 + positionAttr.array[idx + 1] * 5) * wrinkleAmp;
      const wrinkleZ = Math.sin(time * 1.3 + i * wrinkleFreq * 1.2 + positionAttr.array[idx + 2] * 5) * wrinkleAmp;
      vertexAccelerations.current[idx] += wrinkleX;
      vertexAccelerations.current[idx + 1] += wrinkleY;
      vertexAccelerations.current[idx + 2] += wrinkleZ;
    }
    
    // 2. 应用弹簧约束 (相邻顶点之间)
    // 使用优化的邻近检测,只在小范围内检测
    const neighborRange = 30; // 减少邻域范围提升性能
    for (let i = 0; i < vertexCount; i++) {
      const idx = i * 3;
      const x = positionAttr.array[idx];
      const y = positionAttr.array[idx + 1];
      const z = positionAttr.array[idx + 2];
      
      const origX = originalPositions.current[idx];
      const origY = originalPositions.current[idx + 1];
      const origZ = originalPositions.current[idx + 2];
      
      // 对每个顶点,找到邻近顶点并施加弹簧力
      for (let j = i + 1; j < Math.min(i + neighborRange, vertexCount); j++) {
        const jdx = j * 3;
        const jx = positionAttr.array[jdx];
        const jy = positionAttr.array[jdx + 1];
        const jz = positionAttr.array[jdx + 2];
        
        const origJx = originalPositions.current[jdx];
        const origJy = originalPositions.current[jdx + 1];
        const origJz = originalPositions.current[jdx + 2];
        
        // 计算原始距离
        const origDx = origJx - origX;
        const origDy = origJy - origY;
        const origDz = origJz - origZ;
        const origDist = Math.sqrt(origDx * origDx + origDy * origDy + origDz * origDz);
        
        // 只对原本就接近的顶点施加约束
        if (origDist < 0.05) {
          // 计算当前距离
          const dx = jx - x;
          const dy = jy - y;
          const dz = jz - z;
          const dist = Math.sqrt(dx * dx + dy * dy + dz * dz);
          
          if (dist > 0.0001) {
            // 弹簧力 = 刚度 * 距离差
            const diff = dist - origDist;
            const force = diff * physics.structuralStiffness;
            
            const fx = (dx / dist) * force;
            const fy = (dy / dist) * force;
            const fz = (dz / dist) * force;
            
            // 对两个顶点施加相反的力
            vertexAccelerations.current[idx] += fx;
            vertexAccelerations.current[idx + 1] += fy;
            vertexAccelerations.current[idx + 2] += fz;
            
            vertexAccelerations.current[jdx] -= fx;
            vertexAccelerations.current[jdx + 1] -= fy;
            vertexAccelerations.current[jdx + 2] -= fz;
          }
        }
      }
      
      // 添加剪切约束 (对角顶点)
      for (let j = i + neighborRange; j < Math.min(i + neighborRange * 2, vertexCount); j += 3) {
        const jdx = j * 3;
        const jx = positionAttr.array[jdx];
        const jy = positionAttr.array[jdx + 1];
        const jz = positionAttr.array[jdx + 2];
        
        const origJx = originalPositions.current[jdx];
        const origJy = originalPositions.current[jdx + 1];
        const origJz = originalPositions.current[jdx + 2];
        
        const origDx = origJx - origX;
        const origDy = origJy - origY;
        const origDz = origJz - origZ;
        const origDist = Math.sqrt(origDx * origDx + origDy * origDy + origDz * origDz);
        
        if (origDist < 0.08) {
          const dx = jx - x;
          const dy = jy - y;
          const dz = jz - z;
          const dist = Math.sqrt(dx * dx + dy * dy + dz * dz);
          
          if (dist > 0.0001) {
            const diff = dist - origDist;
            const force = diff * physics.shearStiffness;
            const fx = (dx / dist) * force;
            const fy = (dy / dist) * force;
            const fz = (dz / dist) * force;
            
            vertexAccelerations.current[idx] += fx;
            vertexAccelerations.current[idx + 1] += fy;
            vertexAccelerations.current[idx + 2] += fz;
          }
        }
      }
      
      // 保持顶点接近原始位置 (形状保持 - 弯曲约束)
      const restoreX = (origX - x) * physics.bendStiffness;
      const restoreY = (origY - y) * physics.bendStiffness;
      const restoreZ = (origZ - z) * physics.bendStiffness;
      
      vertexAccelerations.current[idx] += restoreX;
      vertexAccelerations.current[idx + 1] += restoreY;
      vertexAccelerations.current[idx + 2] += restoreZ;
    }
    
    // 3. 应用拖拽交互力 (增强版)
    if (isDragging && dragPoint.current) {
      const dragRadius = physics.dragRadius * 2.5; // 扩大拖拽影响半径
      const dragStiffness = physics.dragStiffness * 3.0; // 增强拖拽力度
      const dragDamping = physics.dragDamping;
      
      for (let i = 0; i < vertexCount; i++) {
        const idx = i * 3;
        const x = positionAttr.array[idx];
        const y = positionAttr.array[idx + 1];
        const z = positionAttr.array[idx + 2];
        
        // 计算到拖拽点的距离
        const dx = dragPoint.current.x - x;
        const dy = dragPoint.current.y - y;
        const dz = dragPoint.current.z - z;
        const dist = Math.sqrt(dx * dx + dy * dy + dz * dz);
        
        if (dist < dragRadius) {
          // 非线性影响衰减 (中心区域影响更强)
          const normalizedDist = dist / dragRadius;
          const influence = Math.pow(1 - normalizedDist, 2.5); // 使用幂函数增强中心影响
          const force = dragStiffness * influence;
          
          vertexAccelerations.current[idx] += (dx / dist) * force;
          vertexAccelerations.current[idx + 1] += (dy / dist) * force;
          vertexAccelerations.current[idx + 2] += (dz / dist) * force;
          
          // 添加涟漪扩散效果
          const ripplePhase = time * 8.0 - dist * 15.0;
          const rippleStrength = Math.sin(ripplePhase) * 0.008 * influence;
          vertexAccelerations.current[idx + 1] += rippleStrength;
          
          // 添加径向扩散力(模拟布料被拉扯时的褶皱扩散)
          const radialForce = force * 0.3;
          vertexAccelerations.current[idx] += (x - dragPoint.current.x) / dist * radialForce * Math.sin(time * 3.0);
          vertexAccelerations.current[idx + 2] += (z - dragPoint.current.z) / dist * radialForce * Math.cos(time * 3.0);
          
          // 额外的阻尼
          vertexVelocities.current[idx] *= (1 - dragDamping * influence);
          vertexVelocities.current[idx + 1] *= (1 - dragDamping * influence);
          vertexVelocities.current[idx + 2] *= (1 - dragDamping * influence);
        }
      }
    }
    
    // 4. 速度积分和位置更新
    for (let i = 0; i < vertexCount; i++) {
      const idx = i * 3;
      
      // 应用加速度到速度 (Verlet积分)
      vertexVelocities.current[idx] += vertexAccelerations.current[idx] * dt;
      vertexVelocities.current[idx + 1] += vertexAccelerations.current[idx + 1] * dt;
      vertexVelocities.current[idx + 2] += vertexAccelerations.current[idx + 2] * dt;
      
      // 全局阻尼
      vertexVelocities.current[idx] *= physics.damping;
      vertexVelocities.current[idx + 1] *= physics.damping;
      vertexVelocities.current[idx + 2] *= physics.damping;
      
      // 更新位置
      positionAttr.array[idx] += vertexVelocities.current[idx] * dt;
      positionAttr.array[idx + 1] += vertexVelocities.current[idx + 1] * dt;
      positionAttr.array[idx + 2] += vertexVelocities.current[idx + 2] * dt;
    }
    
    // 5. 地面碰撞检测
    const groundY = physics.groundHeight;
    const restitution = physics.groundRestitution;
    for (let i = 0; i < vertexCount; i++) {
      const idx = i * 3;
      if (positionAttr.array[idx + 1] < groundY) {
        positionAttr.array[idx + 1] = groundY;
        vertexVelocities.current[idx + 1] *= -restitution;
      }
    }
    
    // 6. 自碰撞检测 (简化版 - 防止顶点过于接近)
    const collisionThreshold = 0.02; // 最小顶点间距
    const collisionSteps = Math.floor(vertexCount / 100); // 采样以提升性能
    for (let i = 0; i < vertexCount; i += collisionSteps) {
      const idx = i * 3;
      const x1 = positionAttr.array[idx];
      const y1 = positionAttr.array[idx + 1];
      const z1 = positionAttr.array[idx + 2];
      
      for (let j = i + collisionSteps; j < vertexCount; j += collisionSteps) {
        const jdx = j * 3;
        const x2 = positionAttr.array[jdx];
        const y2 = positionAttr.array[jdx + 1];
        const z2 = positionAttr.array[jdx + 2];
        
        const dx = x2 - x1;
        const dy = y2 - y1;
        const dz = z2 - z1;
        const dist = Math.sqrt(dx * dx + dy * dy + dz * dz);
        
        // 如果顶点过于接近,施加排斥力
        if (dist < collisionThreshold && dist > 0.0001) {
          const pushForce = (collisionThreshold - dist) * 0.5;
          const nx = dx / dist;
          const ny = dy / dist;
          const nz = dz / dist;
          
          // 推开两个顶点
          positionAttr.array[idx] -= nx * pushForce;
          positionAttr.array[idx + 1] -= ny * pushForce;
          positionAttr.array[idx + 2] -= nz * pushForce;
          
          positionAttr.array[jdx] += nx * pushForce;
          positionAttr.array[jdx + 1] += ny * pushForce;
          positionAttr.array[jdx + 2] += nz * pushForce;
          
          // 减少速度
          vertexVelocities.current[idx] *= 0.8;
          vertexVelocities.current[idx + 1] *= 0.8;
          vertexVelocities.current[idx + 2] *= 0.8;
          vertexVelocities.current[jdx] *= 0.8;
          vertexVelocities.current[jdx + 1] *= 0.8;
          vertexVelocities.current[jdx + 2] *= 0.8;
        }
      }
    }
    
    // 标记几何体需要更新
    positionAttr.needsUpdate = true;
    
    // 应用旋转和位置变换
    if (group.current) {
      group.current.rotation.y = rotation;
      
      // 应用拖拽偏移
      group.current.position.x = dragOffset.x;
      group.current.position.y = dragOffset.y;
      group.current.position.z = dragOffset.z;
      
      // 应用倾斜效果
      group.current.rotation.z = tiltAngle;
      // 添加轻微的X轴倾斜增强3D效果
      group.current.rotation.x = tiltAngle * 0.3;
    }
    
    // 应用惯性衰减 (不在拖拽时)
    if (!isDragging) {
      // 速度衰减
      if (Math.abs(velocity) > 0.001) {
        setVelocity(prev => prev * 0.95);
        setRotation(prev => prev + velocity);
      }
      
      // 位置回弹 - 使用弹性动画
      const springStrength = 0.15; // 回弹强度
      const dampingFactor = 0.85; // 阻尼系数
      
      setDragOffset(prev => {
        const newOffset = new THREE.Vector3(
          prev.x * dampingFactor,
          prev.y * dampingFactor,
          prev.z * dampingFactor
        );
        
        // 添加回弹力
        newOffset.x -= prev.x * springStrength;
        newOffset.y -= prev.y * springStrength;
        newOffset.z -= prev.z * springStrength;
        
        // 如果接近原点,直接归零避免抖动
        if (newOffset.length() < 0.001) {
          return new THREE.Vector3(0, 0, 0);
        }
        
        return newOffset;
      });
      
      // 倾斜角度回弹
      setTiltAngle(prev => {
        const newTilt = prev * 0.9;
        return Math.abs(newTilt) < 0.001 ? 0 : newTilt;
      });
    }
  });
  
  return (
    <group
      ref={group}
      position={[0, 0, 0]}
      scale={[1.5, 1.5, 1.5]}
      onPointerDown={handlePointerDown}
      onPointerMove={handlePointerMove}
      onPointerUp={handlePointerUp}
      onPointerLeave={handlePointerUp}
    >
      <primitive object={scene} />
    </group>
  );
}