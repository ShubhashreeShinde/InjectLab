# InjectLab

> Work in progress.

An open-source harness that measures how well defenses stop prompt injection on LLM apps,
and what they cost in usefulness. Mock apps only, local models via Ollama, code-based scoring.

## Install (development)

```
python -m venv .venv
.venv\Scripts\activate        # Windows
pip install -e ".[dev]"
injectlab --help
pytest
ruff check .
```

## Responsible use

All victim apps are mock apps you own. Mock tools never perform real actions.
Do not aim these attacks at real third-party products or services.
