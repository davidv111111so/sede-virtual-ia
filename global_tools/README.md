# Global Tools Directory

This directory contains reusable tools, skills, MCP configurations, and project templates for all your projects.

## Structure

### `skills/` - Reusable code templates and utilities

- **`frontend/`** - React, TypeScript, Tailwind CSS components and utilities
- **`backend/`** - Python APIs, database models, authentication
- **`deployment/`** - Netlify configs, Docker files, CI/CD scripts
- **`project_templates/`** - Starter templates for each project type

### `mcps/` - Model Context Protocol configurations

- **`installed/`** - Configuration for pre-installed MCP servers
- **`custom/`** - Custom MCP servers for specific needs
- **`configuration/`** - Claude Desktop/Hermes configuration files

### `documentation/` - Usage guides and checklists

- **`skill_usage_guides/`** - How to use each skill
- **`mcp_integration_guides/`** - MCP setup and integration
- **`project_setup_checklists/`** - Step-by-step project setup

## Quick Start

1. **Copy skills** to your project: `cp -r global_tools/skills/frontend/react_components src/components`
2. **Configure MCPs**: Copy configuration files to `~/.hermes/`
3. **Use templates**: Start new projects from `project_templates/`

## MCP Servers Installed

1. **Filesystem MCP** - File operations
2. **Git MCP** - Version control
3. **SQLite MCP** - Database operations
4. **Web Search MCP** - Research and information
5. **Browser Automation MCP** - Web testing and automation
6. **Supabase MCP** (custom) - Supabase database operations
7. **Netlify MCP** (custom) - Deployment management

## Project Types Supported

- Remodeling websites
- Chatbots (multiple types)
- Audio enhancement applications
- Furnished apartment rental websites
- Botas rental websites

## Maintenance

- Update skills when patterns change
- Add new MCPs as needed
- Keep documentation current
- Test templates regularly
