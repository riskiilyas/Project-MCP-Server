# Universal Project MCP Server

A Model Context Protocol (MCP) server that provides dynamic project management capabilities with persistent path configuration.

## Features

- **Dynamic Path Setting**: Change project root path during runtime
- **Persistent Configuration**: Remembers your project path between sessions
- **File Operations**: Read, search, and analyze files
- **Directory Operations**: Browse and list directory contents
- **Command Execution**: Run safe shell commands
- **Project Initialization**: Create new projects of various types
- **No CLI Arguments**: All configuration is done through MCP calls

## Use Cases

### 1. Multi-Project Development
**Scenario**: You're a developer working on multiple projects across different directories.

```
User: "Set my project path to D:\Flutter_Projects\ecommerce_app"
Assistant: Sets the project root and can now access all files within this Flutter project.

User: "Now switch to my React project at C:\WebProjects\my-portfolio"
Assistant: Dynamically changes the project root without restarting the MCP server.
```

**Benefits**: Seamlessly switch between projects without manual configuration or server restarts.

### 2. Project Analysis & Documentation
**Scenario**: You need to understand or document an existing codebase.

```
User: "Analyze this Flutter project structure and create comprehensive documentation"
Assistant: 
1. Uses get_structure() to map the entire project
2. Reads key files like pubspec.yaml, README.md
3. Analyzes features/ directory structure
4. Generates detailed documentation based on actual code

User: "What dependencies does this project use?"
Assistant: Reads pubspec.yaml and provides detailed dependency analysis
```

**Benefits**: Automated project analysis without manual file browsing.

### 3. Code Review & Refactoring
**Scenario**: You're reviewing code quality or planning refactoring.

```
User: "Find all files containing 'TODO' comments"
Assistant: Uses search_files() with content search to locate all TODO items across the project.

User: "Show me the authentication implementation"
Assistant: 
1. Searches for auth-related files
2. Reads authentication modules
3. Provides comprehensive overview of auth flow
```

**Benefits**: Quick code exploration and pattern identification.

### 4. Debugging & Problem Solving
**Scenario**: You're troubleshooting issues in your application.

```
User: "My app is crashing on startup, help me debug"
Assistant:
1. Reads main.dart and related entry points
2. Checks dependency configurations
3. Examines error logs if present
4. Suggests potential fixes based on code analysis

User: "Run flutter doctor to check my setup"
Assistant: Executes command safely and provides environment analysis
```

**Benefits**: Contextual debugging with full project awareness.

### 5. Project Setup & Onboarding
**Scenario**: Setting up a new development environment or onboarding new team members.

```
User: "Help me set up this project for development"
Assistant:
1. Reads setup documentation
2. Checks for configuration files (.env, etc.)
3. Provides step-by-step setup instructions
4. Can execute setup commands if needed

User: "Create a new React project for me"
Assistant: Uses init_project() to scaffold a new React application
```

**Benefits**: Automated setup guidance and project initialization.

### 6. Cross-Platform Development
**Scenario**: Working with Flutter apps that target multiple platforms.

```
User: "What platforms does this app support?"
Assistant:
1. Analyzes platform directories (android/, ios/, web/, etc.)
2. Checks pubspec.yaml for platform-specific dependencies
3. Reviews configuration files for each platform

User: "Show me the Android-specific configuration"
Assistant: Navigates to android/ directory and analyzes Gradle files, manifests, etc.
```

**Benefits**: Platform-specific insights without manual directory browsing.

### 7. API Integration Analysis
**Scenario**: Understanding how external services are integrated.

```
User: "How does this app integrate with Supabase?"
Assistant:
1. Searches for Supabase-related code
2. Reads configuration files
3. Analyzes database models and queries
4. Maps out the integration architecture

User: "Show me all API endpoints used in this project"
Assistant: Searches for HTTP calls, API configurations, and service integrations
```

**Benefits**: Comprehensive integration mapping and analysis.

### 8. Performance Optimization
**Scenario**: Optimizing app performance and identifying bottlenecks.

```
User: "Find large assets and dependencies that might slow down the app"
Assistant:
1. Analyzes assets/ directory for large files
2. Reviews pubspec.yaml for heavy dependencies
3. Checks build configurations
4. Suggests optimization strategies

User: "Show me all image assets and their sizes"
Assistant: Lists all images with file size information for optimization planning
```

**Benefits**: Data-driven performance optimization recommendations.

### 9. Team Collaboration
**Scenario**: Coordinating with team members on shared codebases.

```
User: "What has changed in the authentication module recently?"
Assistant:
1. Analyzes auth-related files
2. Can check Git history if needed
3. Identifies recent modifications
4. Explains impact of changes

User: "Prepare a handover document for the new developer"
Assistant: Generates comprehensive project overview including architecture, setup, and key components
```

**Benefits**: Enhanced team communication and knowledge transfer.

### 10. Continuous Integration Setup
**Scenario**: Setting up CI/CD pipelines and deployment automation.

```
User: "Help me set up GitHub Actions for this Flutter project"
Assistant:
1. Analyzes project structure and requirements
2. Checks existing CI configuration
3. Suggests appropriate workflow configurations
4. Can create or modify CI files

User: "What deployment commands does this project use?"
Assistant: Reads README and configuration files to extract deployment procedures
```

**Benefits**: Automated CI/CD setup based on project analysis.

## Installation

```bash
cd coding-mcp-server
uv sync
```

## Claude Config
```json
{
  "mcpServers": {
    "universal-project": {
      "command": "uv",
      "args": ["run", "python", "D:\\path\\to\\your_project\\server_mcp.py"],
      "cwd": "D:\\path\\to\\your_project\\coding-mcp-server"
    }
  }
}
```

## Key Advantages

1. **Context Awareness**: Full understanding of your project structure and dependencies
2. **Dynamic Flexibility**: Switch between projects seamlessly
3. **Persistent Memory**: Remembers configurations between sessions
4. **Safe Operations**: Controlled command execution with safety restrictions
5. **Language Agnostic**: Works with any programming language or framework
6. **No Manual Setup**: Configure everything through natural language commands

This MCP server transforms how you interact with your development projects, making complex project management tasks as simple as having a conversation.