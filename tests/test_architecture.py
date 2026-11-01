"""Enforce actual dependency direction without introducing a framework."""

import ast

from rulereplay.config import ROOT


def test_authority_modules_have_no_provider_or_execution_dependency():
    permitted = {
        "oracle": {"domain"},
        "classify": {"domain"},
        "domain": set(),
        "integrity": set(),
    }
    for module, allowed in permitted.items():
        tree = ast.parse((ROOT / f"backend/rulereplay/{module}.py").read_text())
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom) and (node.module or "").startswith("rulereplay."):
                assert node.module.split(".")[1] in allowed
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
                assert node.func.id not in {"eval", "exec", "__import__"}


def test_no_package_import_cycles():
    graph = {}
    for file in (ROOT / "backend/rulereplay").glob("*.py"):
        graph[file.stem] = {
            node.module.split(".")[1]
            for node in ast.walk(ast.parse(file.read_text()))
            if isinstance(node, ast.ImportFrom) and (node.module or "").startswith("rulereplay.")
        }

    def visit(module, active):
        assert module not in active, f"Import cycle at {module}"
        for dependency in graph.get(module, set()):
            visit(dependency, active | {module})

    for module in graph:
        visit(module, set())


def test_execution_adapter_cannot_select_policies():
    code = (ROOT / "backend/rulereplay/execution.py").read_text()
    tree = ast.parse(code)
    imports = [n.module for n in ast.walk(tree) if isinstance(n, ast.ImportFrom)]
    assert not any(
        m in {"rulereplay.policies", "rulereplay.oracle", "rulereplay.classify"} for m in imports
    )
    assert "PolicySet" not in code
