import React, { useState } from 'react';
import AnalysisReport from './AnalysisReport'; // Import your table component

function App() {
  const [file, setFile] = useState(null);
  const [analysisResult, setAnalysisResult] = useState(null);
  const [error, setError] = useState('');

  const handleFileChange = (e) => {
    const selectedFile = e.target.files[0];
    if (selectedFile) {
      // Check file extension instead of relying solely on MIME type
      const fileName = selectedFile.name.toLowerCase();
      const validTypes = [
        'application/zip',
        'application/x-zip-compressed',
        'application/octet-stream',
        '' // Sometimes ZIP files have empty MIME type
      ];
      
      if (fileName.endsWith('.zip') || validTypes.includes(selectedFile.type)) {
        setFile(selectedFile);
        setError('');
      } else {
        setError('Please select a valid .zip file');
        setFile(null);
      }
    }
  };

  const handleUpload = async () => {
    if (!file) {
      setError('Please select a .zip file first');
      return;
    }

    const formData = new FormData();
    formData.append('project_zip', file);

    try {
      setError('');
      setAnalysisResult(null);
      
      const response = await fetch('http://localhost:5001/api/analyze', {
        method: 'POST',
        body: formData,
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      setAnalysisResult(data);
    } catch (err) {
      const errorMessage = err.message || 'An error occurred during analysis';
      setError(errorMessage);
    }
  };

  return (
    <div className="min-h-screen bg-gray-50 py-8 px-4">
      <div className="max-w-2xl mx-auto">
        <div className="bg-white rounded-lg shadow-md p-8">
          <h1 className="text-2xl font-bold text-gray-800 mb-6 text-center">
            Zip File Analyzer
          </h1>
          
          <div className="space-y-6">
            {/* File Input Section */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Select ZIP File
              </label>
              <div className="relative">
                <input
                  type="file"
                  accept=".zip"
                  onChange={handleFileChange}
                  className="block w-full text-sm text-gray-500 file:mr-4 file:py-2 file:px-4 file:rounded-md file:border-0 file:text-sm file:font-semibold file:bg-blue-50 file:text-blue-700 hover:file:bg-blue-100 file:cursor-pointer cursor-pointer border border-gray-300 rounded-md p-2"
                />
              </div>
              {file && (
                <p className="mt-2 text-sm text-gray-600">
                  Selected: {file.name} ({(file.size / 1024 / 1024).toFixed(2)} MB)
                </p>
              )}
            </div>

            {/* Upload Button */}
            <button
              onClick={handleUpload}
              disabled={!file}
              className="w-full bg-blue-600 hover:bg-blue-700 disabled:bg-gray-400 disabled:cursor-not-allowed text-white font-semibold py-3 px-4 rounded-md transition duration-200"
            >
              {!file ? 'Select a file to upload' : 'Analyze ZIP File'}
            </button>

            {/* Error Display */}
            {error && (
              <div className="p-4 bg-red-50 border border-red-200 rounded-md">
                <div className="flex">
                  <div className="text-red-800">
                    <h3 className="text-sm font-medium">Error</h3>
                    <div className="mt-1 text-sm">{error}</div>
                  </div>
                </div>
              </div>
            )}
          </div>
        </div>

        {/* Analysis Report - Now uses your imported component */}
        {analysisResult && <AnalysisReport data={analysisResult} />}
      </div>
    </div>
  );
}

export default App;