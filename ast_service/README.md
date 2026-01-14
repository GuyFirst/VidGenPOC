# ast_service

Small, extensible AST parsing service.

Usage examples:

- As a module:

```py
from ast_service import parse_code
ast_dict = parse_code("def foo():\n    return 1", "python")
```

- CLI (compact AST by default):

```sh
python -m ast_service --file path/to/code.py
```

Extending with new languages:

- Implement a class following `base.Parser` and register it via `registry.register("lang", parser_instance)`.
