"""Tools the helper agent can use."""
import ast
import datetime
import operator
import os

from langchain_core.tools import tool


def now():
    # The container shares the Pi's /etc/localtime, so this is the Pi's own time zone
    return datetime.datetime.now().astimezone()


@tool
def get_time() -> str:
    """Get the current local time."""
    return now().strftime("%I:%M %p").lstrip("0")


@tool
def get_date() -> str:
    """Get today's date and day of the week."""
    return now().strftime("%A, %d %B %Y")


_OPS = {
    ast.Add: operator.add, ast.Sub: operator.sub, ast.Mult: operator.mul,
    ast.Div: operator.truediv, ast.Pow: operator.pow, ast.Mod: operator.mod, ast.USub: operator.neg,
}


def _eval(node):
    if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
        return node.value
    if isinstance(node, ast.BinOp) and type(node.op) in _OPS:
        return _OPS[type(node.op)](_eval(node.left), _eval(node.right))
    if isinstance(node, ast.UnaryOp) and type(node.op) in _OPS:
        return _OPS[type(node.op)](_eval(node.operand))
    raise ValueError("unsupported")


@tool
def calculate(expression: str) -> str:
    """Do arithmetic. The expression uses + - * / ** % and numbers, for example "12*7"."""
    try:
        result = _eval(ast.parse(expression, mode="eval").body)
        return str(round(result, 4))
    except Exception:
        return "I could not work that out."


@tool
def body_status() -> str:
    """How Bolt's body (the Raspberry Pi) is doing: CPU temperature, uptime and load."""
    parts = []
    try:
        with open("/sys/class/thermal/thermal_zone0/temp") as f:
            parts.append(f"CPU temperature {int(f.read()) / 1000:.0f} degrees C")
    except OSError:
        pass
    try:
        with open("/proc/uptime") as f:
            hours = float(f.read().split()[0]) / 3600
            parts.append(f"awake for {hours:.0f} hours")
    except OSError:
        pass
    if hasattr(os, "getloadavg"):
        parts.append(f"load {os.getloadavg()[0]:.1f} on 4 cores")
    return ", ".join(parts)


ALL_TOOLS = [get_time, get_date, calculate, body_status]
