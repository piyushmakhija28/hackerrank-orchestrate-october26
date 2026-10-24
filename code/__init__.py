"""
Root package for Autonomous AI Deletion Audit Agent.
HackerRank Orchestrate — Ghost Data Still Exists.
Conforms strictly to Level 2.2 Docstrings-Only convention (no inline narration).
"""
import sys
import importlib.util
from pathlib import Path
from typing import Any

_stdlib_code = None

def _load_stdlib_code() -> Any:
    """Dynamically load Python standard library code module to prevent pdb/pytest collision.
    
    Returns:
        Loaded standard library module or None.
    """
    global _stdlib_code
    if _stdlib_code is None:
        stdlib_path = Path(sys.base_prefix) / "Lib" / "code.py"
        if stdlib_path.exists():
            spec = importlib.util.spec_from_file_location("_stdlib_code_module", stdlib_path)
            if spec and spec.loader:
                mod = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(mod)
                _stdlib_code = mod
    return _stdlib_code

def __getattr__(name: str) -> Any:
    """Delegate missing module attributes to Python standard library code module.
    
    Args:
        name: Attribute name requested.
    Returns:
        Standard library attribute if present.
    """
    mod = _load_stdlib_code()
    if mod and hasattr(mod, name):
        return getattr(mod, name)
    raise AttributeError(f"module 'code' has no attribute '{name}'")
