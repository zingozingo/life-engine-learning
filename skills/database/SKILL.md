---
name: database
description: Query and manage database records
status: planned
---

# Database Skill

You can interact with databases using call_mcp_tool with server='database'.

## Available Operations

- **query**: Run a SQL query - args: {sql: string}
- **insert**: Insert a record - args: {table: string, data: dict}
- **update**: Update records - args: {table: string, where: dict, data: dict}
- **delete**: Delete records - args: {table: string, where: dict}
- **list_tables**: List all tables - args: {}
- **describe_table**: Get table schema - args: {table: string}

## Example

call_mcp_tool(server='database', tool_name='query', arguments={'sql': 'SELECT * FROM users LIMIT 10'})
