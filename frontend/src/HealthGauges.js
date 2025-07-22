import React from 'react';
import { RadialBarChart, RadialBar, ResponsiveContainer } from 'recharts';
import { Card } from '@/components/ui/card';

const HealthGauges = ({ data }) => {
  // Calculate scores from the raw data
    // frontend/src/HealthGauges.js - CORRECTED LOGIC

  const calculateScores = () => {
    // This initial defensive check is excellent and should be kept.
    if (!data || !data.files || data.files.length === 0) {
      return {
        maintainabilityScore: 0,
        testabilityScore: 0,
        effortScore: 0
      };
    }

    // --- THE FIX IS HERE ---
    // Use flatMap to create a single array of ALL functions from ALL files
    const allFunctions = data.files.flatMap(file => file.functions || []);

    // Calculate total complexities from the correct 'allFunctions' array
    const totalCognitiveComplexity = allFunctions.reduce((sum, func) => sum + (func.cognitive_complexity || 0), 0);
    const totalCyclomaticComplexity = allFunctions.reduce((sum, func) => sum + (func.cyclomatic_complexity || 0), 0);
    
    // Calculate total Halstead effort by correctly accessing the nested object
    const totalEffort = data.files.reduce((sum, file) => sum + (file.halstead?.effort || 0), 0);

    const functionCount = allFunctions.length > 0 ? allFunctions.length : 1;
    const avgCognitiveComplexity = totalCognitiveComplexity / functionCount;
    const avgCyclomaticComplexity = totalCyclomaticComplexity / functionCount;
    
    // These scoring formulas are fine, we just needed the correct data for them.
    const SCORING_CAP = 500000; // Define as a constant for clarity
    const maintainabilityScore = Math.max(0, 100 - (avgCognitiveComplexity * 5));
    const testabilityScore = Math.max(0, 100 - (avgCyclomaticComplexity * 5));
    const effortScore = Math.max(0, (1 - (totalEffort / SCORING_CAP)) * 100);

    return {
      maintainabilityScore: Math.round(maintainabilityScore),
      testabilityScore: Math.round(testabilityScore),
      effortScore: Math.round(effortScore)
    };
  };

  const scores = calculateScores();

  // Create gauge data for each metric
  const createGaugeData = (score) => [
    {
      name: 'score',
      value: score,
      fill: score >= 80 ? '#22c55e' : score >= 60 ? '#f59e0b' : '#ef4444'
    }
  ];

  const GaugeChart = ({ score, title, color }) => (
    <div className="flex flex-col items-center">
      <div className="relative w-48 h-24">
        <ResponsiveContainer width="100%" height="100%">
          <RadialBarChart
            cx="50%"
            cy="100%"
            innerRadius="60%"
            outerRadius="90%"
            startAngle={180}
            endAngle={0}
            data={createGaugeData(score)}
          >
            <RadialBar
              dataKey="value"
              cornerRadius={10}
              fill={color}
              background={{ fill: '#e5e7eb' }}
            />
          </RadialBarChart>
        </ResponsiveContainer>
        <div className="absolute inset-0 flex items-end justify-center pb-2">
          <text className="text-2xl font-bold text-gray-800">
            {score}%
          </text>
        </div>
      </div>
      <h3 className="mt-4 text-lg font-semibold text-gray-700">{title}</h3>
    </div>
  );

  return (
    <Card className="p-6">
      <div className="flex justify-around items-center space-x-8">
        <GaugeChart
          score={scores.maintainabilityScore}
          title="Maintainability"
          color={scores.maintainabilityScore >= 80 ? '#22c55e' : scores.maintainabilityScore >= 60 ? '#f59e0b' : '#ef4444'}
        />
        <GaugeChart
          score={scores.testabilityScore}
          title="Testability"
          color={scores.testabilityScore >= 80 ? '#22c55e' : scores.testabilityScore >= 60 ? '#f59e0b' : '#ef4444'}
        />
        <GaugeChart
          score={scores.effortScore}
          title="Effort"
          color={scores.effortScore >= 80 ? '#22c55e' : scores.effortScore >= 60 ? '#f59e0b' : '#ef4444'}
        />
      </div>
    </Card>
  );
};

export default HealthGauges;