# Universal Project MCP Server

A simple MCP server that lets Claude connect to your entire project without context limitations. Claude can explore your whole codebase structure and read any files it needs, but won't modify anything.

## Why This Exists

The main purpose is to give Claude full access to understand your project structure without hitting context limits. In other words, use claude as efficient as possible. Instead of copying/pasting code snippets, Claude can:

- See your entire project structure at once
- Read any file it needs to understand your code
- Search through multiple files to find what it's looking for
- Search the files that contains specific keywords
- Get the complete picture of how your project is organized
- Instantly analyze project type, dependencies, and key files

## What Happened to File Editing?

I originally tried adding full CRUD operations (create, edit, delete files) and command execution, but it wasn't really effective. Claude would make unexpected changes or run commands I didn't intend. So I removed all the file modification and command execution features.

Now it's read-only, which works much better - Claude can understand everything but you stay in control of actually making changes.

## Available Methods

### Project Setup
- `set_project_path(path)` - Point to your project directory
- `get_project_path()` - See current project path

### Smart Project Analysis
- `get_project_summary()` - Get complete project overview (type, README files, stats, complexity)
- `get_dependencies()` - Analyze all project dependencies from config files
- `find_entry_points()` - Find main files, configs, routes, and other important files

### Exploring Your Project
- `get_structure(path, max_depth)` - Get the whole directory tree
- `list_directory(path)` - List files in a specific folder
- `read_file(file_path, start_line, end_line)` - Read any file (with optional line range)
- `get_file_info(file_path)` - Get file details and stats

### Finding Stuff
- `search_files(pattern, path, include_content, file_extensions, max_results)` - Search for files by name or content

## How to Use It

1. **Set your project once**: Tell Claude where your project is located
2. **Let Claude analyze instantly**: New smart methods give Claude immediate project understanding
3. **Get targeted help**: Claude focuses on the right files and understands your tech stack
4. **You implement changes**: Claude gives precise suggestions based on full context

## Installation

```bash
cd coding-mcp-server
uv sync
```

## Claude Configuration

Add this to your Claude desktop app configuration:

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

## Example Usage - Before and After
```
You: "Set my project to D:\MyFlutterApp"
Claude: *calls get_project_summary()*
"✓ This is a Flutter project with 156 files, medium complexity. 
Found README.md at root. Main directories: lib/, android/, ios/"

Claude: *calls get_dependencies()*  
"Uses 23 dependencies including http, provider, flutter_bloc"

Claude: *calls find_entry_points()*
"Main entry: lib/main.dart, Config: pubspec.yaml"

Claude: *reads README.md*
"I can see this is an e-commerce app with user authentication..."

Result: Claude understands your entire project in seconds!
```

## Key Benefits

- **No Context Limits**: Claude sees your whole project without token restrictions
- **Instant Analysis**: New methods give immediate project understanding
- **Smart Focus**: Claude knows which files are important to read
- **Tech Stack Aware**: Understands your dependencies and project type
- **Documentation Aware**: Finds and reads your README/docs automatically
- **Safe & Read-Only**: No accidental file changes or command execution

---