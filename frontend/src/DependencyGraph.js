import React, { useMemo } from 'react';
import ReactFlow, { Background, Controls } from 'reactflow';
import 'reactflow/dist/style.css';

const DependencyGraph = ({ data }) => {
  // Transform nodes and edges for ReactFlow format
  const { nodes, edges } = useMemo(() => {
    if (!data?.graph?.nodes || !data?.graph?.edges) {
      return { nodes: [], edges: [] };
    }

    // Transform nodes - calculate positions in a grid layout
    const transformedNodes = data.graph.nodes.map((node, index) => {
      // Simple grid layout calculation
      const gridSize = Math.ceil(Math.sqrt(data.graph.nodes.length));
      const row = Math.floor(index / gridSize);
      const col = index % gridSize;
      
      return {
        id: node.id || `node-${index}`,
        position: {
          x: col * 200 + Math.random() * 50, // Add some randomness to avoid overlap
          y: row * 150 + Math.random() * 50,
        },
        data: {
          label: node.label || node.name || node.id || `Node ${index}`,
        },
        type: 'default',
        // Optional: add custom styling based on node properties
        style: {
          background: node.type === 'dependency' ? '#e1f5fe' : '#f3e5f5',
          border: '1px solid #999',
          borderRadius: '8px',
          padding: '10px',
          fontSize: '12px',
        },
      };
    });

    // Transform edges
    const transformedEdges = data.graph.edges.map((edge, index) => ({
      id: edge.id || `edge-${index}`,
      source: edge.source || edge.from,
      target: edge.target || edge.to,
      type: 'default',
      animated: edge.animated || false,
      style: {
        stroke: edge.color || '#999',
        strokeWidth: edge.weight || 1,
      },
      label: edge.label || '',
    }));

    return {
      nodes: transformedNodes,
      edges: transformedEdges,
    };
  }, [data]);

  return (
    <div style={{ width: '100%', height: '600px' }}>
      <ReactFlow
        nodes={nodes}
        edges={edges}
        nodesDraggable={true}
        nodesConnectable={false}
        elementsSelectable={true}
        fitView={true}
        fitViewOptions={{
          padding: 0.2,
        }}
      >
        <Background
          variant="dots"
          gap={20}
          size={1}
          color="#ccc"
        />
        <Controls
          showZoom={true}
          showFitView={true}
          showInteractive={true}
        />
      </ReactFlow>
    </div>
  );
};

export default DependencyGraph;