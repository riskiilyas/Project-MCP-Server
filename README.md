# Universal Project MCP Server

A simple MCP server that lets Claude connect to your entire project without context limitations. Claude can explore your whole codebase structure and read any files it needs, but won't modify anything.

## Why This Exists

The main purpose is to give Claude full access to understand your project structure without hitting context limits. Instead of copying/pasting code snippets, Claude can:

- See your entire project structure at once
- Read any file it needs to understand your code
- Search through multiple files to find what it's looking for
- Get the complete picture of how your project is organized

## What Happened to File Editing?

I originally tried adding full CRUD operations (create, edit, delete files) and command execution, but it wasn't really effective. Claude would make unexpected changes or run commands I didn't intend. So I removed all the file modification and command execution features.

Now it's read-only, which works much better - Claude can understand everything but you stay in control of actually making changes.

## Available Methods

### Project Setup
- `set_project_path(path)` - Point to your project directory
- `get_project_path()` - See current project path

### Exploring Your Project
- `get_structure(path, max_depth)` - Get the whole directory tree
- `list_directory(path)` - List files in a specific folder
- `read_file(file_path, start_line, end_line)` - Read any file (with optional line range)
- `get_file_info(file_path)` - Get file details and stats

### Finding Stuff
- `search_files(pattern, path, include_content, file_extensions, max_results)` - Search for files by name or content

## How to Use It

1. **Set your project once**: Tell Claude where your project is located
2. **Let Claude explore**: It can see your entire structure and read whatever files it needs
3. **Get better help**: Claude understands your full codebase context instead of just snippets
4. **You implement changes**: Claude gives suggestions, you make the actual changes

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

## Example Usage

```
You: "Set my project to D:\MyFlutterApp"
Claude: "✓ Project set to D:\MyFlutterApp"

You: "What's the structure of this project?"
Claude: *reads entire project structure*
"This is a Flutter project with lib/screens/, lib/models/, etc..."

You: "Find all files that handle user authentication"
Claude: *searches through files*
"I found authentication logic in lib/services/auth_service.dart, lib/screens/login_screen.dart..."

You: "Show me the login function"
Claude: *reads the specific file*
"Here's the login function from auth_service.dart: ..."
```

The key benefit: Claude sees your ENTIRE project context, not just the small pieces you paste to it.

---
