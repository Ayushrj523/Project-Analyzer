#!/usr/bin/env python3
"""
Flask Project Analyzer Server

A Flask server that accepts zip files containing Python projects
and analyzes them for complexity metrics and dependencies.
"""

import os
import json
import zipfile
import tempfile
import sys
from typing import Dict, List, Any
import re

try:
    from flask import Flask, jsonify, request
    from flask_cors import CORS
    from dotenv import load_dotenv
    from radon.visitors import ComplexityVisitor
    from radon.raw import analyze
except ImportError as e:
    print(f"Error: Required libraries are missing. Install them with:")
    print("pip install flask flask-cors python-dotenv radon")
    print(f"Missing: {e}")
    sys.exit(1)

# Load environment variables
load_dotenv()

# Initialize Flask app
app = Flask(__name__)

# Set up CORS for React frontend
CORS(app, origins=['http://localhost:3000'])


def parse_dependencies(directory_path: str) -> List[str]:
    """
    Parse dependencies from requirements.txt file in the provided directory.
    
    Args:
        directory_path: Path to the directory to search for requirements.txt
        
    Returns:
        List of dependency package names (without version specifications)
    """
    requirements_path = os.path.join(directory_path, 'requirements.txt')
    dependencies = []
    
    # Check if requirements.txt exists
    if not os.path.exists(requirements_path):
        return dependencies
    
    try:
        with open(requirements_path, 'r', encoding='utf-8') as f:
            for line in f:
                # Strip whitespace
                line = line.strip()
                
                # Skip empty lines and comments
                if not line or line.startswith('#'):
                    continue
                
                # Parse package name (everything before version specifiers)
                # Handle various version specifiers: ==, >=, <=, >, <, !=, ~=
                # Also handle git+, -e, and other special cases
                if line.startswith('-e ') or line.startswith('--editable '):
                    # Skip editable installs for now
                    continue
                
                if line.startswith('git+') or line.startswith('http'):
                    # For git/http URLs, try to extract package name from URL
                    # This is a basic implementation - could be enhanced
                    if '#egg=' in line:
                        egg_part = line.split('#egg=')[1]
                        package_name = egg_part.split('&')[0].split('[')[0]
                        if package_name:
                            dependencies.append(package_name)
                    continue
                
                # Regular package with version specifiers
                # Remove everything after version specifiers
                package_match = re.match(r'^([a-zA-Z0-9_.-]+)', line)
                if package_match:
                    package_name = package_match.group(1)
                    dependencies.append(package_name)
    
    except (UnicodeDecodeError, IOError) as e:
        print(f"DEBUG: Failed to read requirements.txt: {str(e)}", file=sys.stderr)
    
    return dependencies


def analyze_python_file(file_path: str) -> Dict[str, Any]:
    """
    Analyze a single Python file for complexity metrics.
    
    Args:
        file_path: Path to the Python file to analyze
        
    Returns:
        Dictionary containing file analysis results
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            source_code = f.read()
    except (UnicodeDecodeError, IOError) as e:
        return {
            'file_path': file_path,
            'lines_of_code': 0,
            'functions': [],
            'error': f"Failed to read file: {str(e)}"
        }
    
    # Analyze raw metrics (lines of code)
    try:
        raw_analysis = analyze(source_code)
        lines_of_code = raw_analysis.loc  # Lines of code (excluding comments and blank lines)
    except Exception as e:
        lines_of_code = 0
    
    # Analyze complexity
    functions = []
    try:
        complexity_visitor = ComplexityVisitor.from_code(source_code)
        
        for item in complexity_visitor.blocks:
            # Check if the item has the required attributes for a function/method
            if hasattr(item, 'name') and hasattr(item, 'complexity') and hasattr(item, 'lineno'):
                functions.append({
                    'name': item.name,
                    'complexity': item.complexity,
                    'line_number': item.lineno
                })
    except Exception as e:
        print(f"DEBUG: A complexity analysis error occurred for {file_path}. Error: {e}", file=sys.stderr)
    
    return {
        'file_path': file_path,
        'lines_of_code': lines_of_code,
        'functions': functions
    }


def analyze_project(project_path: str) -> Dict[str, Any]:
    """
    Analyze all Python files in a project directory and parse dependencies.
    
    Args:
        project_path: Path to the project directory
        
    Returns:
        Dictionary containing analysis results for all Python files and dependencies
    """
    if not os.path.exists(project_path):
        raise FileNotFoundError(f"Project path does not exist: {project_path}")
    
    if not os.path.isdir(project_path):
        raise NotADirectoryError(f"Project path is not a directory: {project_path}")
    
    # Parse dependencies from requirements.txt
    dependencies = parse_dependencies(project_path)
    
    analysis_results = {
        'project_path': os.path.abspath(project_path),
        'files_analyzed': 0,
        'total_lines_of_code': 0,
        'total_functions': 0,
        'dependencies': dependencies,
        'files': []
    }
    
    # Walk through all files in the project directory
    for root, dirs, files in os.walk(project_path):
        # Skip common non-source directories
        dirs[:] = [d for d in dirs if not d.startswith('.') and d not in ['__pycache__', 'node_modules', 'venv', 'env']]
        
        for file in files:
            if file.endswith('.py'):
                file_path = os.path.join(root, file)
                relative_path = os.path.relpath(file_path, project_path)
                
                file_analysis = analyze_python_file(file_path)
                file_analysis['relative_path'] = relative_path
                
                analysis_results['files'].append(file_analysis)
                analysis_results['files_analyzed'] += 1
                
                if 'error' not in file_analysis:
                    analysis_results['total_lines_of_code'] += file_analysis['lines_of_code']
                    analysis_results['total_functions'] += len(file_analysis['functions'])
    
    return analysis_results


@app.route('/api/analyze', methods=['POST'])
def analyze_project_endpoint():
    """
    Endpoint to analyze a Python project from an uploaded zip file.
    
    Returns:
        JSON response with analysis results
    """
    try:
        print(f"DEBUG: Received request with files: {list(request.files.keys())}", file=sys.stderr)
        print(f"DEBUG: Content-Type: {request.content_type}", file=sys.stderr)
        
        # Check if file was uploaded
        if 'project_zip' not in request.files:
            return jsonify({
                'error': 'No project_zip file found in request'
            }), 400
        
        uploaded_file = request.files['project_zip']
        print(f"DEBUG: Uploaded filename: {uploaded_file.filename}", file=sys.stderr)
        print(f"DEBUG: Uploaded file mimetype: {uploaded_file.mimetype}", file=sys.stderr)
        
        # Check if file was actually selected
        if uploaded_file.filename == '':
            return jsonify({
                'error': 'No file selected'
            }), 400
        
        # Check if file is a zip file (be more lenient with file extensions)
        if not (uploaded_file.filename.lower().endswith('.zip') or 
                uploaded_file.mimetype in ['application/zip', 'application/x-zip-compressed']):
            return jsonify({
                'error': f'File must be a ZIP archive. Received: {uploaded_file.filename} (mimetype: {uploaded_file.mimetype})'
            }), 400
        
        # Use temporary directory for secure file handling
        with tempfile.TemporaryDirectory() as temp_dir:
            # Save uploaded file to temporary location
            temp_zip_path = os.path.join(temp_dir, 'project.zip')
            uploaded_file.save(temp_zip_path)
            
            # Debug: Check file size and existence
            file_size = os.path.getsize(temp_zip_path) if os.path.exists(temp_zip_path) else 0
            print(f"DEBUG: Saved file size: {file_size} bytes", file=sys.stderr)
            
            # Check if file is actually a ZIP file by reading the first few bytes
            try:
                with open(temp_zip_path, 'rb') as f:
                    file_header = f.read(min(100, file_size))  # Read more bytes for debugging
                    print(f"DEBUG: File header (first 100 bytes): {file_header}", file=sys.stderr)
                    print(f"DEBUG: File header hex: {file_header.hex()}", file=sys.stderr)
                    
                    # Check if this looks like a file path reference instead of actual file content
                    if file_header.startswith(b'<@'):
                        return jsonify({
                            'error': 'Received file path reference instead of file content. Please ensure your client is sending the actual file data, not a file path.'
                        }), 400
                    
                    # ZIP files start with PK (0x504B)
                    if not file_header.startswith(b'PK'):
                        return jsonify({
                            'error': f'File is not a valid ZIP archive (invalid file signature). Expected PK header, got: {file_header[:10].hex()}'
                        }), 400
                    
                    print("DEBUG: ZIP file signature validated successfully", file=sys.stderr)
                        
            except Exception as e:
                return jsonify({
                    'error': f'Failed to read uploaded file: {str(e)}'
                }), 500
            
            # Extract zip file
            try:
                # Test if ZIP file is readable first
                with zipfile.ZipFile(temp_zip_path, 'r') as zip_test:
                    zip_info = zip_test.infolist()
                    print(f"DEBUG: ZIP contains {len(zip_info)} files", file=sys.stderr)
                    
                    # Check if ZIP has any content
                    if len(zip_info) == 0:
                        return jsonify({
                            'error': 'ZIP file is empty'
                        }), 400
                
                # Now extract the ZIP file
                with zipfile.ZipFile(temp_zip_path, 'r') as zip_ref:
                    # Create extraction directory
                    extract_dir = os.path.join(temp_dir, 'extracted_project')
                    
                    # Extract all files
                    zip_ref.extractall(extract_dir)
                    print(f"DEBUG: Extracted to: {extract_dir}", file=sys.stderr)
                    
                    # Check if extraction was successful
                    if not os.path.exists(extract_dir):
                        return jsonify({
                            'error': 'Failed to create extraction directory'
                        }), 500
                        
                    extracted_items = os.listdir(extract_dir)
                    print(f"DEBUG: Extracted items: {extracted_items}", file=sys.stderr)
                    
                    if not extracted_items:
                        return jsonify({
                            'error': 'ZIP file appears to be empty after extraction'
                        }), 400
                    
            except zipfile.BadZipFile as e:
                print(f"DEBUG: BadZipFile error: {str(e)}", file=sys.stderr)
                return jsonify({
                    'error': f'Invalid ZIP file format: {str(e)}'
                }), 400
            except zipfile.LargeZipFile:
                return jsonify({
                    'error': 'ZIP file is too large (requires ZIP64 support)'
                }), 400
            except Exception as e:
                print(f"DEBUG: Unexpected ZIP error: {str(e)}", file=sys.stderr)
                return jsonify({
                    'error': f'Failed to extract ZIP file: {str(e)}'
                }), 500
            
            # Analyze the extracted project
            try:
                extracted_items = os.listdir(extract_dir)
                analysis_path = extract_dir
                if len(extracted_items) == 1 and os.path.isdir(os.path.join(extract_dir, extracted_items[0])):
                    # If there's only one item and it's a directory, assume it's the project root
                    analysis_path = os.path.join(extract_dir, extracted_items[0])
                    print(f"DEBUG: Single root directory detected. Analyzing inside: {analysis_path}", file=sys.stderr)
                    
                analysis_results = analyze_project(analysis_path)
                
                # Check if any Python files were found
                if analysis_results['files_analyzed'] == 0:
                    return jsonify({
                        'error': 'No Python files found in the uploaded project'
                    }), 400
                
                # Clean up the project_path in results to not expose server paths
                analysis_results['project_path'] = 'uploaded_project'
                
                return jsonify(analysis_results), 200
                
            except (FileNotFoundError, NotADirectoryError) as e:
                return jsonify({
                    'error': f'Project analysis failed: {str(e)}'
                }), 400
            except Exception as e:
                return jsonify({
                    'error': f'Unexpected error during analysis: {str(e)}'
                }), 500
        
        # Temporary directory is automatically cleaned up here
        
    except Exception as e:
        return jsonify({
            'error': f'Server error: {str(e)}'
        }), 500


@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint."""
    return jsonify({'status': 'healthy', 'message': 'Flask Project Analyzer is running'}), 200


if __name__ == '__main__':
    # Run the Flask development server
    app.run(
        host='0.0.0.0',
        port=5001,
        debug=True
    )