"""CLI for the AST service."""
import argparse
import json
from . import parse_code


def main():
    parser = argparse.ArgumentParser(description="Parse code to AST JSON")
    parser.add_argument("--language", "-l", default="python", help="Language to parse (default: python)")
    parser.add_argument("--file", "-f", help="Path to source file; if omitted reads stdin")
    args = parser.parse_args()

    if args.file:
        with open(args.file, "r", encoding="utf-8") as fh:
            code = fh.read()
    else:
        import sys

        code = sys.stdin.read()

    ast_obj = parse_code(code, args.language)
    print(json.dumps(ast_obj, indent=2))


if __name__ == "__main__":
    main()
