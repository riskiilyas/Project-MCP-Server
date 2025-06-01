#!/usr/bin/env python3
import json
import os
import sys
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional
import mimetypes
import re

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    filename='universal_mcp_debug.log',
    format='%(asctime)s - %(levelname)s - %(message)s'
)

class UniversalProjectMCP:
    def __init__(self):
        # Start with current directory, but allow changing via method
        self.project_root = Path(".").resolve()
        self._config_file = Path.home() / ".universal_mcp_config.json"
        self._load_config()
        
    def _load_config(self):
        """Load saved configuration"""
        try:
            if self._config_file.exists():
                with open(self._config_file, 'r') as f:
                    config = json.load(f)
                    if 'project_root' in config:
                        self.project_root = Path(config['project_root']).resolve()
                        logging.info(f"Loaded project root from config: {self.project_root}")
        except Exception as e:
            logging.error(f"Error loading config: {e}")
    
    def _save_config(self):
        """Save current configuration"""
        try:
            config = {
                'project_root': str(self.project_root)
            }
            with open(self._config_file, 'w') as f:
                json.dump(config, f, indent=2)
            logging.info(f"Saved config: {config}")
        except Exception as e:
            logging.error(f"Error saving config: {e}")
    
    def set_project_path(self, path: str) -> Dict[str, Any]:
        """Set the project root path and save it"""
        try:
            new_path = Path(path).resolve()
            
            if not new_path.exists():
                return {"error": f"Path does not exist: {path}"}
            
            if not new_path.is_dir():
                return {"error": f"Path is not a directory: {path}"}
            
            old_path = str(self.project_root)
            self.project_root = new_path
            self._save_config()
            
            return {
                "success": True,
                "message": f"Project path changed from '{old_path}' to '{new_path}'",
                "old_path": old_path,
                "new_path": str(new_path)
            }
            
        except Exception as e:
            return {"error": f"Error setting project path: {str(e)}"}
    
    def get_project_path(self) -> Dict[str, Any]:
        """Get current project path"""
        return {
            "project_path": str(self.project_root),
            "exists": self.project_root.exists(),
            "is_directory": self.project_root.is_dir()
        }
        
    def get_structure(self, path: str = "", max_depth: int = 2) -> Dict[str, Any]:
        """Get project directory structure with configurable depth"""
        base_path = self.project_root / path if path else self.project_root
        
        def build_tree(current_path: Path, current_depth: int = 0) -> Dict[str, Any]:
            if current_depth >= max_depth:
                return {"type": "directory", "truncated": True}
            
            try:
                if not current_path.exists():
                    return {"error": "Path not found"}
                
                if current_path.is_file():
                    stat = current_path.stat()
                    return {
                        "type": "file",
                        "size": stat.st_size,
                        "extension": current_path.suffix
                    }
                
                # Directory processing
                items = list(current_path.iterdir())
                result = {"type": "directory", "children": {}}
                
                # Sort: directories first, then files, alphabetically within each group
                dirs = sorted([item for item in items if item.is_dir()], key=lambda x: x.name.lower())
                files = sorted([item for item in items if item.is_file()], key=lambda x: x.name.lower())
                
                for item in dirs + files:
                    # Skip hidden files/dirs unless explicitly requested
                    if item.name.startswith('.') and item.name not in {'.env', '.gitignore', '.dockerignore'}:
                        continue
                        
                    result["children"][item.name] = build_tree(item, current_depth + 1)
                
                return result
                
            except PermissionError:
                return {"type": "directory", "error": "Permission denied"}
            except Exception as e:
                return {"error": str(e)}
        
        return {
            "name": base_path.name,
            "path": str(base_path.relative_to(self.project_root)) if path else "",
            "project_root": str(self.project_root),
            "structure": build_tree(base_path)
        }

    def read_file(self, file_path: str, start_line: int = 1, end_line: Optional[int] = None) -> Dict[str, Any]:
        """Read file content with optional line range"""
        try:
            full_path = self.project_root / file_path
            
            if not full_path.exists():
                return {"error": f"File not found: {file_path}"}
            
            if not full_path.is_file():
                return {"error": f"Path is not a file: {file_path}"}
            
            # Check file size (limit to 5MB)
            file_size = full_path.stat().st_size
            if file_size > 5 * 1024 * 1024:
                return {"error": f"File too large ({file_size} bytes). Maximum 5MB allowed."}
            
            # Detect MIME type
            mime_type, encoding = mimetypes.guess_type(str(full_path))
            
            # Try to read as text
            encodings_to_try = ['utf-8', 'utf-16', 'latin-1', 'cp1252']
            content = None
            used_encoding = None
            
            for enc in encodings_to_try:
                try:
                    with open(full_path, 'r', encoding=enc) as f:
                        content = f.read()
                    used_encoding = enc
                    break
                except UnicodeDecodeError:
                    continue
                except Exception:
                    break
            
            if content is None:
                return {"error": "Cannot read file as text (binary file or encoding issue)"}
            
            lines = content.splitlines(keepends=True)
            total_lines = len(lines)
            
            # Handle line range
            if end_line is None:
                end_line = total_lines
            
            start_idx = max(0, start_line - 1)
            end_idx = min(total_lines, end_line)
            
            selected_content = "".join(lines[start_idx:end_idx])
            
            return {
                "file_path": file_path,
                "full_path": str(full_path),
                "content": selected_content,
                "total_lines": total_lines,
                "returned_lines": end_idx - start_idx,
                "line_range": f"{start_line}-{end_idx}",
                "file_size": file_size,
                "mime_type": mime_type,
                "encoding": used_encoding
            }
            
        except Exception as e:
            return {"error": f"Error reading file: {str(e)}"}

    def search_files(self, pattern: str = "*", path: str = "", include_content: bool = False, 
                    file_extensions: Optional[List[str]] = None, max_results: int = 100) -> List[Dict[str, Any]]:
        """Search for files by pattern"""
        import fnmatch
        
        search_path = self.project_root / path if path else self.project_root
        results = []
        count = 0
        
        try:
            for root, dirs, files in os.walk(search_path):
                # Skip common build/cache directories
                dirs[:] = [d for d in dirs if d not in {
                    '.git', 'node_modules', '__pycache__', '.venv', 'venv', 
                    'target', 'build', 'dist', '.cache', 'tmp', 'temp'
                }]
                
                for file in files:
                    if count >= max_results:
                        break
                        
                    file_path = Path(root) / file
                    relative_path = file_path.relative_to(self.project_root)
                    
                    # Filter by extension if specified
                    if file_extensions and file_path.suffix.lower() not in file_extensions:
                        continue
                    
                    # Check if filename matches pattern
                    if fnmatch.fnmatch(file.lower(), pattern.lower()):
                        try:
                            stat = file_path.stat()
                            result = {
                                "path": str(relative_path),
                                "name": file,
                                "size": stat.st_size,
                                "extension": file_path.suffix,
                                "directory": str(relative_path.parent)
                            }
                            
                            # Search in content if requested and file is small enough
                            if include_content and stat.st_size < 1024 * 1024:  # Max 1MB for content search
                                try:
                                    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                                        content = f.read()
                                        if pattern.lower().replace('*', '') in content.lower():
                                            # Find matching lines
                                            lines = content.split('\n')
                                            matches = []
                                            for i, line in enumerate(lines, 1):
                                                if pattern.lower().replace('*', '') in line.lower():
                                                    matches.append({
                                                        "line_number": i,
                                                        "content": line.strip()
                                                    })
                                                    if len(matches) >= 5:  # Limit matches per file
                                                        break
                                            result["content_matches"] = matches
                                except:
                                    pass  # Skip files that can't be read
                            
                            results.append(result)
                            count += 1
                            
                        except Exception:
                            continue
                            
                if count >= max_results:
                    break
            
            return sorted(results, key=lambda x: (x['directory'], x['name']))
            
        except Exception as e:
            return [{"error": f"Search failed: {str(e)}"}]

    def search_in_files(self, keyword: str, path: str = "", file_extensions: Optional[List[str]] = None, 
                    max_results: int = 50, case_sensitive: bool = False, 
                    max_matches_per_file: int = 10) -> Dict[str, Any]:
        """Search for keyword within file contents and return matching files with context"""
        import fnmatch
        
        search_path = self.project_root / path if path else self.project_root
        results = {
            "keyword": keyword,
            "search_path": str(search_path.relative_to(self.project_root)) if path else "",
            "case_sensitive": case_sensitive,
            "total_files_searched": 0,
            "files_with_matches": 0,
            "matches": []
        }
        
        if not keyword.strip():
            return {"error": "Keyword cannot be empty"}
        
        # Prepare keyword for search
        search_keyword = keyword if case_sensitive else keyword.lower()
        
        try:
            for root, dirs, files in os.walk(search_path):
                # Skip common build/cache directories
                dirs[:] = [d for d in dirs if d not in {
                    '.git', 'node_modules', '__pycache__', '.venv', 'venv', 
                    'target', 'build', 'dist', '.cache', 'tmp', 'temp', '.next',
                    'coverage', '.nyc_output', 'logs', '.logs'
                }]
                
                for file in files:
                    if len(results["matches"]) >= max_results:
                        break
                        
                    file_path = Path(root) / file
                    relative_path = file_path.relative_to(self.project_root)
                    
                    # Filter by extension if specified
                    if file_extensions:
                        if not any(file_path.suffix.lower() == ext.lower() if ext.startswith('.') 
                                else file_path.suffix.lower() == f'.{ext.lower()}' 
                                for ext in file_extensions):
                            continue
                    
                    # Skip binary files and very large files
                    try:
                        stat = file_path.stat()
                        if stat.st_size > 10 * 1024 * 1024:  # Skip files larger than 10MB
                            continue
                            
                        # Check if file might be binary
                        if self._is_likely_binary_file(file_path):
                            continue
                            
                    except Exception:
                        continue
                    
                    results["total_files_searched"] += 1
                    
                    # Search in file content
                    try:
                        encodings_to_try = ['utf-8', 'utf-16', 'latin-1', 'cp1252']
                        content = None
                        used_encoding = None
                        
                        for enc in encodings_to_try:
                            try:
                                with open(file_path, 'r', encoding=enc) as f:
                                    content = f.read()
                                used_encoding = enc
                                break
                            except UnicodeDecodeError:
                                continue
                            except Exception:
                                break
                        
                        if content is None:
                            continue
                        
                        # Search for keyword
                        search_content = content if case_sensitive else content.lower()
                        
                        if search_keyword in search_content:
                            results["files_with_matches"] += 1
                            
                            # Find all matches with line numbers and context
                            lines = content.split('\n')
                            matches_in_file = []
                            
                            for line_num, line in enumerate(lines, 1):
                                search_line = line if case_sensitive else line.lower()
                                
                                if search_keyword in search_line:
                                    # Find all occurrences in this line
                                    start = 0
                                    while True:
                                        pos = search_line.find(search_keyword, start)
                                        if pos == -1:
                                            break
                                        
                                        # Get context around the match
                                        context_start = max(0, pos - 50)
                                        context_end = min(len(line), pos + len(keyword) + 50)
                                        context = line[context_start:context_end]
                                        
                                        # Highlight the match
                                        if not case_sensitive:
                                            # Find the actual match in original case
                                            actual_match_start = line.lower().find(search_keyword, pos)
                                            if actual_match_start != -1:
                                                actual_match = line[actual_match_start:actual_match_start + len(keyword)]
                                            else:
                                                actual_match = keyword
                                        else:
                                            actual_match = keyword
                                        
                                        matches_in_file.append({
                                            "line_number": line_num,
                                            "column": pos + 1,
                                            "line_content": line.strip(),
                                            "context": context,
                                            "matched_text": actual_match
                                        })
                                        
                                        start = pos + 1
                                        
                                        if len(matches_in_file) >= max_matches_per_file:
                                            break
                                    
                                    if len(matches_in_file) >= max_matches_per_file:
                                        break
                            
                            if matches_in_file:
                                results["matches"].append({
                                    "file_path": str(relative_path),
                                    "file_name": file,
                                    "file_size": stat.st_size,
                                    "encoding": used_encoding,
                                    "match_count": len(matches_in_file),
                                    "matches": matches_in_file
                                })
                    
                    except Exception as e:
                        logging.debug(f"Error searching in file {file_path}: {e}")
                        continue
                
                if len(results["matches"]) >= max_results:
                    break
            
            # Sort results by relevance (number of matches, then by file name)
            results["matches"].sort(key=lambda x: (-x["match_count"], x["file_name"]))
            
            return results
            
        except Exception as e:
            return {"error": f"Search failed: {str(e)}"}

    def _is_likely_binary_file(self, file_path: Path) -> bool:
        """Check if file is likely binary by extension and content sampling"""
        # Check extension first
        binary_extensions = {
            '.exe', '.dll', '.so', '.dylib', '.bin', '.dat', '.db', '.sqlite',
            '.jpg', '.jpeg', '.png', '.gif', '.bmp', '.ico', '.tiff', '.webp',
            '.mp3', '.mp4', '.avi', '.mov', '.wav', '.flac', '.ogg',
            '.pdf', '.doc', '.docx', '.xls', '.xlsx', '.ppt', '.pptx',
            '.zip', '.rar', '.7z', '.tar', '.gz', '.bz2',
            '.woff', '.woff2', '.ttf', '.otf', '.eot'
        }
        
        if file_path.suffix.lower() in binary_extensions:
            return True
        
        # Sample first few bytes to check for binary content
        try:
            with open(file_path, 'rb') as f:
                sample = f.read(512)
                # Check for null bytes (common in binary files)
                if b'\x00' in sample:
                    return True
                # Check for high ratio of non-printable characters
                printable_chars = sum(1 for byte in sample if 32 <= byte < 127 or byte in [9, 10, 13])
                if len(sample) > 0 and printable_chars / len(sample) < 0.7:
                    return True
        except Exception:
            return True
        
        return False


    def list_directory(self, path: str = "") -> Dict[str, Any]:
        """List directory contents (flat view)"""
        try:
            target_path = self.project_root / path if path else self.project_root
            
            if not target_path.exists():
                return {"error": f"Directory not found: {path}"}
            
            if not target_path.is_dir():
                return {"error": f"Path is not a directory: {path}"}
            
            items = []
            
            for item in target_path.iterdir():
                try:
                    stat = item.stat()
                    item_info = {
                        "name": item.name,
                        "type": "directory" if item.is_dir() else "file",
                        "size": stat.st_size if item.is_file() else None,
                        "modified": stat.st_mtime,
                    }
                    
                    if item.is_file():
                        item_info["extension"] = item.suffix
                        # Get MIME type
                        mime_type, _ = mimetypes.guess_type(str(item))
                        item_info["mime_type"] = mime_type
                    
                    items.append(item_info)
                    
                except Exception:
                    continue
            
            # Sort: directories first, then files
            items.sort(key=lambda x: (x['type'] == 'file', x['name'].lower()))
            
            return {
                "path": path,
                "full_path": str(target_path),
                "items": items,
                "total_count": len(items)
            }
            
        except Exception as e:
            return {"error": f"Error listing directory: {str(e)}"}

    def get_file_info(self, file_path: str) -> Dict[str, Any]:
        """Get detailed file information"""
        try:
            full_path = self.project_root / file_path
            
            if not full_path.exists():
                return {"error": f"File not found: {file_path}"}
            
            stat = full_path.stat()
            mime_type, encoding = mimetypes.guess_type(str(full_path))
            
            info = {
                "path": file_path,
                "full_path": str(full_path),
                "name": full_path.name,
                "size": stat.st_size,
                "extension": full_path.suffix,
                "mime_type": mime_type,
                "encoding": encoding,
                "is_directory": full_path.is_dir(),
                "is_file": full_path.is_file(),
                "modified": stat.st_mtime,
                "created": stat.st_ctime,
            }
            
            # For text files, get additional info
            if full_path.is_file() and stat.st_size < 1024 * 1024:  # Max 1MB
                try:
                    with open(full_path, 'r', encoding='utf-8', errors='ignore') as f:
                        content = f.read()
                        lines = content.split('\n')
                        info.update({
                            "lines": len(lines),
                            "characters": len(content),
                            "words": len(content.split()),
                            "blank_lines": sum(1 for line in lines if not line.strip())
                        })
                except:
                    pass
            
            return info
            
        except Exception as e:
            return {"error": f"Error getting file info: {str(e)}"}
    
    # ===== NEW METHODS =====
    
    def get_project_summary(self) -> Dict[str, Any]:
        """Get comprehensive project overview and analysis"""
        try:
            summary = {
                "project_root": str(self.project_root),
                "project_name": self.project_root.name
            }
            
            # Detect project type
            summary["project_type"] = self._detect_project_type()
            
            # Find README files
            summary["readme_files"] = self._find_readme_files()
            
            # Count files by extension
            summary["file_statistics"] = self._count_files_by_extension()
            
            # Find main directories
            summary["main_directories"] = self._get_main_directories()
            
            # Calculate total project size
            summary["total_size_mb"] = self._calculate_project_size()
            
            # Estimate complexity
            summary["estimated_complexity"] = self._estimate_complexity()
            
            return summary
            
        except Exception as e:
            return {"error": f"Error analyzing project: {str(e)}"}
    
    def get_dependencies(self) -> Dict[str, Any]:
        """Extract and analyze project dependencies"""
        try:
            dependencies = {
                "dependency_files": {},
                "total_dependencies": 0,
                "dev_dependencies": 0,
                "summary": []
            }
            
            # Common dependency files to check
            dep_files = {
                "package.json": self._parse_package_json,
                "pubspec.yaml": self._parse_pubspec_yaml,
                "requirements.txt": self._parse_requirements_txt,
                "Pipfile": self._parse_pipfile,
                "composer.json": self._parse_composer_json,
                "go.mod": self._parse_go_mod,
                "Cargo.toml": self._parse_cargo_toml,
                "pom.xml": self._parse_pom_xml,
                "build.gradle": self._parse_gradle
            }
            
            for filename, parser in dep_files.items():
                file_path = self.project_root / filename
                if file_path.exists():
                    try:
                        parsed = parser(file_path)
                        if parsed:
                            dependencies["dependency_files"][filename] = parsed
                            dependencies["total_dependencies"] += len(parsed.get("dependencies", {}))
                            dependencies["dev_dependencies"] += len(parsed.get("dev_dependencies", {}))
                    except Exception as e:
                        dependencies["dependency_files"][filename] = {"error": str(e)}
            
            # Create summary
            for filename, data in dependencies["dependency_files"].items():
                if "error" not in data:
                    deps_count = len(data.get("dependencies", {}))
                    dev_deps_count = len(data.get("dev_dependencies", {}))
                    dependencies["summary"].append({
                        "file": filename,
                        "dependencies": deps_count,
                        "dev_dependencies": dev_deps_count,
                        "type": self._get_dependency_file_type(filename)
                    })
            
            return dependencies
            
        except Exception as e:
            return {"error": f"Error reading dependencies: {str(e)}"}
    
    def find_entry_points(self) -> List[Dict[str, Any]]:
        """Find main entry points and important files of the application"""
        try:
            entry_points = []
            
            # Entry point patterns for different project types
            patterns = {
                "main_files": ["main.*", "index.*", "app.*", "server.*", "run.*"],
                "config_files": ["*.config.*", "config.*", "settings.*", ".env*"],
                "route_files": ["routes.*", "urls.py", "router.*", "api.*"],
                "build_files": ["Dockerfile", "docker-compose.*", "Makefile", "build.*"],
                "test_files": ["test.*", "*test.*", "spec.*", "*spec.*"]
            }
            
            for category, file_patterns in patterns.items():
                for pattern in file_patterns:
                    matches = self.search_files(pattern=pattern, max_results=20)
                    
                    for match in matches:
                        if isinstance(match, dict) and "error" not in match:
                            entry_points.append({
                                "file": match["path"],
                                "name": match["name"],
                                "category": category,
                                "type": self._classify_entry_point(match["name"]),
                                "size": match["size"],
                                "directory": match["directory"]
                            })
            
            # Remove duplicates and sort by importance
            seen = set()
            unique_points = []
            for point in entry_points:
                key = point["file"]
                if key not in seen:
                    seen.add(key)
                    unique_points.append(point)
            
            # Sort by category importance and file name
            category_order = {"main_files": 1, "config_files": 2, "route_files": 3, "build_files": 4, "test_files": 5}
            unique_points.sort(key=lambda x: (category_order.get(x["category"], 6), x["name"]))
            
            return unique_points[:50]  # Limit results
            
        except Exception as e:
            return [{"error": f"Error finding entry points: {str(e)}"}]
    
    # Helper methods for new functionality
    
    def _detect_project_type(self) -> str:
        """Detect the type of project based on files and structure"""
        indicators = [
            ("Flutter", ["pubspec.yaml", "lib", "android", "ios"]),
            ("React", ["package.json", "src", "public", "node_modules"]),
            ("Next.js", ["next.config.js", "pages", "package.json"]),
            ("Vue.js", ["vue.config.js", "src", "package.json"]),
            ("Angular", ["angular.json", "src", "package.json"]),
            ("Django", ["manage.py", "requirements.txt", "settings.py"]),
            ("FastAPI", ["main.py", "requirements.txt", "app"]),
            ("Laravel", ["composer.json", "artisan", "app", "routes"]),
            ("Node.js", ["package.json", "node_modules"]),
            ("Python", ["requirements.txt", "*.py"]),
            ("Go", ["go.mod", "main.go"]),
            ("Rust", ["Cargo.toml", "src"]),
            ("Java", ["pom.xml", "src/main/java"]),
            ("C#/.NET", ["*.csproj", "*.sln"]),
            ("PHP", ["composer.json", "*.php"]),
        ]
        
        for project_type, files in indicators:
            score = 0
            for indicator in files:
                if "*" in indicator:
                    # Wildcard pattern
                    matches = self.search_files(pattern=indicator, max_results=1)
                    if matches and not any("error" in m for m in matches if isinstance(m, dict)):
                        score += 1
                else:
                    # Exact file/directory
                    if (self.project_root / indicator).exists():
                        score += 1
            
            if score >= 2:  # Need at least 2 indicators
                return project_type
        
        return "Unknown"
    
    def _find_readme_files(self) -> List[Dict[str, str]]:
        """Find README files in the project"""
        readme_patterns = ["README*", "readme*", "Read*"]
        readme_files = []
        
        for pattern in readme_patterns:
            matches = self.search_files(pattern=pattern, max_results=10)
            for match in matches:
                if isinstance(match, dict) and "error" not in match:
                    readme_files.append({
                        "path": match["path"],
                        "name": match["name"],
                        "size": match["size"]
                    })
        
        # Remove duplicates
        seen = set()
        unique_readmes = []
        for readme in readme_files:
            if readme["path"] not in seen:
                seen.add(readme["path"])
                unique_readmes.append(readme)
        
        return unique_readmes
    
    def _count_files_by_extension(self) -> Dict[str, int]:
        """Count files by their extensions"""
        extension_counts = {}
        
        try:
            for root, dirs, files in os.walk(self.project_root):
                # Skip build/cache directories
                dirs[:] = [d for d in dirs if d not in {
                    '.git', 'node_modules', '__pycache__', '.venv', 'venv',
                    'target', 'build', 'dist', '.cache', 'tmp', 'temp'
                }]
                
                for file in files:
                    ext = Path(file).suffix.lower()
                    if not ext:
                        ext = "no_extension"
                    extension_counts[ext] = extension_counts.get(ext, 0) + 1
        except Exception:
            pass
        
        # Sort by count
        return dict(sorted(extension_counts.items(), key=lambda x: x[1], reverse=True))
    
    def _get_main_directories(self) -> List[Dict[str, Any]]:
        """Get main directories in project root"""
        directories = []
        
        try:
            for item in self.project_root.iterdir():
                if item.is_dir() and not item.name.startswith('.'):
                    # Count files in directory
                    file_count = 0
                    try:
                        for _ in item.rglob('*'):
                            file_count += 1
                            if file_count > 1000:  # Limit counting for performance
                                break
                    except:
                        file_count = 0
                    
                    directories.append({
                        "name": item.name,
                        "file_count": file_count,
                        "type": self._classify_directory(item.name)
                    })
        except Exception:
            pass
        
        return sorted(directories, key=lambda x: x["file_count"], reverse=True)
    
    def _calculate_project_size(self) -> float:
        """Calculate total project size in MB"""
        total_size = 0
        
        try:
            for root, dirs, files in os.walk(self.project_root):
                # Skip build/cache directories
                dirs[:] = [d for d in dirs if d not in {
                    '.git', 'node_modules', '__pycache__', '.venv', 'venv',
                    'target', 'build', 'dist', '.cache', 'tmp', 'temp'
                }]
                
                for file in files:
                    try:
                        file_path = Path(root) / file
                        total_size += file_path.stat().st_size
                    except:
                        continue
        except Exception:
            pass
        
        return round(total_size / (1024 * 1024), 2)  # Convert to MB
    
    def _estimate_complexity(self) -> str:
        """Estimate project complexity based on file counts and structure"""
        file_stats = self._count_files_by_extension()
        total_files = sum(file_stats.values())
        
        if total_files < 10:
            return "Very Simple"
        elif total_files < 50:
            return "Simple"
        elif total_files < 200:
            return "Medium"
        elif total_files < 500:
            return "Complex"
        else:
            return "Very Complex"
    
    def _classify_directory(self, dir_name: str) -> str:
        """Classify directory type"""
        classifications = {
            "source": ["src", "lib", "app", "source"],
            "config": ["config", "configs", "settings", "conf"],
            "assets": ["assets", "static", "public", "resources", "images", "img"],
            "tests": ["test", "tests", "spec", "specs", "__tests__"],
            "docs": ["docs", "documentation", "doc"],
            "build": ["build", "dist", "out", "target", "bin"],
            "dependencies": ["node_modules", "vendor", "packages"],
        }
        
        dir_lower = dir_name.lower()
        for category, keywords in classifications.items():
            if any(keyword in dir_lower for keyword in keywords):
                return category
        
        return "other"
    
    def _classify_entry_point(self, filename: str) -> str:
        """Classify entry point file type"""
        name_lower = filename.lower()
        
        if any(x in name_lower for x in ["main", "index", "app"]):
            return "main_entry"
        elif any(x in name_lower for x in ["config", "settings"]):
            return "configuration"
        elif any(x in name_lower for x in ["route", "url", "api"]):
            return "routing"
        elif any(x in name_lower for x in ["test", "spec"]):
            return "testing"
        elif any(x in name_lower for x in ["docker", "make", "build"]):
            return "build_system"
        else:
            return "other"
    
    def _get_dependency_file_type(self, filename: str) -> str:
        """Get the type of dependency file"""
        types = {
            "package.json": "Node.js/JavaScript",
            "pubspec.yaml": "Flutter/Dart",
            "requirements.txt": "Python",
            "Pipfile": "Python (Pipenv)",
            "composer.json": "PHP",
            "go.mod": "Go",
            "Cargo.toml": "Rust",
            "pom.xml": "Java (Maven)",
            "build.gradle": "Java/Android (Gradle)"
        }
        return types.get(filename, "Unknown")
    
    # Dependency file parsers
    
    def _parse_package_json(self, file_path: Path) -> Dict[str, Any]:
        """Parse package.json file"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            return {
                "dependencies": data.get("dependencies", {}),
                "dev_dependencies": data.get("devDependencies", {}),
                "scripts": data.get("scripts", {}),
                "name": data.get("name", ""),
                "version": data.get("version", "")
            }
        except Exception:
            return {"error": "Failed to parse package.json"}
    
    def _parse_pubspec_yaml(self, file_path: Path) -> Dict[str, Any]:
        """Parse pubspec.yaml file"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Simple YAML parsing for dependencies
            dependencies = {}
            dev_dependencies = {}
            in_deps = False
            in_dev_deps = False
            
            for line in content.split('\n'):
                line = line.strip()
                if line.startswith('dependencies:'):
                    in_deps = True
                    in_dev_deps = False
                elif line.startswith('dev_dependencies:'):
                    in_deps = False
                    in_dev_deps = True
                elif line and not line.startswith(' ') and ':' in line:
                    in_deps = False
                    in_dev_deps = False
                elif line.startswith('  ') and ':' in line and (in_deps or in_dev_deps):
                    parts = line.split(':')
                    if len(parts) >= 2:
                        dep_name = parts[0].strip()
                        dep_version = parts[1].strip()
                        if in_deps:
                            dependencies[dep_name] = dep_version
                        elif in_dev_deps:
                            dev_dependencies[dep_name] = dep_version
            
            return {
                "dependencies": dependencies,
                "dev_dependencies": dev_dependencies
            }
        except Exception:
            return {"error": "Failed to parse pubspec.yaml"}
    
    def _parse_requirements_txt(self, file_path: Path) -> Dict[str, Any]:
        """Parse requirements.txt file"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            dependencies = {}
            for line in lines:
                line = line.strip()
                if line and not line.startswith('#'):
                    # Split by various version specifiers
                    for sep in ['==', '>=', '<=', '>', '<', '~=', '!=']:
                        if sep in line:
                            parts = line.split(sep)
                            dependencies[parts[0].strip()] = f"{sep}{parts[1].strip()}"
                            break
                    else:
                        dependencies[line] = ""
            
            return {
                "dependencies": dependencies,
                "dev_dependencies": {}
            }
        except Exception:
            return {"error": "Failed to parse requirements.txt"}
    
    def _parse_pipfile(self, file_path: Path) -> Dict[str, Any]:
        """Parse Pipfile"""
        try:
            # Simple Pipfile parsing
            dependencies = {}
            dev_dependencies = {}
            
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            in_packages = False
            in_dev_packages = False
            
            for line in content.split('\n'):
                line = line.strip()
                if line.startswith('[packages]'):
                    in_packages = True
                    in_dev_packages = False
                elif line.startswith('[dev-packages]'):
                    in_packages = False
                    in_dev_packages = True
                elif line.startswith('[') and line.endswith(']'):
                    in_packages = False
                    in_dev_packages = False
                elif '=' in line and (in_packages or in_dev_packages):
                    parts = line.split('=', 1)
                    if len(parts) == 2:
                        dep_name = parts[0].strip()
                        dep_version = parts[1].strip().strip('"\'')
                        if in_packages:
                            dependencies[dep_name] = dep_version
                        elif in_dev_packages:
                            dev_dependencies[dep_name] = dep_version
            
            return {
                "dependencies": dependencies,
                "dev_dependencies": dev_dependencies
            }
        except Exception:
            return {"error": "Failed to parse Pipfile"}
    
    def _parse_composer_json(self, file_path: Path) -> Dict[str, Any]:
        """Parse composer.json file"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            return {
                "dependencies": data.get("require", {}),
                "dev_dependencies": data.get("require-dev", {}),
                "name": data.get("name", ""),
                "version": data.get("version", "")
            }
        except Exception:
            return {"error": "Failed to parse composer.json"}
    
    def _parse_go_mod(self, file_path: Path) -> Dict[str, Any]:
        """Parse go.mod file"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            dependencies = {}
            in_require = False
            
            for line in content.split('\n'):
                line = line.strip()
                if line.startswith('require'):
                    if '(' in line:
                        in_require = True
                    else:
                        # Single line require
                        parts = line.replace('require', '').strip().split()
                        if len(parts) >= 2:
                            dependencies[parts[0]] = parts[1]
                elif in_require and line == ')':
                    in_require = False
                elif in_require and line:
                    parts = line.split()
                    if len(parts) >= 2:
                        dependencies[parts[0]] = parts[1]
            
            return {
                "dependencies": dependencies,
                "dev_dependencies": {}
            }
        except Exception:
            return {"error": "Failed to parse go.mod"}
    
    def _parse_cargo_toml(self, file_path: Path) -> Dict[str, Any]:
        """Parse Cargo.toml file"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            dependencies = {}
            dev_dependencies = {}
            in_deps = False
            in_dev_deps = False
            
            for line in content.split('\n'):
                line = line.strip()
                if line.startswith('[dependencies]'):
                    in_deps = True
                    in_dev_deps = False
                elif line.startswith('[dev-dependencies]'):
                    in_deps = False
                    in_dev_deps = True
                elif line.startswith('[') and line.endswith(']'):
                    in_deps = False
                    in_dev_deps = False
                elif '=' in line and (in_deps or in_dev_deps):
                    parts = line.split('=', 1)
                    if len(parts) == 2:
                        dep_name = parts[0].strip()
                        dep_version = parts[1].strip().strip('"\'')
                        if in_deps:
                            dependencies[dep_name] = dep_version
                        elif in_dev_deps:
                            dev_dependencies[dep_name] = dep_version
            
            return {
                "dependencies": dependencies,
                "dev_dependencies": dev_dependencies
            }
        except Exception:
            return {"error": "Failed to parse Cargo.toml"}
    
    def _parse_pom_xml(self, file_path: Path) -> Dict[str, Any]:
        """Parse pom.xml file (basic parsing)"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            dependencies = {}
            # Very basic XML parsing for dependencies
            import re
            
            # Find dependency blocks
            dep_pattern = r'<dependency>.*?</dependency>'
            matches = re.findall(dep_pattern, content, re.DOTALL)
            
            for match in matches:
                group_match = re.search(r'<groupId>(.*?)</groupId>', match)
                artifact_match = re.search(r'<artifactId>(.*?)</artifactId>', match)
                version_match = re.search(r'<version>(.*?)</version>', match)
                
                if group_match and artifact_match:
                    dep_name = f"{group_match.group(1)}:{artifact_match.group(1)}"
                    version = version_match.group(1) if version_match else ""
                    dependencies[dep_name] = version
            
            return {
                "dependencies": dependencies,
                "dev_dependencies": {}
            }
        except Exception:
            return {"error": "Failed to parse pom.xml"}
    
    def _parse_gradle(self, file_path: Path) -> Dict[str, Any]:
        """Parse build.gradle file (basic parsing)"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            dependencies = {}
            dev_dependencies = {}
            
            # Look for implementation/compile dependencies
            lines = content.split('\n')
            for line in lines:
                line = line.strip()
                if any(line.startswith(dep_type) for dep_type in ['implementation', 'compile', 'api']):
                    # Extract dependency string
                    import re
                    match = re.search(r'["\']([^"\']+)["\']', line)
                    if match:
                        dep_string = match.group(1)
                        dependencies[dep_string] = ""
                elif any(line.startswith(dep_type) for dep_type in ['testImplementation', 'androidTestImplementation']):
                    import re
                    match = re.search(r'["\']([^"\']+)["\']', line)
                    if match:
                        dep_string = match.group(1)
                        dev_dependencies[dep_string] = ""
            
            return {
                "dependencies": dependencies,
                "dev_dependencies": dev_dependencies
            }
        except Exception:
            return {"error": "Failed to parse build.gradle"}


def main():
    logging.info("Universal Project MCP Server starting...")
    mcp = UniversalProjectMCP()
    
    while True:
        try:
            line = sys.stdin.readline()
            if not line:
                logging.info("No input received, exiting")
                break
                
            logging.debug(f"Received: {line.strip()}")
            request = json.loads(line.strip())
            
            method = request.get("method")
            params = request.get("params", {})
            request_id = request.get("id")
            
            logging.info(f"Processing method: {method}")
            
            # Handle MCP protocol methods
            if method == "initialize":
                result = {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {
                        "tools": {}
                    },
                    "serverInfo": {
                        "name": "universal-project-mcp",
                        "version": "2.0.0"
                    }
                }
            elif method == "initialized":
                result = {}
            elif method == "tools/list":
                result = {
                    "tools": [
                        {
                            "name": "set_project_path",
                            "description": "Set the project root path and save it for future use",
                            "inputSchema": {
                                "type": "object",
                                "properties": {
                                    "path": {"type": "string", "description": "Absolute or relative path to project directory"}
                                },
                                "required": ["path"]
                            }
                        },
                        {
                            "name": "get_project_path",
                            "description": "Get the current project root path",
                            "inputSchema": {
                                "type": "object",
                                "properties": {}
                            }
                        },
                        {
                            "name": "get_structure",
                            "description": "Get project directory structure with configurable depth",
                            "inputSchema": {
                                "type": "object",
                                "properties": {
                                    "path": {"type": "string", "description": "Path relative to project root"},
                                    "max_depth": {"type": "integer", "description": "Maximum depth to traverse", "default": 2}
                                }
                            }
                        },
                        {
                            "name": "read_file",
                            "description": "Read file content with optional line range",
                            "inputSchema": {
                                "type": "object",
                                "properties": {
                                    "file_path": {"type": "string", "description": "Path to file relative to project root"},
                                    "start_line": {"type": "integer", "description": "Start line number", "default": 1},
                                    "end_line": {"type": "integer", "description": "End line number"}
                                },
                                "required": ["file_path"]
                            }
                        },
                        {
                            "name": "search_files",
                            "description": "Search for files by pattern and optionally in content",
                            "inputSchema": {
                                "type": "object",
                                "properties": {
                                    "pattern": {"type": "string", "description": "File name pattern (supports wildcards)", "default": "*"},
                                    "path": {"type": "string", "description": "Path to search in"},
                                    "include_content": {"type": "boolean", "description": "Search within file content", "default": False},
                                    "file_extensions": {"type": "array", "items": {"type": "string"}, "description": "Filter by file extensions"},
                                    "max_results": {"type": "integer", "description": "Maximum results to return", "default": 100}
                                }
                            }
                        },
                        {
                            "name": "list_directory",
                            "description": "List directory contents (flat view)",
                            "inputSchema": {
                                "type": "object",
                                "properties": {
                                    "path": {"type": "string", "description": "Directory path relative to project root"}
                                }
                            }
                        },
                        {
                            "name": "get_file_info",
                            "description": "Get detailed file information",
                            "inputSchema": {
                                "type": "object",
                                "properties": {
                                    "file_path": {"type": "string", "description": "Path to file relative to project root"}
                                },
                                "required": ["file_path"]
                            }
                        },
                        {
                            "name": "get_project_summary",
                            "description": "Get comprehensive project overview and analysis",
                            "inputSchema": {
                                "type": "object",
                                "properties": {}
                            }
                        },
                        {
                            "name": "get_dependencies",
                            "description": "Extract and analyze project dependencies from various config files",
                            "inputSchema": {
                                "type": "object",
                                "properties": {}
                            }
                        },
                        {
                            "name": "find_entry_points",
                            "description": "Find main entry points and important files of the application",
                            "inputSchema": {
                                "type": "object",
                                "properties": {}
                            }
                        },
                        {
                            "name": "search_in_files", 
                            "description": "Search for keyword within file contents and return matching files with context",
                            "inputSchema": {
                                "type": "object",
                                "properties": {
                                    "keyword": {"type": "string", "description": "Keyword to search for"},
                                    "path": {"type": "string", "description": "Path to search in (relative to project root)"},
                                    "file_extensions": {"type": "array", "items": {"type": "string"}, "description": "Filter by file extensions (e.g. ['.py', '.js'])"},
                                    "max_results": {"type": "integer", "description": "Maximum number of files to return", "default": 50},
                                    "case_sensitive": {"type": "boolean", "description": "Whether search should be case sensitive", "default": False},
                                    "max_matches_per_file": {"type": "integer", "description": "Maximum matches to show per file", "default": 10}
                                },
                                "required": ["keyword"]
                            }
                        },
                    ]
                }
            elif method == "tools/call":
                tool_name = params.get("name")
                arguments = params.get("arguments", {})
                
                # Route to methods
                if tool_name == "set_project_path":
                    tool_result = mcp.set_project_path(**arguments)
                elif tool_name == "get_project_path":
                    tool_result = mcp.get_project_path(**arguments)
                elif tool_name == "get_structure":
                    tool_result = mcp.get_structure(**arguments)
                elif tool_name == "read_file":
                    tool_result = mcp.read_file(**arguments)
                elif tool_name == "search_files":
                    tool_result = mcp.search_files(**arguments)
                elif tool_name == "search_in_files":
                    tool_result = mcp.search_in_files(**arguments)
                elif tool_name == "list_directory":
                    tool_result = mcp.list_directory(**arguments)
                elif tool_name == "get_file_info":
                    tool_result = mcp.get_file_info(**arguments)
                elif tool_name == "get_project_summary":
                    tool_result = mcp.get_project_summary(**arguments)
                elif tool_name == "get_dependencies":
                    tool_result = mcp.get_dependencies(**arguments)
                elif tool_name == "find_entry_points":
                    tool_result = mcp.find_entry_points(**arguments)
                else:
                    tool_result = {"error": f"Unknown tool: {tool_name}"}
                
                # Format result for MCP
                result = {
                    "content": [
                        {
                            "type": "text",
                            "text": json.dumps(tool_result, indent=2)
                        }
                    ]
                }
            else:
                result = {"error": f"Unknown method: {method}"}
            
            # Send response
            response = {
                "jsonrpc": "2.0",
                "id": request_id,
                "result": result
            }
            
            response_json = json.dumps(response)
            logging.debug(f"Sending response: {response_json}")
            
            print(response_json)
            sys.stdout.flush()
            
        except json.JSONDecodeError as e:
            logging.error(f"JSON decode error: {e}")
            continue
        except Exception as e:
            logging.error(f"Error processing request: {e}")
            error_response = {
                "jsonrpc": "2.0",
                "id": request.get("id") if 'request' in locals() else None,
                "error": {"code": -1, "message": str(e)}
            }
            print(json.dumps(error_response))
            sys.stdout.flush()

if __name__ == "__main__":
    main()