import { useRef, useMemo } from 'react';
import { Canvas, useFrame } from '@react-three/fiber';
import { OrbitControls, Text, Line } from '@react-three/drei';
import * as THREE from 'three';
import type { BlochVector } from '../types/quantum';
import HelpBubble from './HelpBubble';
import { useLearning } from '../contexts/LearningContext';

interface BlochSphereViewProps {
  vectors: BlochVector[];
}

const COLORS = [
  '#c8ad7f', '#e07a5f', '#81b29a', '#f2cc8f',
  '#d4a5a5', '#7eb8c9', '#b8a898', '#e8a87c',
];

function WireframeSphere() {
  return (
    <group>
      {/* Main sphere wireframe */}
      <mesh>
        <sphereGeometry args={[1, 32, 16]} />
        <meshBasicMaterial
          color="#2c2c2c"
          wireframe
          transparent
          opacity={0.15}
        />
      </mesh>

      {/* Equator circle */}
      <Line
        points={Array.from({ length: 65 }, (_, i) => {
          const t = (i / 64) * Math.PI * 2;
          return [Math.cos(t), 0, Math.sin(t)] as [number, number, number];
        })}
        color="#3a3a3a"
        lineWidth={1}
      />

      {/* Prime meridian (XZ plane) */}
      <Line
        points={Array.from({ length: 65 }, (_, i) => {
          const t = (i / 64) * Math.PI * 2;
          return [Math.cos(t), Math.sin(t), 0] as [number, number, number];
        })}
        color="#333333"
        lineWidth={0.5}
      />

      {/* YZ meridian */}
      <Line
        points={Array.from({ length: 65 }, (_, i) => {
          const t = (i / 64) * Math.PI * 2;
          return [0, Math.sin(t), Math.cos(t)] as [number, number, number];
        })}
        color="#333333"
        lineWidth={0.5}
      />
    </group>
  );
}

function Axes() {
  return (
    <group>
      {/* X axis */}
      <Line points={[[-1.3, 0, 0], [1.3, 0, 0]]} color="#ef4444" lineWidth={1} />
      <Text position={[1.45, 0, 0]} fontSize={0.12} color="#ef4444">X</Text>

      {/* Y axis */}
      <Line points={[[0, 0, -1.3], [0, 0, 1.3]]} color="#22c55e" lineWidth={1} />
      <Text position={[0, 0, 1.45]} fontSize={0.12} color="#22c55e">Y</Text>

      {/* Z axis */}
      <Line points={[[0, -1.3, 0], [0, 1.3, 0]]} color="#3b82f6" lineWidth={1} />
      <Text position={[0, 1.45, 0]} fontSize={0.12} color="#3b82f6">|0⟩</Text>
      <Text position={[0, -1.45, 0]} fontSize={0.12} color="#3b82f6">|1⟩</Text>

      {/* Cardinal point labels */}
      <Text position={[1.2, 0.12, 0]} fontSize={0.08} color="#888">|+⟩</Text>
      <Text position={[-1.2, 0.12, 0]} fontSize={0.08} color="#888">|−⟩</Text>
      <Text position={[0, 0.12, 1.2]} fontSize={0.08} color="#888">|+i⟩</Text>
      <Text position={[0, 0.12, -1.2]} fontSize={0.08} color="#888">|−i⟩</Text>
    </group>
  );
}

function StateVector({ vector, color, label }: { vector: BlochVector; color: string; label: string }) {
  const meshRef = useRef<THREE.Mesh>(null);
  const arrowEnd = useMemo(
    () => new THREE.Vector3(vector.x, vector.z, vector.y),
    [vector.x, vector.y, vector.z]
  );
  const origin = new THREE.Vector3(0, 0, 0);

  // Purity = |r| (1 = pure, <1 = mixed/entangled)
  const purity = Math.sqrt(vector.x ** 2 + vector.y ** 2 + vector.z ** 2);

  useFrame(() => {
    if (meshRef.current) {
      meshRef.current.position.copy(arrowEnd);
    }
  });

  return (
    <group>
      {/* Vector line */}
      <Line
        points={[
          [origin.x, origin.y, origin.z],
          [arrowEnd.x, arrowEnd.y, arrowEnd.z],
        ]}
        color={color}
        lineWidth={2.5}
      />

      {/* Arrow tip sphere */}
      <mesh ref={meshRef} position={[arrowEnd.x, arrowEnd.y, arrowEnd.z]}>
        <sphereGeometry args={[0.06, 16, 16]} />
        <meshBasicMaterial color={color} />
      </mesh>

      {/* Label */}
      <Text
        position={[
          arrowEnd.x * 1.15,
          arrowEnd.y * 1.15 + 0.08,
          arrowEnd.z * 1.15,
        ]}
        fontSize={0.1}
        color={color}
      >
        {label} ({(purity * 100).toFixed(0)}%)
      </Text>
    </group>
  );
}

export default function BlochSphere({ vectors }: BlochSphereViewProps) {
  const { learningMode } = useLearning();
  if (!vectors.length) return null;

  return (
    <div className="flex flex-col gap-2">
      <div className="flex items-center gap-2">
        <h3 className="text-sm font-bold" style={{ color: 'var(--text-secondary)' }}>
          Bloch Sphere
        </h3>
        {learningMode && (
          <HelpBubble title="Bloch Sphere">
            The Bloch sphere represents a single qubit's state as a point on a sphere.
            The north pole (top) is |0{'>'}, the south pole (bottom) is |1{'>'}.
            Points on the equator are superposition states.
            When a qubit is entangled with others, its arrow shrinks toward the center (mixed state).
            Click and drag to rotate the view.
          </HelpBubble>
        )}
      </div>

      <div
        className="rounded-lg overflow-hidden"
        style={{
          height: '360px',
          background: 'var(--bg-primary)',
          border: '1px solid var(--border)',
        }}
      >
        <Canvas camera={{ position: [2.2, 1.8, 2.2], fov: 40 }}>
          <ambientLight intensity={0.6} />
          <pointLight position={[5, 5, 5]} intensity={0.4} />

          <WireframeSphere />
          <Axes />

          {vectors.map((v, i) => (
            <StateVector
              key={i}
              vector={v}
              color={COLORS[i % COLORS.length]}
              label={`q${v.qubit}`}
            />
          ))}

          <OrbitControls
            enableDamping
            dampingFactor={0.1}
            enableZoom={true}
            minDistance={2}
            maxDistance={6}
          />
        </Canvas>
      </div>

      {/* Bloch vector values */}
      <div className="flex flex-wrap gap-2">
        {vectors.map((v, i) => {
          const purity = Math.sqrt(v.x ** 2 + v.y ** 2 + v.z ** 2);
          return (
            <div
              key={i}
              className="px-2 py-1 rounded text-xs"
              style={{
                background: 'var(--bg-tertiary)',
                border: `1px solid ${COLORS[i % COLORS.length]}44`,
              }}
            >
              <span style={{ color: COLORS[i % COLORS.length] }} className="font-bold">q{v.qubit}</span>
              <span className="ml-2" style={{ color: 'var(--text-secondary)' }}>
                ({v.x.toFixed(3)}, {v.y.toFixed(3)}, {v.z.toFixed(3)})
              </span>
              <span className="ml-1" style={{ color: purity > 0.99 ? 'var(--success)' : 'var(--warning)' }}>
                {purity > 0.99 ? 'pure' : `mixed ${(purity * 100).toFixed(0)}%`}
              </span>
            </div>
          );
        })}
      </div>
    </div>
  );
}
