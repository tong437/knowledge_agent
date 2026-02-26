"""
代码文件处理器，用于分析源代码文件。
"""

import re
from pathlib import Path
from typing import Dict, Any, List, Optional

from .base_processor import BaseDataSourceProcessor
from core.models import DataSource, SourceType
from core.exceptions import ProcessingError


class CodeProcessor(BaseDataSourceProcessor):
    """
    代码文件处理器。

    支持多种编程语言，提取代码结构（函数、类、方法）、
    注释和文档字符串、导入语句等信息。
    """

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
        """初始化代码处理器。"""
        super().__init__()

    def get_supported_types(self) -> List[SourceType]:
        """获取此处理器支持的数据源类型列表。"""
        return [SourceType.CODE]

    def validate(self, source: DataSource) -> bool:
        """
        验证代码数据源是否可以被处理。

        Args:
            source: 待验证的数据源

        Returns:
            bool: 可处理返回 True，否则返回 False
        """
        if not super().validate(source):
            return False

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
        从代码数据源中提取元数据。

        Args:
            source: 待提取元数据的数据源

        Returns:
            Dict[str, Any]: 元数据字典
        """
        metadata = super().get_metadata(source)

        path = Path(source.path)
        ext = path.suffix.lower()

        metadata['document_type'] = 'code'
        metadata['language'] = self.LANGUAGE_MAP.get(ext, 'unknown')

        try:
            content = self._read_file(source.path, source.encoding or 'utf-8')

            lines = content.split('\n')
            metadata['line_count'] = len(lines)
            metadata['non_empty_lines'] = sum(1 for line in lines if line.strip())

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
        从代码文件中提取内容。

        Args:
            source: 待提取内容的数据源

        Returns:
            str: 提取的内容（包含结构信息和完整代码）

        Raises:
            ProcessingError: 内容提取失败时抛出
        """
        encoding = source.encoding or 'utf-8'
        raw_content = self._read_file(source.path, encoding)

        path = Path(source.path)
        ext = path.suffix.lower()
        language = self.LANGUAGE_MAP.get(ext, 'unknown')

        structure_info = self._extract_structure_info(raw_content, language)

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
        分析代码结构并提取统计信息。

        Args:
            content: 代码内容
            language: 编程语言

        Returns:
            Dict[str, Any]: 结构信息
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

        structure['comment_lines'] = self._count_comments(content, language)
        return structure

    def _extract_structure_info(self, content: str, language: str) -> str:
        """
        从代码中提取结构化信息。

        Args:
            content: 代码内容
            language: 编程语言

        Returns:
            str: 格式化的结构信息
        """
        info_parts = []

        imports = self._extract_imports(content, language)
        if imports:
            info_parts.append("Imports/Includes:")
            info_parts.extend(f"  - {imp}" for imp in imports[:20])
            if len(imports) > 20:
                info_parts.append(f"  ... and {len(imports) - 20} more")

        functions = self._extract_functions(content, language)
        if functions:
            info_parts.append("\nFunctions/Methods:")
            info_parts.extend(f"  - {func}" for func in functions[:30])
            if len(functions) > 30:
                info_parts.append(f"  ... and {len(functions) - 30} more")

        classes = self._extract_classes(content, language)
        if classes:
            info_parts.append("\nClasses/Types:")
            info_parts.extend(f"  - {cls}" for cls in classes[:20])
            if len(classes) > 20:
                info_parts.append(f"  ... and {len(classes) - 20} more")

        docs = self._extract_documentation(content, language)
        if docs:
            info_parts.append("\nDocumentation:")
            info_parts.extend(f"  {doc}" for doc in docs[:10])
            if len(docs) > 10:
                info_parts.append(f"  ... and {len(docs) - 10} more")

        return '\n'.join(info_parts)

    def _extract_imports(self, content: str, language: str) -> List[str]:
        """提取导入/包含语句。"""
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
        """提取函数/方法定义。"""
        functions = []

        if language == 'python':
            matches = re.findall(r'^\s*def\s+(\w+)\s*\([^)]*\)', content, re.MULTILINE)
            functions = matches
        elif language in ['javascript', 'typescript']:
            matches1 = re.findall(r'function\s+(\w+)\s*\(', content)
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
        """提取类/结构体/类型定义。"""
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
        """提取文档字符串和注释。"""
        docs = []

        if language == 'python':
            matches = re.findall(r'"""([^"]+)"""|\'\'\'([^\']+)\'\'\'', content, re.DOTALL)
            for match in matches:
                doc = match[0] or match[1]
                doc = doc.strip()
                if doc and len(doc) > 20:
                    docs.append(doc[:200])

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
                if match and len(match) > 20:
                    docs.append(match[:200])

        return docs[:10]

    def _count_comments(self, content: str, language: str) -> int:
        """统计代码中的注释行数。"""
        count = 0

        if language == 'python':
            count = len(re.findall(r'^\s*#', content, re.MULTILINE))
        elif language in ['javascript', 'typescript', 'java', 'c', 'cpp', 'go', 'rust', 'csharp']:
            count = len(re.findall(r'^\s*//', content, re.MULTILINE))

        return count

    def _generate_title(self, source: DataSource, content: str) -> str:
        """
        为代码文件生成标题。

        Args:
            source: 数据源
            content: 提取的内容

        Returns:
            str: 生成的标题（文件名 + 语言）
        """
        path = Path(source.path)
        ext = path.suffix.lower()
        language = self.LANGUAGE_MAP.get(ext, 'code')
        return f"{path.stem} ({language})"
