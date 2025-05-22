# Universal Project MCP Server

A comprehensive Model Context Protocol (MCP) server that provides extensive project management capabilities with persistent path configuration and advanced file operations.

## Features

### Core Functionality
- **Dynamic Path Management**: Change project root path during runtime with persistent configuration
- **Advanced File Operations**: Complete file lifecycle management including read, write, edit, move, copy, and delete
- **Directory Operations**: Browse, create, and manage directory structures
- **Content Search**: Powerful file and content search capabilities
- **Command Execution**: Safe execution of development tools and shell commands
- **Project Initialization**: Create new projects for 20+ frameworks and technologies
- **Line-Level Editing**: Precise file editing with line-by-line control

### Advanced Capabilities
- **Multi-encoding Support**: Handle files with various text encodings (UTF-8, UTF-16, Latin-1, CP1252)
- **Safe File Operations**: Automatic backup creation before modifications
- **Content Analysis**: File statistics including lines, words, characters, and MIME type detection
- **Pattern Matching**: Advanced file search with wildcards and content filtering
- **Development Tool Integration**: Support for 100+ development tools and package managers

## Complete Method Reference

### Path Management
- `set_project_path(path)` - Set and persist project root directory
- `get_project_path()` - Get current project root path information

### Directory Operations
- `get_structure(path, max_depth)` - Get hierarchical directory structure
- `list_directory(path)` - List directory contents with detailed file information
- `create_directory(dir_path, parents)` - Create directories with parent creation option

### File Reading & Information
- `read_file(file_path, start_line, end_line)` - Read files with optional line range
- `get_file_info(file_path)` - Get comprehensive file metadata and statistics

### File Creation & Writing
- `create_file(file_path, content, encoding, create_dirs)` - Create new files
- `write_file(file_path, content, encoding, create_dirs)` - Write/overwrite file content
- `append_file(file_path, content, encoding, newline_before)` - Append content to files

### Advanced File Editing
- `insert_lines(file_path, line_number, content, encoding)` - Insert content at specific line
- `replace_lines(file_path, start_line, end_line, content, encoding)` - Replace line ranges
- `delete_lines(file_path, start_line, end_line, encoding)` - Delete specific line ranges

### File Management
- `copy_file(source_path, dest_path, create_dirs)` - Copy files or directories
- `move_file(source_path, dest_path, create_dirs)` - Move/rename files or directories  
- `delete_file(file_path, create_backup)` - Delete files with optional backup

### Search & Discovery
- `search_files(pattern, path, include_content, file_extensions, max_results)` - Advanced file search
  - Pattern matching with wildcards
  - Content-based search within files
  - File extension filtering
  - Configurable result limits

### Command Execution
- `execute_command(command, cwd, timeout)` - Execute development commands safely
  - Support for 100+ development tools
  - Working directory specification
  - Timeout protection
  - Comprehensive output capture

### Project Initialization
- `init_project(project_type, project_name, options)` - Initialize new projects
  - **Frontend**: React, Next.js, Vue, Angular, Svelte, Vite
  - **Mobile**: Flutter, React Native, Ionic, Expo
  - **Backend**: Laravel, Symfony, Django, FastAPI, Express, NestJS
  - **Desktop**: Electron, Tauri
  - **Languages**: Go, Rust, .NET/C#
  - **Static Sites**: Gatsby, Hugo, Astro

## Supported Development Tools

### Package Managers
- **Node.js**: npm, yarn, pnpm, bun, npx
- **Python**: pip, pip3, pipenv, poetry, conda, mamba, uv
- **PHP**: composer
- **System**: brew (macOS), apt/yum/dnf/pacman (Linux), choco/winget/scoop (Windows)

### Frameworks & Build Tools
- **Frontend**: webpack, vite, rollup, parcel, next, nuxt, vue, angular, react
- **Mobile**: flutter, dart, ionic, cordova, capacitor, expo, react-native
- **Build Systems**: make, cmake, ninja, bazel, gradle, maven, sbt

### Version Control & DevOps
- **VCS**: git, svn, hg, bzr
- **Containers**: docker, docker-compose
- **Cloud**: kubectl, helm, terraform, ansible, aws, az, gcloud, heroku, vercel, netlify

### Testing & Quality
- **Testing**: jest, mocha, cypress, playwright, selenium, puppeteer, pytest
- **Linting**: eslint, tslint, stylelint, prettier, black, flake8, mypy, golint, clippy

### Languages & Compilers
- **JavaScript/TypeScript**: node, deno, bun, tsc, ts-node
- **Python**: python, python3, django-admin, flask, fastapi
- **Java/JVM**: java, javac, kotlin, mvn, gradle, spring, quarkus
- **Go**: go, gofmt, goimports
- **Rust**: cargo, rustc, rustup, rustfmt
- **C/C++**: gcc, g++, clang, make, cmake
- **.NET**: dotnet, nuget, msbuild
- **PHP**: php, artisan, symfony, wp-cli
- **Ruby**: ruby, gem, bundle, rails, rake

## Use Cases

### 1. Multi-Project Development
Switch seamlessly between different projects without server restarts:

```
User: "Set my project to D:\Flutter_Projects\ecommerce_app"
Assistant: Updates project root and can now access all Flutter project files

User: "Now switch to my React project at C:\WebProjects\portfolio" 
Assistant: Dynamically changes context to React project
```

### 2. Comprehensive Code Analysis
Analyze entire codebases with detailed insights:

```
User: "Analyze this project structure and create documentation"
Assistant: 
1. Maps project hierarchy with get_structure()
2. Reads configuration files (package.json, pubspec.yaml, etc.)
3. Analyzes dependencies and architecture
4. Generates comprehensive documentation
```

### 3. Advanced File Editing
Perform precise file modifications:

```
User: "Add error handling to line 45 in auth.dart"
Assistant: Uses insert_lines() to add try-catch block at exact location

User: "Replace the login function from lines 20-35 with the new implementation"
Assistant: Uses replace_lines() to swap out specific code sections
```

### 4. Project Setup & Scaffolding
Quickly initialize new projects:

```
User: "Create a new Flutter project called 'my_app'"
Assistant: Executes flutter create and sets up complete project structure

User: "Set up a React app with TypeScript"
Assistant: Uses create-react-app with TypeScript template
```

### 5. Development Workflow Automation
Streamline common development tasks:

```
User: "Find all TODO comments in this project"
Assistant: Uses search_files() with content search to locate all TODOs

User: "Run the build command and show me any errors"
Assistant: Executes build command and analyzes output for issues
```

### 6. Code Refactoring & Maintenance
Support large-scale code changes:

```
User: "Find all files importing the old API client"
Assistant: Searches across project for specific import patterns

User: "Update all copyright headers in Python files"
Assistant: Uses replace_lines() to update headers in multiple files
```

### 7. Cross-Platform Development
Handle platform-specific configurations:

```
User: "What platforms does this Flutter app support?"
Assistant: Analyzes platform directories and configuration files

User: "Update Android permissions in the manifest"
Assistant: Locates and modifies android/app/src/main/AndroidManifest.xml
```

### 8. Dependency Management
Track and manage project dependencies:

```
User: "What are the main dependencies in this project?"
Assistant: Reads package.json/pubspec.yaml/requirements.txt and analyzes deps

User: "Add a new dependency and update the lock file" 
Assistant: Modifies configuration and runs package manager commands
```

### 9. Performance & Asset Optimization
Identify optimization opportunities:

```
User: "Find large assets that might slow down the app"
Assistant: Analyzes assets directory and identifies files over size threshold

User: "Show me all image files and their sizes"
Assistant: Lists images with detailed size information for optimization
```

### 10. Team Collaboration & Documentation
Facilitate team development:

```
User: "Generate a setup guide for new developers"
Assistant: Creates comprehensive setup documentation based on project analysis

User: "What has changed in the authentication module?"
Assistant: Analyzes auth-related files and explains recent modifications
```

## Installation

```bash
cd coding-mcp-server
uv sync
```

## Claude Configuration

Add to your Claude desktop configuration:

```json
{
  "mcpServers": {
    "universal-project": {
      "command": "uv",
      "args": ["run", "python", "D:\\path\\to\\your\\coding-mcp-server\\server_mcp.py"],
      "cwd": "D:\\path\\to\\your\\coding-mcp-server"
    }
  }
}
```

## Key Advantages

### Technical Capabilities
- **Comprehensive File Operations**: Complete CRUD operations with advanced editing features
- **Safe Command Execution**: Whitelist-based security with timeout protection  
- **Multi-encoding Support**: Handle diverse file formats and encodings
- **Persistent Configuration**: Remember settings between sessions
- **Atomic Operations**: Backup creation before destructive operations

### Developer Experience
- **Context Awareness**: Full understanding of project structure and dependencies
- **Dynamic Flexibility**: Switch between projects seamlessly during conversations
- **Natural Language Interface**: Configure everything through conversational commands
- **Language Agnostic**: Works with any programming language or framework
- **Rich Feedback**: Detailed operation results and error reporting

### Safety & Reliability
- **Automatic Backups**: Files backed up before modifications
- **Command Whitelisting**: Only safe development commands allowed
- **Path Validation**: Ensures operations stay within project boundaries
- **Error Handling**: Comprehensive error reporting with recovery suggestions
- **Resource Limits**: File size and operation timeouts prevent abuse

This MCP server transforms project management from manual file operations into intelligent, context-aware development assistance that understands your codebase and helps you work more efficiently.
