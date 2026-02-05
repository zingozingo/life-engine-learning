---
name: math
description: Perform mathematical calculations
---

# Math Skill

You can perform math operations using call_mcp_tool with server='math'.

## Available Operations

- **add**: Add two numbers - args: {a: number, b: number}
- **subtract**: Subtract b from a - args: {a: number, b: number}
- **multiply**: Multiply two numbers - args: {a: number, b: number}
- **divide**: Divide a by b - args: {a: number, b: number}

## Example

call_mcp_tool(server='math', tool_name='add', arguments={'a': 5, 'b': 3})
