---
name: filesystem
description: Read, write, and manage files on the local system
---

# Filesystem Skill

You can interact with the local filesystem using the call_mcp_tool function.

## Available Operations

- **list_directory**: List contents of a directory
  - args: {path: string}

- **read_file**: Read contents of a file
  - args: {path: string}

- **write_file**: Write content to a file
  - args: {path: string, content: string}

- **create_directory**: Create a new directory
  - args: {path: string}

## How to Use

Call the generic MCP tool like this:
call_mcp_tool(server='filesystem', tool_name='list_directory', arguments={'path': '.'})

## Examples

To list current directory:
call_mcp_tool(server='filesystem', tool_name='list_directory', arguments={'path': '.'})

To read a file:
call_mcp_tool(server='filesystem', tool_name='read_file', arguments={'path': 'main.py'})
