#!/usr/bin/env python3
"""
Flask Project Analyzer Server

A Flask server that accepts zip files containing Python projects
and analyzes them for complexity metrics, dependencies, and code smells.
Enhanced with Halstead and Cognitive complexity metrics.
"""

import os
import json
import zipfile
import tempfile
import sys
import ast
from typing import Dict, List, Any
import re

try:
    from flask import Flask, jsonify, request
    from flask_cors import CORS
    from dotenv import load_dotenv
    from radon.visitors import ComplexityVisitor
    from radon.raw import analyze
    from cognitive_complexity.api import get_cognitive_complexity
except ImportError as e:
    print(f"Error: Required libraries are missing. Install them with:")
    print("pip install flask flask-cors python-dotenv radon cognitive_complexity")
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


def calculate_cognitive_complexity_from_ast(node) -> int:
    """
    Calculate cognitive complexity directly from AST node.
    This is a robust implementation that doesn't rely on radon compatibility.
    """
    complexity = 0
    nesting_level = 0
    
    def visit_node(node, nesting=0):
        nonlocal complexity
        
        # Base complexity increment for control structures
        if isinstance(node, (ast.If, ast.While, ast.For, ast.AsyncFor)):
            complexity += 1 + nesting
        elif isinstance(node, (ast.Try, ast.ExceptHandler)):
            complexity += 1 + nesting
        elif isinstance(node, ast.With):
            complexity += 1 + nesting
        elif isinstance(node, ast.BoolOp):
            # Each additional boolean operator adds complexity
            complexity += len(node.values) - 1
        elif isinstance(node, ast.comprehension):
            # List/dict/set comprehensions add complexity
            complexity += 1 + nesting
        
        # Recursively visit child nodes with increased nesting for certain structures
        for child in ast.iter_child_nodes(node):
            new_nesting = nesting
            if isinstance(node, (ast.If, ast.While, ast.For, ast.AsyncFor, ast.Try, ast.With)):
                new_nesting = nesting + 1
            visit_node(child, new_nesting)
    
    visit_node(node)
    return complexity


def calculate_halstead_from_ast(source_code: str) -> Dict[str, Any]:
    """
    Calculate Halstead metrics directly from AST.
    More robust than relying on radon's implementation.
    """
    try:
        tree = ast.parse(source_code)
    except SyntaxError:
        return {}
    
    operators = set()
    operands = set()
    operator_count = 0
    operand_count = 0
    
    # Define Python operators
    operator_nodes = (
        ast.Add, ast.Sub, ast.Mult, ast.Div, ast.Mod, ast.Pow, ast.LShift, ast.RShift,
        ast.BitOr, ast.BitXor, ast.BitAnd, ast.FloorDiv, ast.And, ast.Or, ast.Not,
        ast.Eq, ast.NotEq, ast.Lt, ast.LtE, ast.Gt, ast.GtE, ast.Is, ast.IsNot,
        ast.In, ast.NotIn, ast.UAdd, ast.USub, ast.Invert
    )
    
    for node in ast.walk(tree):
        # Count operators
        if isinstance(node, operator_nodes):
            op_name = type(node).__name__
            operators.add(op_name)
            operator_count += 1
        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            operators.add(type(node).__name__)
            operator_count += 1
        elif isinstance(node, (ast.If, ast.While, ast.For, ast.AsyncFor)):
            operators.add(type(node).__name__)
            operator_count += 1
        elif isinstance(node, (ast.Return, ast.Yield, ast.YieldFrom)):
            operators.add(type(node).__name__)
            operator_count += 1
        
        # Count operands (variables, constants, function names)
        elif isinstance(node, ast.Name):
            operands.add(node.id)
            operand_count += 1
        elif isinstance(node, ast.Constant):
            operands.add(str(node.value))
            operand_count += 1
        elif isinstance(node, ast.Attribute):
            operands.add(node.attr)
            operand_count += 1
    
    h1 = len(operators)  # Distinct operators
    h2 = len(operands)   # Distinct operands
    N1 = operator_count  # Total operators
    N2 = operand_count   # Total operands
    
    # Calculate derived metrics
    vocabulary = h1 + h2
    length = N1 + N2
    
    if vocabulary > 0 and length > 0:
        import math
        volume = length * math.log2(vocabulary)
        difficulty = (h1 / 2) * (N2 / h2) if h2 > 0 else 0
        effort = difficulty * volume
        time_required = effort / 18  # Halstead's constant
        bugs = volume / 3000  # Halstead's constant
    else:
        volume = difficulty = effort = time_required = bugs = 0
    
    return {
        'h1': h1,
        'h2': h2,
        'N1': N1,
        'N2': N2,
        'vocabulary': vocabulary,
        'length': length,
        'volume': round(volume, 2),
        'difficulty': round(difficulty, 2),
        'effort': round(effort, 2),
        'time': round(time_required, 2),
        'bugs': round(bugs, 4)
    }


def analyze_python_file(file_path: str) -> Dict[str, Any]:
    """
    Analyze a single Python file for complexity metrics and code smells.
    Now includes robust Halstead and Cognitive complexity metrics calculated directly from AST.
    
    Args:
        file_path: Path to the Python file to analyze
        
    Returns:
        Dictionary containing file analysis results with enhanced metrics
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            source_code = f.read()
    except (UnicodeDecodeError, IOError) as e:
        return {
            'file_path': file_path,
            'lines_of_code': 0,
            'functions': [],
            'code_smells': [],
            'halstead': {},
            'error': f"Failed to read file: {str(e)}"
        }
    
    # Analyze raw metrics (lines of code) using radon
    lines_of_code = 0
    try:
        raw_analysis = analyze(source_code)
        lines_of_code = raw_analysis.loc  # Lines of code (excluding comments and blank lines)
        print(f"DEBUG: Lines of code for {file_path}: {lines_of_code}", file=sys.stderr)
    except Exception as e:
        print(f"DEBUG: Raw analysis error for {file_path}: {e}", file=sys.stderr)
        # Fallback: count non-empty, non-comment lines
        lines_of_code = len([line for line in source_code.split('\n') 
                            if line.strip() and not line.strip().startswith('#')])
    
    # Calculate Halstead metrics using our robust AST-based implementation
    halstead_metrics = calculate_halstead_from_ast(source_code)
    print(f"DEBUG: Halstead metrics for {file_path}: {halstead_metrics}", file=sys.stderr)
    
    # Analyze complexity (both Cyclomatic and Cognitive)
    functions = []
    try:
        # Parse AST for cognitive complexity calculation
        tree = ast.parse(source_code)
        
        # Use radon for cyclomatic complexity
        complexity_visitor = ComplexityVisitor.from_code(source_code)
        
        # Create a mapping of function names to AST nodes for cognitive complexity
        function_nodes = {}
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                function_nodes[node.name] = node
        
        for item in complexity_visitor.blocks:
            # Check if the item has the required attributes for a function/method
            if hasattr(item, 'name') and hasattr(item, 'complexity') and hasattr(item, 'lineno'):
                # Calculate cognitive complexity using our AST-based method
                cognitive_comp = 0
                if item.name in function_nodes:
                    cognitive_comp = calculate_cognitive_complexity_from_ast(function_nodes[item.name])
                    print(f"DEBUG: Cognitive complexity for {item.name}: {cognitive_comp}", file=sys.stderr)
                
                functions.append({
                    'name': item.name,
                    'cyclomatic_complexity': item.complexity,  # From radon
                    'cognitive_complexity': cognitive_comp,    # From our AST implementation
                    'line_number': item.lineno,
                    'halstead': None  # Individual function Halstead metrics not calculated for now
                })
                
                print(f"DEBUG: Function {item.name} - Cyclomatic: {item.complexity}, Cognitive: {cognitive_comp}", file=sys.stderr)
        
    except Exception as e:
        print(f"DEBUG: A complexity analysis error occurred for {file_path}. Error: {e}", file=sys.stderr)
        import traceback
        print(f"DEBUG: Traceback: {traceback.format_exc()}", file=sys.stderr)
    
    # Parse AST and detect code smells
    code_smells = []
    try:
        tree = ast.parse(source_code)
        
        # Traverse the AST to detect code smells
        for node in ast.walk(tree):
            # Long Parameter List detection
            if isinstance(node, ast.FunctionDef):
                param_count = len(node.args.args)
                if param_count > 5:
                    code_smells.append({
                        'type': 'Long Parameter List',
                        'message': f'Function "{node.name}" has {param_count} parameters (more than 5)',
                        'line_number': node.lineno
                    })
            
            # Magic Numbers detection
            elif isinstance(node, ast.Compare):
                for comparator in node.comparators:
                    if isinstance(comparator, ast.Constant) and isinstance(comparator.value, int):
                        code_smells.append({
                            'type': 'Magic Number',
                            'message': f'Magic number {comparator.value} found in comparison',
                            'line_number': comparator.lineno
                        })
    
    except SyntaxError as e:
        print(f"DEBUG: Syntax error in {file_path}: {str(e)}", file=sys.stderr)
        code_smells.append({
            'type': 'Syntax Error',
            'message': f'Invalid Python syntax: {str(e)}',
            'line_number': getattr(e, 'lineno', 0)
        })
    except Exception as e:
        print(f"DEBUG: AST parsing error for {file_path}: {str(e)}", file=sys.stderr)
    
    return {
        'file_path': file_path,
        'lines_of_code': lines_of_code,
        'functions': functions,
        'code_smells': code_smells,
        'halstead': halstead_metrics
    }


def analyze_project(project_path: str) -> Dict[str, Any]:
    """
    Analyze all Python files in a project directory and parse dependencies.
    Now aggregates Halstead and Cognitive complexity metrics.
    
    Args:
        project_path: Path to the project directory
        
    Returns:
        Dictionary containing analysis results for all Python files, dependencies, and code smells
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
        'total_code_smells': 0,
        'total_cyclomatic_complexity': 0,
        'total_cognitive_complexity': 0,
        'average_cyclomatic_complexity': 0,
        'average_cognitive_complexity': 0,
        'total_halstead_volume': 0,
        'total_halstead_difficulty': 0,
        'total_halstead_effort': 0,
        'average_halstead_volume': 0,
        'average_halstead_difficulty': 0,
        'average_halstead_effort': 0,
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
                    analysis_results['total_code_smells'] += len(file_analysis['code_smells'])
                    
                    # Aggregate complexity metrics
                    for func in file_analysis['functions']:
                        analysis_results['total_cyclomatic_complexity'] += func.get('cyclomatic_complexity', 0)
                        analysis_results['total_cognitive_complexity'] += func.get('cognitive_complexity', 0)
                    
                    # Aggregate Halstead metrics
                    halstead = file_analysis.get('halstead', {})
                    if halstead:
                        analysis_results['total_halstead_volume'] += halstead.get('volume', 0)
                        analysis_results['total_halstead_difficulty'] += halstead.get('difficulty', 0)
                        analysis_results['total_halstead_effort'] += halstead.get('effort', 0)
    
    # Calculate averages
    if analysis_results['total_functions'] > 0:
        analysis_results['average_cyclomatic_complexity'] = round(
            analysis_results['total_cyclomatic_complexity'] / analysis_results['total_functions'], 2
        )
        analysis_results['average_cognitive_complexity'] = round(
            analysis_results['total_cognitive_complexity'] / analysis_results['total_functions'], 2
        )
    
    if analysis_results['files_analyzed'] > 0:
        analysis_results['average_halstead_volume'] = round(
            analysis_results['total_halstead_volume'] / analysis_results['files_analyzed'], 2
        )
        analysis_results['average_halstead_difficulty'] = round(
            analysis_results['total_halstead_difficulty'] / analysis_results['files_analyzed'], 2
        )
        analysis_results['average_halstead_effort'] = round(
            analysis_results['total_halstead_effort'] / analysis_results['files_analyzed'], 2
        )
    
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