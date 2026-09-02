"""Vercel entry point.

Vercel builds every top-level .py file under /api as its own function, which
would try to build the rule modules as endpoints. vercel.json pins the function
set to this file alone; everything else is an ordinary importable package.
"""

from api.app.main import app

__all__ = ["app"]
