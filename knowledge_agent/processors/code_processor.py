"""
Code file processor for analyzing source code files.
"""

import re
from pathlib import Path
from typing import Dict, Any, List, Optional

from .base_processor import BaseDataSourceProcessor
from ..models import DataSource, SourceType
from ..core.exceptions import ProcessingError


class CodeProcessor(BaseDataSourceProcessor):
    """
    Processor for code files.
    
    Supports:
    - Python (.py)
    - JavaScript (.js, .jsx, .ts, .tsx)
    - Java (.java)
    - C/C++ (.c, .cpp, .h, .hpp)
    - Go (.go)
    - Rust (.rs)
    - Ruby (.rb)
    - PHP (.php)
    - And more...
    
    Extracts:
    - Code structure (functions, classes, methods)
    - Comments and docstrings
    - Import/include statements
    """
    
    # Supported file extensions and their languages
    LANGUAGE_MAP = {
        '.py': 'python',
        '.js': 'javascript',
        '.jsx': 'javascript',
        '.ts': 'typescript',
        '.tsx': 'typescript',
        '.java': 'java',
        '.c': 'c',
        '.cpp': 'cpp',
        '.cc': 'cpp',
        '.cxx': 'cpp',
        '.h': 'c_header',
        '.hpp': 'cpp_header',
        '.go': 'go',
        '.rs': 'rust',
        '.rb': 'ruby',
        '.php': 'php',
        '.cs': 'csharp',
        '.swift': 'swift',
        '.kt': 'kotlin',
        '.scala': 'scala',
        '.r': 'r',
        '.m': 'objective_c',
        '.sh': 'shell',
        '.bash': 'shell',
        '.sql': 'sql',
        '.html': 'html',
        '.css': 'css',
        '.xml': 'xml',
        '.json': 'json',
        '.yaml': 'yaml',
        '.yml': 'yaml',
    }
    
    def __init__(self):
        """Initialize the code processor."""
        super().__init__()
    
    def get_supported_types(self) -> List[SourceType]:
        """Get the list of source types this processor supports."""
        return [SourceType.CODE]
    
    def validate(self, source: DataSource) -> bool:
        """
        Validate that a code source can be processed.
        
        Args:
            source: The data source to validate
            
        Returns:
            bool: True if the source can be processed, False otherwise
        """
        # Call parent validation
        if not super().validate(source):
            return False
        
        # Check file extension
        path = Path(source.path)
        ext = path.suffix.lower()
        
        if ext not in self.LANGUAGE_MAP:
            self.logger.warning(
                f"Unsupported code file extension: {ext}. "
                f"Supported: {list(self.LANGUAGE_MAP.keys())}"
            )
            return False
        
        return True
    
    def get_metadata(self, source: DataSource) -> Dict[str, Any]:
        """
        Extract metadata from a code source.
        
        Args:
            source: The data source to extract metadata from
            
        Returns:
            Dict[str, Any]: Metadata dictionary
        """
        metadata = super().get_metadata(source)
        
        # Add code-specific metadata
        path = Path(source.path)
        ext = path.suffix.lower()
        
        metadata['document_type'] = 'code'
        metadata['language'] = self.LANGUAGE_MAP.get(ext, 'unknown')
        
        # Try to extract additional code structure info
        try:
            content = self._read_file(source.path, source.encoding or 'utf-8')
            
            # Count lines
            lines = content.split('\n')
            metadata['line_count'] = len(lines)
            metadata['non_empty_lines'] = sum(1 for line in lines if line.strip())
            
            # Extract structure based on language
            language = metadata['language']
            structure = self._analyze_structure(content, language)
            metadata.update(structure)
            
        except Exception as e:
            self.logger.warning(
                f"Error extracting code metadata from {source.path}: {str(e)}"
            )
        
        return metadata
    
    def _extract_content(self, source: DataSource) -> str:
        """
        Extract content from the code file.
        
        Args:
            source: The data source to extract content from
            
        Returns:
            str: The extracted content with structure and comments
            
        Raises:
            ProcessingError: If content extraction fails
        """
        encoding = source.encoding or 'utf-8'
        raw_content = self._read_file(source.path, encoding)
        
        # Get language
        path = Path(source.path)
        ext = path.suffix.lower()
        language = self.LANGUAGE_MAP.get(ext, 'unknown')
        
        # Extract structured information
        structure_info = self._extract_structure_info(raw_content, language)
        
        # Combine raw content with structure info
        content_parts = []
        
        if structure_info:
            content_parts.append("=== Code Structure ===\n")
            content_parts.append(structure_info)
            content_parts.append("\n\n=== Full Code ===\n")
        
        content_parts.append(raw_content)
        
        content = '\n'.join(content_parts)
        
        return content
    
    def _analyze_structure(self, content: str, language: str) -> Dict[str, Any]:
        """
        Analyze code structure and extract counts.
        
        Args:
            content: The code content
            language: The programming language
            
        Returns:
            Dict[str, Any]: Structure information
        """
        structure = {}
        
        if language == 'python':
            structure['function_count'] = len(re.findall(r'^\s*def\s+\w+', content, re.MULTILINE))
            structure['class_count'] = len(re.findall(r'^\s*class\s+\w+', content, re.MULTILINE))
            structure['import_count'] = len(re.findall(r'^\s*(?:import|from)\s+', content, re.MULTILINE))
        
        elif language in ['javascript', 'typescript']:
            structure['function_count'] = len(re.findall(r'function\s+\w+|const\s+\w+\s*=\s*(?:\([^)]*\)|[^=]+)\s*=>', content))
            structure['class_count'] = len(re.findall(r'class\s+\w+', content))
            structure['import_count'] = len(re.findall(r'^\s*import\s+', content, re.MULTILINE))
        
        elif language == 'java':
            structure['method_count'] = len(re.findall(r'(?:public|private|protected)\s+(?:static\s+)?[\w<>]+\s+\w+\s*\(', content))
            structure['class_count'] = len(re.findall(r'(?:public|private)\s+class\s+\w+', content))
            structure['import_count'] = len(re.findall(r'^\s*import\s+', content, re.MULTILINE))
        
        elif language == 'go':
            structure['function_count'] = len(re.findall(r'func\s+\w+', content))
            structure['struct_count'] = len(re.findall(r'type\s+\w+\s+struct', content))
            structure['import_count'] = len(re.findall(r'^\s*import\s+', content, re.MULTILINE))
        
        # Count comments
        structure['comment_lines'] = self._count_comments(content, language)
        
        return structure
    
    def _extract_structure_info(self, content: str, language: str) -> str:
        """
        Extract structured information from code.
        
        Args:
            content: The code content
            language: The programming language
            
        Returns:
            str: Formatted structure information
        """
        info_parts = []
        
        # Extract imports
        imports = self._extract_imports(content, language)
        if imports:
            info_parts.append("Imports/Includes:")
            info_parts.extend(f"  - {imp}" for imp in imports[:20])  # Limit to 20
            if len(imports) > 20:
                info_parts.append(f"  ... and {len(imports) - 20} more")
        
        # Extract functions/methods
        functions = self._extract_functions(content, language)
        if functions:
            info_parts.append("\nFunctions/Methods:")
            info_parts.extend(f"  - {func}" for func in functions[:30])  # Limit to 30
            if len(functions) > 30:
                info_parts.append(f"  ... and {len(functions) - 30} more")
        
        # Extract classes
        classes = self._extract_classes(content, language)
        if classes:
            info_parts.append("\nClasses/Types:")
            info_parts.extend(f"  - {cls}" for cls in classes[:20])  # Limit to 20
            if len(classes) > 20:
                info_parts.append(f"  ... and {len(classes) - 20} more")
        
        # Extract docstrings/comments
        docs = self._extract_documentation(content, language)
        if docs:
            info_parts.append("\nDocumentation:")
            info_parts.extend(f"  {doc}" for doc in docs[:10])  # Limit to 10
            if len(docs) > 10:
                info_parts.append(f"  ... and {len(docs) - 10} more")
        
        return '\n'.join(info_parts)
    
    def _extract_imports(self, content: str, language: str) -> List[str]:
        """Extract import/include statements."""
        imports = []
        
        if language == 'python':
            imports = re.findall(r'^\s*(?:import|from)\s+.+', content, re.MULTILINE)
        elif language in ['javascript', 'typescript']:
            imports = re.findall(r'^\s*import\s+.+', content, re.MULTILINE)
        elif language == 'java':
            imports = re.findall(r'^\s*import\s+.+;', content, re.MULTILINE)
        elif language in ['c', 'cpp', 'c_header', 'cpp_header']:
            imports = re.findall(r'^\s*#include\s+.+', content, re.MULTILINE)
        elif language == 'go':
            imports = re.findall(r'^\s*import\s+.+', content, re.MULTILINE)
        
        return [imp.strip() for imp in imports]
    
    def _extract_functions(self, content: str, language: str) -> List[str]:
        """Extract function/method definitions."""
        functions = []
        
        if language == 'python':
            matches = re.findall(r'^\s*def\s+(\w+)\s*\([^)]*\)', content, re.MULTILINE)
            functions = matches
        elif language in ['javascript', 'typescript']:
            # Function declarations
            matches1 = re.findall(r'function\s+(\w+)\s*\(', content)
            # Arrow functions
            matches2 = re.findall(r'(?:const|let|var)\s+(\w+)\s*=\s*(?:\([^)]*\)|[^=]+)\s*=>', content)
            functions = matches1 + matches2
        elif language == 'java':
            matches = re.findall(r'(?:public|private|protected)\s+(?:static\s+)?[\w<>]+\s+(\w+)\s*\(', content)
            functions = matches
        elif language == 'go':
            matches = re.findall(r'func\s+(?:\([^)]+\)\s+)?(\w+)\s*\(', content)
            functions = matches
        
        return functions
    
    def _extract_classes(self, content: str, language: str) -> List[str]:
        """Extract class/struct/type definitions."""
        classes = []
        
        if language == 'python':
            matches = re.findall(r'^\s*class\s+(\w+)', content, re.MULTILINE)
            classes = matches
        elif language in ['javascript', 'typescript']:
            matches = re.findall(r'class\s+(\w+)', content)
            classes = matches
        elif language == 'java':
            matches = re.findall(r'(?:public|private)\s+class\s+(\w+)', content)
            classes = matches
        elif language == 'go':
            matches = re.findall(r'type\s+(\w+)\s+(?:struct|interface)', content)
            classes = matches
        
        return classes
    
    def _extract_documentation(self, content: str, language: str) -> List[str]:
        """Extract documentation strings and comments."""
        docs = []
        
        if language == 'python':
            # Extract docstrings
            matches = re.findall(r'"""([^"]+)"""|\'\'\'([^\']+)\'\'\'', content, re.DOTALL)
            for match in matches:
                doc = match[0] or match[1]
                doc = doc.strip()
                if doc and len(doc) > 20:  # Only meaningful docs
                    docs.append(doc[:200])  # Limit length
        
        # Extract single-line comments (for all languages)
        if language == 'python':
            comment_pattern = r'#\s*(.+)'
        elif language in ['javascript', 'typescript', 'java', 'c', 'cpp', 'go', 'rust', 'csharp']:
            comment_pattern = r'//\s*(.+)'
        else:
            comment_pattern = None
        
        if comment_pattern:
            matches = re.findall(comment_pattern, content)
            for match in matches:
                match = match.strip()
                if match and len(match) > 20:  # Only meaningful comments
                    docs.append(match[:200])  # Limit length
        
        return docs[:10]  # Limit total docs
    
    def _count_comments(self, content: str, language: str) -> int:
        """Count comment lines in the code."""
        count = 0
        
        if language == 'python':
            count = len(re.findall(r'^\s*#', content, re.MULTILINE))
        elif language in ['javascript', 'typescript', 'java', 'c', 'cpp', 'go', 'rust', 'csharp']:
            count = len(re.findall(r'^\s*//', content, re.MULTILINE))
        
        return count
    
    def _generate_title(self, source: DataSource, content: str) -> str:
        """
        Generate a title for the code file.
        
        Args:
            source: The data source
            content: The extracted content
            
        Returns:
            str: Generated title
        """
        path = Path(source.path)
        
        # Use filename with language
        ext = path.suffix.lower()
        language = self.LANGUAGE_MAP.get(ext, 'code')
        
        return f"{path.stem} ({language})"
