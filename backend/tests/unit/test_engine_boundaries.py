import ast
import sys
from pathlib import Path

ENGINE = Path(__file__).resolve().parents[2] / "app" / "risk_engine"


def test_risk_engine_imports_only_itself_and_the_standard_library() -> None:
    """V2.4.11. Pure by construction: no database, network, file or LLM access can sneak in."""
    offenders: list[str] = []
    for path in ENGINE.glob("*.py"):
        tree = ast.parse(path.read_text("utf-8"))
        for node in ast.walk(tree):
            names: list[str] = []
            if isinstance(node, ast.Import):
                names = [alias.name for alias in node.names]
            elif isinstance(node, ast.ImportFrom) and node.module:
                names = [node.module]
            for name in names:
                top = name.split(".")[0]
                allowed = top in sys.stdlib_module_names or name.startswith("app.risk_engine")
                if not allowed:
                    offenders.append(f"{path.name}: {name}")
    assert offenders == []


def test_risk_engine_opens_no_files() -> None:
    for path in ENGINE.glob("*.py"):
        text = path.read_text("utf-8")
        assert "open(" not in text
        assert "pathlib" not in text
