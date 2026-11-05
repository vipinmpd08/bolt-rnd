"""Tools the helper agent can use."""
import ast
import datetime
import operator
import os
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET

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


COUNTRIES = {"us": "US", "usa": "US", "america": "US", "india": "IN", "uae": "AE", "dubai": "AE",
             "uk": "GB", "britain": "GB", "england": "GB", "australia": "AU", "canada": "CA"}


@tool
def get_news(topic: str = "", country: str = "US") -> str:
    """Latest news headlines from Google News, right now.

    topic: what to search for, e.g. "elections" or "cricket"; leave empty for top stories.
    country: country code or name, e.g. "US", "India", "UAE", "UK".
    """
    gl = COUNTRIES.get(country.strip().lower(), country.strip().upper()[:2] or "US")
    params = {"hl": f"en-{gl}", "gl": gl, "ceid": f"{gl}:en"}
    if topic.strip():
        params["q"] = topic.strip() + " when:1d"
        url = "https://news.google.com/rss/search?" + urllib.parse.urlencode(params)
    else:
        url = "https://news.google.com/rss?" + urllib.parse.urlencode(params)
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (Bolt the dog)"})
        with urllib.request.urlopen(req, timeout=10) as r:
            root = ET.fromstring(r.read())
    except Exception as e:
        return f"Could not fetch the news ({e})."
    titles = [i.findtext("title", "").rsplit(" - ", 1)[0] for i in root.iter("item")][:6]
    return " | ".join(titles) if titles else "No headlines found."


ALL_TOOLS = [get_time, get_date, calculate, body_status, get_news]
