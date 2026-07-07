import ast
from pathlib import Path


def test_authenticate_workday_tool_does_not_accept_user_id_argument():
    tree = ast.parse(Path("src/server.py").read_text())
    funcs = [node for node in ast.walk(tree) if isinstance(node, ast.AsyncFunctionDef) and node.name == "authenticate_workday"]
    assert funcs, "authenticate_workday tool must exist"
    assert [arg.arg for arg in funcs[0].args.args] == []


def test_no_user_id_parameter_in_tool_implementation():
    tree = ast.parse(Path("src/tools/auth_tools.py").read_text())
    funcs = [node for node in ast.walk(tree) if isinstance(node, ast.AsyncFunctionDef) and node.name == "authenticate_workday"]
    assert funcs
    assert "user_id" not in [arg.arg for arg in funcs[0].args.args]
