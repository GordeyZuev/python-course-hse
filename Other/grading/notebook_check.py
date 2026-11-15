"""Check one function from a submitted Big HW notebook inside the grader container."""
import ast
import json
import re
import sys
from pathlib import Path

import numpy as np


def solution_namespace(path):
    notebook = json.loads(open(path, encoding='utf-8').read())
    if not isinstance(notebook, dict) or not isinstance(notebook.get('cells'), list):
        raise ValueError('Invalid notebook')
    namespace = {'np': np}
    for cell in notebook['cells']:
        if cell.get('cell_type') != 'code':
            continue
        source = cell.get('source', [])
        if not isinstance(source, (str, list)):
            raise ValueError('Invalid code cell')
        source = ''.join(source)
        if not re.search(r'(?m)^\s*(?:async\s+)?def\s+[A-Za-z_]\w*\s*\(',source):
            continue
        tree = ast.parse(source)
        # Skip notebook experiments; preserve helper definitions and constants.
        nodes = [node for node in tree.body if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.Import, ast.ImportFrom, ast.ClassDef, ast.Assign, ast.AnnAssign))]
        exec(compile(ast.Module(body=nodes, type_ignores=[]), path, 'exec'), namespace)
    return namespace


def main():
    filename, function = sys.argv[1:]
    sys.path.insert(0, str(Path(filename).resolve().parent))
    from Other.grading_checks import check_task
    namespace = solution_namespace(filename)
    result=check_task(function, namespace.get(function), verbose=False)
    if not result['passed']:
        print(result['message'],file=sys.stderr)
        raise SystemExit(1)


if __name__ == '__main__':
    main()
