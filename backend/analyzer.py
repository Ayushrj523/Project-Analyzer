#!/usr/bin/env python3
"""
Python Project Complexity Analyzer

This script analyzes Python files in a given project directory and reports:
- File paths
- Lines of code per file
- Cyclomatic complexity of functions

Usage:
    python analyzer.py <project_path>
"""

import argparse
import os
import json
import sys
from typing import Dict, List, Any

try:
    from radon.visitors import ComplexityVisitor
    from radon.raw import analyze
except ImportError:
    print("Error: radon library is required. Install it with: pip install radon")
    sys.exit(1)


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
    Analyze all Python files in a project directory.
    
    Args:
        project_path: Path to the project directory
        
    Returns:
        Dictionary containing analysis results for all Python files
    """
    if not os.path.exists(project_path):
        raise FileNotFoundError(f"Project path does not exist: {project_path}")
    
    if not os.path.isdir(project_path):
        raise NotADirectoryError(f"Project path is not a directory: {project_path}")
    
    analysis_results = {
        'project_path': os.path.abspath(project_path),
        'files_analyzed': 0,
        'total_lines_of_code': 0,
        'total_functions': 0,
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


def main():
    """Main function to handle command-line arguments and run the analysis."""
    parser = argparse.ArgumentParser(
        description='Analyze Python files in a project for complexity metrics',
        epilog='Example: python analyzer.py /path/to/my/project'
    )
    
    parser.add_argument(
        'project_path',
        help='Path to the project directory to analyze'
    )
    
    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Enable verbose output'
    )
    
    args = parser.parse_args()
    
    try:
        if args.verbose:
            print(f"Analyzing project: {args.project_path}", file=sys.stderr)
        
        results = analyze_project(args.project_path)
        
        if args.verbose:
            print(f"Analysis complete. Found {results['files_analyzed']} Python files.", file=sys.stderr)
        
        # Output the results as JSON with 2-space indentation
        print(json.dumps(results, indent=2))
        
    except (FileNotFoundError, NotADirectoryError) as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Unexpected error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()