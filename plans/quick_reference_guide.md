# Quick Reference Guide: Roo Skills & MCPs

## 🚀 Essential Skills Cheat Sheet

### File Operations

```markdown
read_file - Read files with line numbers
write_to_file - Create/overwrite complete files  
apply_diff - Make surgical edits (use SEARCH/REPLACE blocks)
list_files - Explore directories (recursive or top-level)
```

### Code Analysis

```markdown
search_files - Regex search across files with context - Use file_pattern to filter by extension
```

### Project Management

```markdown
update_todo_list - Track progress: [ ], [x], [-]
ask_followup_question - Get clarification with suggestions
attempt_completion - Finalize tasks
```

### Mode Management

```markdown
switch_mode - Change to code/debug/architect/etc.
new_task - Create new task instance
```

## 📋 MCP Quick Reference

### Must-Have MCPs

1. **Filesystem MCP** - File operations
2. **Git MCP** - Version control
3. **SQLite MCP** - Lightweight databases

### Project-Specific MCPs

- **Web Search MCP** - Research for all projects
- **Browser Automation MCP** - Testing web apps
- **Supabase MCP** (custom) - Database operations
- **Netlify MCP** (custom) - Deployment management

## 🎯 When to Use What

### Starting a New Project

1. `list_files` - Explore structure
2. `read_file` - Understand existing code
3. `update_todo_list` - Plan tasks

### Writing Code

1. `write_to_file` - Create new files
2. `apply_diff` - Edit existing files
3. `search_files` - Find references

### Debugging

1. `read_file` (indentation mode) - See complete functions
2. `search_files` - Find error patterns
3. Switch to **Debug mode** for systematic troubleshooting

### Deployment

1. Use **Netlify MCP** for deployments
2. `write_to_file` for config files
3. `update_todo_list` to track deployment steps

## 🔧 Common Workflows

### React Component Creation

```
1. write_to_file - Create component.tsx
2. write_to_file - Create component.module.css
3. apply_diff - Add to parent component
4. update_todo_list - Mark as complete
```

### Python API Endpoint

```
1. read_file - Check existing endpoints
2. apply_diff - Add new route
3. write_to_file - Create model/schema
4. update_todo_list - Track progress
```

### Database Migration

```
1. Use SQLite MCP for local testing
2. write_to_file - Create migration script
3. Use Supabase MCP for production
4. update_todo_list - Track migration steps
```

## ⚡ Pro Tips

1. **Use indentation mode** with `read_file` when you have line numbers
2. **Chain tools** - List files, then read the ones you need
3. **Update todos frequently** - Keep track of complex tasks
4. **Create custom MCPs** for repetitive project tasks
5. **Use the skill tool** for specialized tasks like creating MCP servers

## 📁 Global Tools Structure (Quick View)

```
global_tools/
├── skills/          # Reusable code templates
├── mcps/           # MCP configurations
└── documentation/  # Usage guides
```

## 🆘 Troubleshooting

| Issue                | Solution                                     |
| -------------------- | -------------------------------------------- |
| Can't edit file      | Use `apply_diff` not `write_to_file`         |
| Need to find code    | Use `search_files` with regex                |
| Don't know structure | Use `list_files` recursive                   |
| Complex task         | Break into todos with `update_todo_list`     |
| Need clarification   | Use `ask_followup_question` with suggestions |

## 📞 Mode Selection Guide

- **🏗️ Architect** - Planning, design, strategy
- **💻 Code** - Writing, modifying, refactoring code
- **🪲 Debug** - Troubleshooting, error investigation
- **❓ Ask** - Explanations, documentation, analysis
- **🪃 Orchestrator** - Complex multi-step projects

## 🎮 Quick Start Commands

To switch modes when needed:

```markdown
Use switch_mode with reason: "Need to implement code changes"
```

To create a new task:

```markdown
Use new_task with mode: "code" and clear todos
```

This quick reference should be your go-to guide for daily work with Roo. Keep it handy and update it as you discover new patterns!
