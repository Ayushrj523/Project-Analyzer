import { ResponsiveContainer, ScatterChart, XAxis, YAxis, Tooltip, Scatter } from 'recharts';

const RiskMatrix = ({ data }) => {
  // Transform the files data for recharts
  const chartData = data.files.map(file => {
    // Calculate maximum cognitive complexity from functions array
    const maxComplexity = file.functions.length > 0 
      ? Math.max(...file.functions.map(func => func.cognitive_complexity))
      : 0;

    return {
      x: file.lines_of_code,
      y: maxComplexity,
      z: file.relative_path
    };
  });

  // Custom tooltip to show file details
  const CustomTooltip = ({ active, payload }) => {
    if (active && payload && payload.length) {
      const data = payload[0].payload;
      return (
        <div className="bg-white p-3 border border-gray-300 rounded shadow-lg">
          <p className="font-semibold text-sm mb-1">File: {data.z}</p>
          <p className="text-sm">Lines of Code: {data.x}</p>
          <p className="text-sm">Max Cognitive Complexity: {data.y}</p>
        </div>
      );
    }
    return null;
  };

  return (
    <ResponsiveContainer width="100%" height={400}>
      <ScatterChart margin={{ top: 20, right: 20, bottom: 20, left: 20 }}>
        <XAxis 
          type="number" 
          dataKey="x" 
          name="Lines of Code"
          label={{ value: 'Lines of Code', position: 'insideBottom', offset: -10 }}
        />
        <YAxis 
          type="number" 
          dataKey="y" 
          name="Cognitive Complexity"
          label={{ value: 'Cognitive Complexity', angle: -90, position: 'insideLeft' }}
        />
        <Tooltip content={<CustomTooltip />} />
        <Scatter 
          data={chartData} 
          fill="#ef4444"
        />
      </ScatterChart>
    </ResponsiveContainer>
  );
};

export default RiskMatrix;