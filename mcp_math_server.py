from mcp.server.fastmcp import FastMCP

app = FastMCP("Math Tools")


@app.tool()
def add(a: float, b: float) -> float:
    """Add two numbers together."""
    return a + b


@app.tool()
def multiply(a: float, b: float) -> float:
    """Multiply two numbers together."""
    return a * b


@app.tool()
def subtract(a: float, b: float) -> float:
    """Subtract b from a."""
    return a - b


@app.tool()
def divide(a: float, b: float) -> float:
    """Divide a by b."""
    if b == 0:
        raise ValueError("Cannot divide by zero")
    return a / b


if __name__ == "__main__":
    app.run()
