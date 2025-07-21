// frontend/src/AnalysisReport.js - CORRECTED VERSION

import React from 'react';

const AnalysisReport = ({ data }) => {
  // Safety check for data and the files array
  const files = data?.files || [];

  return (
    <div className="mt-8">
      <h2 className="text-2xl font-semibold text-gray-700 mb-4">Code Analysis Report</h2>
      <div className="bg-white shadow-md rounded-lg overflow-hidden">
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  File Path
                </th>
                <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Lines of Code
                </th>
                <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Functions Found
                </th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {files.map((file, index) => (
                <tr key={index}>
                  {/* FIX #1: Use 'relative_path', not 'filePath' */}
                  <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                    {file.relative_path || 'N/A'}
                  </td>
                  
                  {/* FIX #2: Use 'lines_of_code', not 'linesOfCode' */}
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                    {file.lines_of_code || 0}
                  </td>
                  
                  {/* FIX #3: Use 'functions.length', not 'functionsAnalyzed' */}
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                    {file.functions?.length || 0}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        {files.length === 0 && (
          <p className="py-4 text-center text-gray-500">No Python files were found or analyzed in this project.</p>
        )}
      </div>
    </div>
  );
};

export default AnalysisReport;