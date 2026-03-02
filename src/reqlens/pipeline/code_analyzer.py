"""Static Python code analyzer using AST."""

from __future__ import annotations

import ast
from pathlib import Path

from reqlens.exceptions import StageExecutionError
from reqlens.models.schemas import CodeElement

_COMPLEXITY_NODES = (
    ast.If,
    ast.For,
    ast.AsyncFor,
    ast.While,
    ast.Try,
    ast.With,
    ast.BoolOp,
    ast.IfExp,
)


class _ElementVisitor(ast.NodeVisitor):
    def __init__(self, file_path: str, rel_path: str):
        self.file_path = file_path
        self.rel_path = rel_path
        self.class_stack: list[str] = []
        self.elements: list[CodeElement] = []

    def visit_ClassDef(self, node: ast.ClassDef) -> None:
        qualified = ".".join(self.class_stack + [node.name])
        element_id = f"{self.rel_path}:{qualified}"
        self.elements.append(
            CodeElement(
                id=element_id,
                file_path=self.file_path,
                symbol_type="class",
                qualified_name=qualified,
                signature=f"class {node.name}",
                complexity=_compute_complexity(node),
            )
        )
        self.class_stack.append(node.name)
        self.generic_visit(node)
        self.class_stack.pop()

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        self._handle_function(node)

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:
        self._handle_function(node)

    def _handle_function(self, node: ast.FunctionDef | ast.AsyncFunctionDef) -> None:
        if self.class_stack:
            qualified = ".".join(self.class_stack + [node.name])
            symbol_type = "method"
        else:
            qualified = node.name
            symbol_type = "function"
        element_id = f"{self.rel_path}:{qualified}"
        args = [arg.arg for arg in node.args.args]
        signature = f"{node.name}({', '.join(args)})"
        self.elements.append(
            CodeElement(
                id=element_id,
                file_path=self.file_path,
                symbol_type=symbol_type,
                qualified_name=qualified,
                signature=signature,
                complexity=_compute_complexity(node),
            )
        )
        self.generic_visit(node)


def analyze_code(code_dir: str | Path) -> list[CodeElement]:
    root = Path(code_dir)
    if not root.exists() or not root.is_dir():
        raise StageExecutionError("code_analyzer", f"Code directory not found: {root}")

    elements: list[CodeElement] = []
    py_files = sorted(path for path in root.rglob("*.py") if "/tests/" not in str(path).replace("\\", "/"))
    if not py_files:
        raise StageExecutionError("code_analyzer", f"No Python files found under {root}")

    for py_file in py_files:
        try:
            source = py_file.read_text(encoding="utf-8")
            tree = ast.parse(source)
            rel_path = str(py_file.relative_to(root))
            visitor = _ElementVisitor(str(py_file.resolve()), rel_path)
            visitor.visit(tree)
            elements.extend(visitor.elements)
        except Exception as exc:
            raise StageExecutionError("code_analyzer", f"Failed parsing {py_file}: {exc}") from exc

    return elements


def _compute_complexity(node: ast.AST) -> int:
    return 1 + sum(1 for n in ast.walk(node) if isinstance(n, _COMPLEXITY_NODES))
