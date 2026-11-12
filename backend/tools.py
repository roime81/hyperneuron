import ast
import operator as op
from typing import List
from langchain_community.tools import DuckDuckGoSearchResults

_OPERATORS = {ast.Add: op.add, ast.Sub: op.sub, ast.Mult: op.mul, ast.Div: op.truediv, ast.Pow: op.pow, ast.USub: op.neg}

def safe_calculate(expression: str) -> str:
    def _eval(node):
        if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
            return node.value
        if isinstance(node, ast.BinOp) and type(node.op) in _OPERATORS:
            return _OPERATORS[type(node.op)](_eval(node.left), _eval(node.right))
        if isinstance(node, ast.UnaryOp) and type(node.op) in _OPERATORS:
            return _OPERATORS[type(node.op)](_eval(node.operand))
        raise ValueError("Unsupported expression")
    try:
        tree = ast.parse(expression.strip(), mode="eval")
        return str(_eval(tree.body))
    except Exception as exc:
        return f"Calculation error: {exc}"

def web_search(queries: List[str], max_results: int = 4) -> str:
    search = DuckDuckGoSearchResults(num_results=max_results)
    compiled = []
    for q in queries[:3]:
        try:
            res = search.invoke(q)
            compiled.append(f"### Query: {q}\n{res}")
        except Exception as exc:
            compiled.append(f"### Query: {q}\nSearch failed: {exc}")
    return "\n\n".join(compiled)
