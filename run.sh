#!/bin/sh
# Запуск инструментов УВМ.
#   ./run.sh asm <source.asm> <output.bin> [--test]
#   ./run.sh test
set -e
ROOT="$(cd "$(dirname "$0")" && pwd)"
export PYTHONPATH="$ROOT/src"
cmd="$1"
[ $# -gt 0 ] && shift
case "$cmd" in
    asm)  exec python3 -m uvm.assembler "$@" ;;
    test) exec python3 -m unittest discover -s "$ROOT/tests" -t "$ROOT" -v ;;
    *)    echo "usage: $0 {asm|test} [args...]" >&2; exit 2 ;;
esac
