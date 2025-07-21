// frontend/src/CodeCity.js - CORRECTED SCOPE FIX

import React, { useState } from 'react';
import { Canvas } from '@react-three/fiber';
// 'Text' has been removed from the import as it was unused
import { OrbitControls } from '@react-three/drei';

// Helper function to calculate max complexity from a file's functions array
const getMaxComplexity = (functions) => {
  if (!functions || functions.length === 0) return 0;
  return Math.max(...functions.map(func => func.complexity || 0));
};

// Helper function to determine building color
const getColorByComplexity = (complexity) => {
  if (complexity < 10) return '#4caf50'; // Green
  if (complexity < 20) return '#ff9800'; // Orange
  return '#f44336';      // Red
};


// The Building component now receives its height as a prop
const Building = ({ file, position, height }) => {
  const [isHovered, setIsHovered] = useState(false);
  const maxComplexity = getMaxComplexity(file.functions);
  const color = getColorByComplexity(maxComplexity);

  return (
    <mesh
      position={position}
      onPointerOver={() => setIsHovered(true)}
      onPointerOut={() => setIsHovered(false)}
      onClick={() => console.log(file.relative_path)}
    >
      {/* It now uses the 'height' prop for its geometry */}
      <boxGeometry args={[2, height, 2]} />
      <meshStandardMaterial color={isHovered ? 'lightblue' : color} />
    </mesh>
  );
};


const CodeCity = ({ data }) => {
  const filesToRender = data?.files || [];

  return (
    <div style={{ height: '500px', width: '100%', marginTop: '2rem', border: '1px solid #ddd', background: '#f0f0f0' }}>
      <Canvas camera={{ position: [15, 15, 30], fov: 50 }}>
        <ambientLight intensity={0.6} />
        <directionalLight position={[10, 10, 5]} intensity={1} />
        <directionalLight position={[-10, 10, -5]} intensity={0.5} />
        <OrbitControls />

        {filesToRender.map((file, index) => {
          // *** THE BUG FIX IS HERE ***
          // We calculate height in the parent component, where it's needed for the position.
          const height = (file.lines_of_code || 10) / 50 + 0.2; // Add a base height so no building is invisible
          
          const gridX = (index % 10) * 3;
          const gridZ = Math.floor(index / 10) * 3;
          
          // Now we can safely use 'height' here AND pass it as a prop
          return (
            <Building 
              key={file.relative_path} 
              file={file} 
              position={[gridX, height / 2, gridZ]} 
              height={height} 
            />
          );
        })}

        <mesh rotation={[-Math.PI / 2, 0, 0]} position={[0, -0.01, 0]}>
          <planeGeometry args={[100, 100]} />
          <meshStandardMaterial color="#ddd" />
        </mesh>
      </Canvas>
    </div>
  );
};

export default CodeCity;