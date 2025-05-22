#!/usr/bin/env python3
import json
import os
import sys
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional
import mimetypes
import subprocess

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

    def execute_command(self, command: str, cwd: str = "", timeout: int = 30) -> Dict[str, Any]:
        """Execute shell command safely with comprehensive tool support"""
        try:
            work_dir = self.project_root / cwd if cwd else self.project_root
            
            # Comprehensive safe commands untuk berbagai development stacks
            safe_commands = {
                # System commands (Still Unstable for Claude)
                # 'ls', 'dir', 'pwd', 'cd', 'mkdir', 'rmdir', 'rm', 'cp', 'mv', 'cat', 'head', 'tail', 
                # 'wc', 'find', 'grep', 'which', 'where', 'echo', 'type', 'tree', 'sort', 'uniq',
                
                # Package managers
                'npm', 'yarn', 'pnpm', 'bun', 'npx', 'pip', 'pip3', 'pipenv', 'poetry', 
                'conda', 'mamba', 'uv', 'composer', 'brew', 'apt', 'yum', 'dnf', 'pacman',
                'choco', 'winget', 'scoop',
                
                # Version control
                'git', 'svn', 'hg', 'bzr',
                
                # Node.js & JavaScript/TypeScript
                'node', 'nodejs', 'deno', 'bun', 'tsx', 'ts-node', 'tsc', 'eslint', 'prettier',
                'webpack', 'vite', 'rollup', 'parcel', 'next', 'nuxt', 'vue', 'angular', 'ng',
                'react', 'create-react-app', 'gatsby', 'svelte', 'sveltekit',
                
                # Flutter & Dart
                'flutter', 'dart', 'pub', 'fvm',
                
                # Android Development
                'adb', 'fastboot', 'gradle', 'gradlew', './gradlew', '.\\gradlew.bat',
                'sdkmanager', 'avdmanager', 'emulator',
                
                # Java & JVM
                'java', 'javac', 'jar', 'mvn', 'gradle', 'sbt', 'kotlin', 'kotlinc',
                'spring', 'quarkus',
                
                # Python
                'python', 'python3', 'py', 'django-admin', 'manage.py', 'flask', 'fastapi',
                'pytest', 'black', 'flake8', 'mypy', 'isort', 'bandit', 'pylint',
                
                # Go
                'go', 'gofmt', 'golint', 'govet', 'godoc', 'goimports',
                
                # Rust
                'cargo', 'rustc', 'rustup', 'rustfmt', 'clippy',
                
                # PHP & Laravel
                'php', 'composer', 'artisan', 'sail', 'laravel', 'symfony', 'wp-cli',
                
                # Ruby
                'ruby', 'gem', 'bundle', 'rails', 'rake', 'rspec',
                
                # .NET & C#
                'dotnet', 'nuget', 'msbuild', 'csc',
                
                # C/C++
                'gcc', 'g++', 'clang', 'clang++', 'make', 'cmake', 'ninja', 'vcpkg', 'conan',
                
                # Database
                'mysql', 'psql', 'sqlite3', 'mongo', 'redis-cli', 'mongosh',
                
                # Cloud & DevOps
                'docker', 'docker-compose', 'kubectl', 'helm', 'terraform', 'ansible',
                'aws', 'az', 'gcloud', 'heroku', 'vercel', 'netlify',
                
                # Build tools & Task runners
                'make', 'cmake', 'ninja', 'bazel', 'buck', 'gulp', 'grunt', 'rollup',
                
                # Testing
                'jest', 'mocha', 'cypress', 'playwright', 'selenium', 'puppeteer',
                
                # Linting & Formatting
                'eslint', 'tslint', 'stylelint', 'prettier', 'black', 'gofmt', 'rustfmt',
                
                # Version managers
                'nvm', 'n', 'fnm', 'pyenv', 'rbenv', 'jenv', 'sdkman',
                
                # Mobile development
                'ionic', 'cordova', 'capacitor', 'expo', 'eas', 'react-native',
                
                # Static site generators
                'hugo', 'jekyll', 'eleventy', 'astro', 'docusaurus',
                
                # API tools
                'curl', 'wget', 'httpie', 'postman', 'insomnia',
                
                # Others
                'code', 'code-insiders', 'subl', 'vim', 'nano', 'emacs',
                'tmux', 'screen', 'ssh', 'scp', 'rsync', 'tar', 'zip', 'unzip',
                'openssl', 'gpg', 'jq', 'yq', 'sed', 'awk'
            }
            
            cmd_parts = command.split()
            if not cmd_parts:
                return {"error": "Empty command"}
                
            # Check if command starts with allowed commands
            base_command = cmd_parts[0]
            
            # Handle path-based commands (like ./gradlew, ./manage.py, etc.)
            if base_command.startswith('./') or base_command.startswith('.\\'):
                # Allow execution of local scripts with common extensions
                allowed_extensions = {'.sh', '.bat', '.cmd', '.py', '.js', '.ts', '.php', '.rb', '.go'}
                script_path = Path(base_command)
                if script_path.suffix.lower() in allowed_extensions:
                    pass  # Allow it
                else:
                    return {"error": f"Local script not allowed: {base_command}"}
            elif base_command not in safe_commands:
                return {"error": f"Command not allowed: {base_command}"}
            
            # Special handling untuk beberapa commands
            if base_command in ['rm', 'del', 'rmdir'] and ('*' in command or '..' in command):
                return {"error": "Dangerous file operations not allowed"}
            
            result = subprocess.run(
                command,
                shell=True,
                cwd=work_dir,
                capture_output=True,
                text=True,
                timeout=timeout
            )
            
            return {
                "command": command,
                "cwd": str(work_dir.relative_to(self.project_root)),
                "full_cwd": str(work_dir),
                "return_code": result.returncode,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "success": result.returncode == 0
            }
            
        except subprocess.TimeoutExpired:
            return {"error": f"Command timed out after {timeout} seconds"}
        except Exception as e:
            return {"error": f"Command execution failed: {str(e)}"}

    def init_project(self, project_type: str, project_name: str = "", options: dict = None) -> Dict[str, Any]:
        """Initialize different types of projects"""
        try:
            if options is None:
                options = {}
                
            project_dir = self.project_root / project_name if project_name else self.project_root
            
            init_commands = {
                # Frontend
                'react': f'npx create-react-app {project_name}',
                'nextjs': f'npx create-next-app@latest {project_name}',
                'vue': f'npm create vue@latest {project_name}',
                'angular': f'npx @angular/cli new {project_name}',
                'svelte': f'npm create svelte@latest {project_name}',
                'vite': f'npm create vite@latest {project_name}',
                
                # Mobile
                'flutter': f'flutter create {project_name}',
                'react-native': f'npx react-native init {project_name}',
                'ionic': f'ionic start {project_name}',
                'expo': f'npx create-expo-app {project_name}',
                
                # Backend
                'laravel': f'composer create-project laravel/laravel {project_name}',
                'symfony': f'composer create-project symfony/skeleton {project_name}',
                'django': f'django-admin startproject {project_name}',
                'fastapi': f'uvicorn --reload main:app' if not project_name else None,  # Custom handling needed
                'express': f'npx express-generator {project_name}',
                'nestjs': f'npx @nestjs/cli new {project_name}',
                
                # Desktop
                'electron': f'npx create-electron-app {project_name}',
                'tauri': f'npx create-tauri-app {project_name}',
                
                # Languages
                'go': f'go mod init {project_name}' if project_name else 'go mod init',
                'rust': f'cargo new {project_name}',
                'dotnet': f'dotnet new console -n {project_name}',
                
                # Static sites
                'gatsby': f'npx create-gatsby {project_name}',
                'hugo': f'hugo new site {project_name}',
                'astro': f'npm create astro@latest {project_name}',
            }
            
            if project_type not in init_commands:
                return {"error": f"Unknown project type: {project_type}. Available: {list(init_commands.keys())}"}
            
            command = init_commands[project_type]
            if command is None:
                return {"error": f"Project type {project_type} requires manual setup"}
            
            # Execute initialization command
            result = self.execute_command(command, timeout=120)  # Longer timeout for project init
            
            if result.get('success'):
                # Update project root to new project if created
                if project_name and (self.project_root / project_name).exists():
                    self.set_project_path(str(self.project_root / project_name))
            
            return {
                "project_type": project_type,
                "project_name": project_name,
                "command_used": command,
                "result": result
            }
            
        except Exception as e:
            return {"error": f"Error initializing project: {str(e)}"}


# MCP Server JSON-RPC Handler
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
                        "version": "1.0.0"
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
                            "name": "execute_command",
                            "description": "Execute safe shell commands with comprehensive development tool support",
                            "inputSchema": {
                                "type": "object",
                                "properties": {
                                    "command": {"type": "string", "description": "Command to execute"},
                                    "cwd": {"type": "string", "description": "Working directory relative to project root"},
                                    "timeout": {"type": "integer", "description": "Timeout in seconds", "default": 30}
                                },
                                "required": ["command"]
                            }
                        },
                        {
                            "name": "init_project",
                            "description": "Initialize new project of various types (React, Flutter, Laravel, etc.)",
                            "inputSchema": {
                                "type": "object",
                                "properties": {
                                    "project_type": {
                                        "type": "string", 
                                        "description": "Type of project to initialize",
                                        "enum": ["react", "nextjs", "vue", "angular", "svelte", "vite", "flutter", 
                                                "react-native", "ionic", "expo", "laravel", "symfony", "django", 
                                                "fastapi", "express", "nestjs", "electron", "tauri", "go", "rust", 
                                                "dotnet", "gatsby", "hugo", "astro"]
                                    },
                                    "project_name": {"type": "string", "description": "Name of the project"},
                                    "options": {"type": "object", "description": "Additional options for project initialization"}
                                },
                                "required": ["project_type"]
                            }
                        }
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
                elif tool_name == "list_directory":
                    tool_result = mcp.list_directory(**arguments)
                elif tool_name == "get_file_info":
                    tool_result = mcp.get_file_info(**arguments)
                elif tool_name == "execute_command":
                    tool_result = mcp.execute_command(**arguments)
                elif tool_name == "init_project":
                    tool_result = mcp.init_project(**arguments)
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
