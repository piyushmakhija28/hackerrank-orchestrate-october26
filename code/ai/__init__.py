"""AI Optimization, Context Engineering and Anti-Hallucination Subsystem.

Conforms strictly to Level 2.2 Docstrings-Only convention (no inline narration).
Coordinates subword BPE token budgeting, causal context building, and witness-grounded prompt guards.
"""

from code.ai.token_optimizer import TokenOptimizer
from code.ai.context_builder import ContextBuilder
from code.ai.prompt_guard import PromptGuard

__all__ = [
    "TokenOptimizer",
    "ContextBuilder",
    "PromptGuard",
]
