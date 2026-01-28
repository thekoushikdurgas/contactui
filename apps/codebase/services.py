"""Codebase analysis service for scanning and analyzing codebases."""

import os
import ast
import logging
from typing import Dict, Any, List, Optional
from pathlib import Path

logger = logging.getLogger(__name__)


class CodebaseAnalysisService:
    """Service for analyzing codebases."""
    
    # Supported file extensions
    PYTHON_EXTENSIONS = {'.py'}
    JAVASCRIPT_EXTENSIONS = {'.js', '.jsx', '.ts', '.tsx'}
    SUPPORTED_EXTENSIONS = PYTHON_EXTENSIONS | JAVASCRIPT_EXTENSIONS
    
    def __init__(self):
        """Initialize codebase analysis service."""
        pass
    
    def scan_directory(self, target_path: str, analysis_type: str = 'full_scan') -> Dict[str, Any]:
        """
        Scan a directory and analyze the codebase.
        
        Args:
            target_path: Path to the directory to scan
            analysis_type: Type of analysis to perform
            
        Returns:
            Analysis results dictionary
        """
        results = {
            'files': [],
            'languages': {},
            'total_files': 0,
            'total_lines': 0,
            'dependencies': [],
            'patterns': []
        }
        
        if not os.path.exists(target_path):
            logger.error(f"Target path does not exist: {target_path}")
            return results
        
        # Scan files
        for root, dirs, files in os.walk(target_path):
            # Skip common directories
            dirs[:] = [d for d in dirs if d not in {'.git', '__pycache__', 'node_modules', '.venv', 'venv', '.cursor'}]
            
            for file in files:
                file_path = os.path.join(root, file)
                file_ext = os.path.splitext(file)[1]
                
                if file_ext in self.SUPPORTED_EXTENSIONS:
                    file_info = self._analyze_file(file_path, file_ext)
                    if file_info:
                        results['files'].append(file_info)
                        results['total_files'] += 1
                        results['total_lines'] += file_info.get('lines', 0)
                        
                        # Track languages
                        lang = self._get_language(file_ext)
                        results['languages'][lang] = results['languages'].get(lang, 0) + 1
        
        # Detect dependencies
        results['dependencies'] = self._detect_dependencies(target_path)
        
        # Detect patterns
        results['patterns'] = self._detect_patterns(results['files'])
        
        return results
    
    def _analyze_file(self, file_path: str, file_ext: str) -> Optional[Dict[str, Any]]:
        """
        Analyze a single file.
        
        Args:
            file_path: Path to the file
            file_ext: File extension
            
        Returns:
            File analysis dictionary, or None if error
        """
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
                lines = content.split('\n')
            
            file_info = {
                'path': file_path,
                'name': os.path.basename(file_path),
                'extension': file_ext,
                'language': self._get_language(file_ext),
                'lines': len(lines),
                'size': os.path.getsize(file_path)
            }
            
            # Parse code if Python
            if file_ext == '.py':
                try:
                    tree = ast.parse(content)
                    file_info['classes'] = len([node for node in ast.walk(tree) if isinstance(node, ast.ClassDef)])
                    file_info['functions'] = len([node for node in ast.walk(tree) if isinstance(node, ast.FunctionDef)])
                    file_info['imports'] = self._extract_imports(tree)
                except SyntaxError:
                    file_info['parse_error'] = True
            
            return file_info
        except Exception as e:
            logger.error(f"Error analyzing file {file_path}: {str(e)}")
            return None
    
    def _get_language(self, file_ext: str) -> str:
        """Get language name from file extension."""
        if file_ext in self.PYTHON_EXTENSIONS:
            return 'Python'
        elif file_ext in self.JAVASCRIPT_EXTENSIONS:
            return 'JavaScript'
        return 'Unknown'
    
    def _extract_imports(self, tree: ast.AST) -> List[str]:
        """Extract import statements from AST."""
        imports = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imports.append(alias.name)
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    imports.append(node.module)
        return imports
    
    def _detect_dependencies(self, target_path: str) -> List[str]:
        """
        Detect dependencies from requirements.txt, package.json, etc.
        
        Args:
            target_path: Path to scan for dependency files
            
        Returns:
            List of dependency names
        """
        dependencies = []
        
        # Check for requirements.txt
        requirements_path = os.path.join(target_path, 'requirements.txt')
        if os.path.exists(requirements_path):
            try:
                with open(requirements_path, 'r', encoding='utf-8') as f:
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith('#'):
                            # Extract package name (before ==, >=, etc.)
                            pkg_name = line.split('==')[0].split('>=')[0].split('<=')[0].split('>')[0].split('<')[0].strip()
                            if pkg_name:
                                dependencies.append(pkg_name)
            except Exception as e:
                logger.error(f"Error reading requirements.txt: {e}")
        
        # Check for package.json
        package_json_path = os.path.join(target_path, 'package.json')
        if os.path.exists(package_json_path):
            try:
                import json
                with open(package_json_path, 'r', encoding='utf-8') as f:
                    package_data = json.load(f)
                    deps = package_data.get('dependencies', {})
                    dev_deps = package_data.get('devDependencies', {})
                    all_deps = {**deps, **dev_deps}
                    dependencies.extend(list(all_deps.keys()))
            except Exception as e:
                logger.error(f"Error reading package.json: {e}")
        
        return dependencies
    
    def _detect_patterns(self, files: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Detect code patterns.
        
        Args:
            files: List of file analysis dictionaries
            
        Returns:
            List of detected patterns
        """
        patterns = []
        
        # Detect Django patterns
        django_files = [f for f in files if 'django' in f.get('imports', [])]
        if django_files:
            patterns.append({
                'type': 'framework',
                'name': 'Django',
                'count': len(django_files),
                'description': 'Django web framework detected'
            })
        
        # Detect React patterns
        react_files = [f for f in files if f.get('extension') in {'.jsx', '.tsx'}]
        if react_files:
            patterns.append({
                'type': 'framework',
                'name': 'React',
                'count': len(react_files),
                'description': 'React components detected'
            })
        
        # Detect service patterns
        service_files = [f for f in files if 'service' in f.get('name', '').lower()]
        if service_files:
            patterns.append({
                'type': 'architecture',
                'name': 'Service Layer',
                'count': len(service_files),
                'description': 'Service pattern detected'
            })
        
        return patterns
    
    def create_analysis(self, target_path: str, name: str = None) -> Dict[str, Any]:
        """
        Create a new codebase analysis.
        
        Args:
            target_path: Path to analyze
            name: Optional analysis name
            
        Returns:
            Analysis data dictionary
        """
        scan_results = self.scan_directory(target_path)
        
        analysis_data = {
            'name': name or os.path.basename(target_path),
            'target_path': target_path,
            'scan_results': scan_results,
            'created_at': None  # Would be set by model
        }
        
        return analysis_data
    
    def run_analysis(self, target_path: str) -> Dict[str, Any]:
        """
        Run codebase analysis.
        
        Args:
            target_path: Path to analyze
            
        Returns:
            Analysis results
        """
        return self.scan_directory(target_path)
