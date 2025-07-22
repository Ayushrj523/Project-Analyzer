import React, { useState } from 'react';
import { Sparkles, Upload, Loader2 } from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from './components/ui/card';
import { Button } from './components/ui/button';
import { Input } from './components/ui/input';
import { Label } from './components/ui/label';
import { Alert, AlertDescription } from './components/ui/alert';
import AnalysisReport from './AnalysisReport';
import CodeCity from './CodeCity';

function App() {
  const [file, setFile] = useState(null);
  const [analysisResult, setAnalysisResult] = useState(null);
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

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
      setLoading(true);
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
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-background flex">
      {/* Left Sidebar */}
      <div className="w-80 border-r bg-card p-6 flex flex-col">
        <div className="flex items-center gap-2 mb-8">
          <Sparkles className="h-6 w-6 text-primary" />
          <h1 className="text-xl font-bold text-foreground">Project Analyzer</h1>
        </div>

        <Card className="flex-1">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Upload className="h-5 w-5" />
              Upload Project
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="zip-upload">Select ZIP File</Label>
              <Input
                id="zip-upload"
                type="file"
                accept=".zip"
                onChange={handleFileChange}
                className="cursor-pointer"
              />
              {file && (
                <p className="text-sm text-muted-foreground">
                  Selected: {file.name} ({(file.size / 1024 / 1024).toFixed(2)} MB)
                </p>
              )}
            </div>

            <Button
              onClick={handleUpload}
              disabled={!file || loading}
              className="w-full"
            >
              {loading ? (
                <>
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  Analyzing...
                </>
              ) : (
                'Analyze Project'
              )}
            </Button>
          </CardContent>
        </Card>
      </div>

      {/* Right Main Content Area */}
      <div className="flex-1 p-6 overflow-auto">
        {loading && (
          <div className="flex flex-col items-center justify-center h-64 space-y-4">
            <Loader2 className="h-8 w-8 animate-spin text-primary" />
            <p className="text-lg text-muted-foreground">Analyzing your project...</p>
          </div>
        )}

        {error && (
          <Alert variant="destructive" className="mb-6">
            <AlertDescription>{error}</AlertDescription>
          </Alert>
        )}

        {analysisResult && (
          <div className="space-y-6">
            <AnalysisReport data={analysisResult} />
            <CodeCity data={analysisResult} />
          </div>
        )}

        {!loading && !error && !analysisResult && (
          <div className="flex flex-col items-center justify-center h-64 space-y-4">
            <div className="text-center space-y-2">
              <h2 className="text-2xl font-semibold text-foreground">Welcome to Project Analyzer</h2>
              <p className="text-muted-foreground">
                Upload a ZIP file containing your project to get started with the analysis.
              </p>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

export default App;