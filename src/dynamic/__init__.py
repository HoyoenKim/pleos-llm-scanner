"""Dynamic verification module — LangGraph state machine + Frida hook driver.

Future Work D (2026-05-14): deterministic state transitions only. LLM analysis
is preserved as an external Claude Code session, *not* invoked from within the
state graph (environment policy: no Anthropic SDK code).
"""
