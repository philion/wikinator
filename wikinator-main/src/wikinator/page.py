import json
import yaml
from pathlib import Path
import logging
from typing import Optional, List


log = logging.getLogger(__name__)


class Page:
    """
    Specific class for page, to help with validation, as graphql is strict about params
    """
    content: str
    editor: str
    isPublished: bool
    isPrivate: bool
    locale: str
    path: str
    tags: Optional[List[str]]
    title: str
    description: str

    def __init__(self, content: str, editor: str, isPublished: bool, isPrivate: bool,
                locale: str, path: str, tags: Optional[List[str]], title: str, description: str):
        self.content = content
        self.editor = editor
        self.isPublished = isPublished
        self.isPrivate = isPrivate
        self.locale = locale
        self.path = path
        self.tags = tags or []
        self.title = title
        self.description = description

    @classmethod
    def load(cls, params: dict):
        return cls(
            content=params["content"],
            editor=params["editor"],
            isPublished=params["isPublished"],
            isPrivate=params["isPrivate"],
            locale=params["locale"],
            path=params["path"],
            tags=params.get("tags", []),
            title=params["title"],
            description=params["description"],
        )

    @classmethod
    def load_json(cls, json_str: str):
        return cls.load(json.loads(json_str))

    @classmethod
    def load_file(cls, filename: str):
        """Load a page from a markdown file with YAML frontmatter."""
        file_path = Path(filename)
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {filename}")
        
        content = file_path.read_text(encoding='utf-8')
        
        # Parse YAML frontmatter if present
        metadata = {}
        if content.startswith('---'):
            try:
                parts = content.split('---', 2)
                if len(parts) >= 3:
                    yaml_content = parts[1].strip()
                    metadata = yaml.safe_load(yaml_content) or {}
                    content = parts[2].strip()
            except yaml.YAMLError as e:
                log.warning(f"Failed to parse YAML frontmatter in {filename}: {e}")
        
        # Extract title from first heading if not in metadata
        title = metadata.get('title', file_path.stem)
        if not metadata.get('title'):
            lines = content.split('\n')
            for line in lines:
                if line.startswith('# '):
                    title = line[2:].strip()
                    break
        
        return cls(
            content=content,
            editor=metadata.get('editor', 'markdown'),
            isPublished=metadata.get('isPublished', False),
            isPrivate=metadata.get('isPrivate', True),
            locale=metadata.get('locale', 'en'),
            path=str(file_path.relative_to(Path.cwd())),
            tags=metadata.get('tags', []),
            title=title,
            description=metadata.get('description', f"Generated from {filename}"),
        )

    def filename(self, root: Optional[Path] = None) -> Path:
        """
        Determine the file name for this page.
        If `root` is supplied, that file name will be relative to that path.
        """
        # Clean the path to avoid invalid characters
        clean_path = self.path.replace('\\', '/').replace(':', '_')
        filename = f"{clean_path}.md"
        
        if root:
            return Path(root) / filename
        else:
            return Path(filename)

    def write_file(self, filename: str) -> None:
        """Write content and metadata to specified file."""
        target = Path(filename)
        
        # Ensure required directories exist
        target.parent.mkdir(parents=True, exist_ok=True)
        
        # Create YAML frontmatter
        metadata = {
            'title': self.title,
            'editor': self.editor,
            'isPublished': self.isPublished,
            'isPrivate': self.isPrivate,
            'locale': self.locale,
            'path': self.path,
            'tags': self.tags,
            'description': self.description,
        }
        
        # Write the content with frontmatter
        with open(target, 'w', encoding='utf-8') as output_file:
            output_file.write('---\n')
            yaml.dump(metadata, output_file, default_flow_style=False, allow_unicode=True)
            output_file.write('---\n\n')
            output_file.write(self.content)

    def write(self, root: str) -> None:
        """
        Output the converted document to the specified directory `root`.
        Use the stored path to output relative to the provided root.
        """
        filename = self.filename(Path(root))
        self.write_file(str(filename))
        log.info(f"Wrote page '{self.title}' to {filename}")

    def to_dict(self) -> dict:
        """Convert page to dictionary for API calls."""
        return {
            'content': self.content,
            'editor': self.editor,
            'isPublished': self.isPublished,
            'isPrivate': self.isPrivate,
            'locale': self.locale,
            'path': self.path,
            'tags': self.tags,
            'title': self.title,
            'description': self.description,
        }

    def __str__(self) -> str:
        return f"Page(title='{self.title}', path='{self.path}')"

    def __repr__(self) -> str:
        return self.__str__()
