"""Ассемблер УВМ: разбор текста программы во внутреннее представление.

Внутреннее представление программы -- список объектов Instruction,
каждый из которых хранит имя команды и значения полей A и B.
"""

import argparse
import re
import sys
from dataclasses import dataclass

from uvm import spec

NUMBER = r"(0[xX][0-9a-fA-F]+|\d+)"

PATTERNS = (
    (spec.LOAD_CONST, re.compile(rf"push\({NUMBER}\)")),
    (spec.READ_MEM, re.compile(rf"push\(mem\[pop\(\)(?:\+{NUMBER})?\]\)")),
    (spec.WRITE_MEM, re.compile(r"mem\[pop\(\)\]=pop\(\)")),
    (spec.POW, re.compile(rf"mem\[{NUMBER}\]=pow\(pop\(\),pop\(\)\)")),
)


class AssemblyError(Exception):
    """Ошибка разбора исходного текста программы."""

    def __init__(self, line_no, message):
        super().__init__(f"строка {line_no}: {message}")
        self.line_no = line_no


@dataclass(frozen=True)
class Instruction:
    """Одна команда во внутреннем представлении."""

    name: str
    a: int
    b: int | None = None
    line_no: int = 0

    def fields(self):
        """Возвращает поля команды в виде строки 'A=.., B=..'."""
        if self.b is None:
            return f"A={self.a}"
        return f"A={self.a}, B={self.b}"


def parse_number(text):
    """Преобразует десятичный или шестнадцатеричный литерал в число."""
    return int(text, 0)


def normalize(line):
    """Удаляет комментарий, пробелы и завершающую точку с запятой."""
    code = line.split("#", 1)[0]
    code = re.sub(r"\s+", "", code)
    return code.rstrip(";")


def parse_line(code, line_no):
    """Разбирает одну нормализованную строку в Instruction."""
    for command, pattern in PATTERNS:
        match = pattern.fullmatch(code)
        if match is None:
            continue
        b = None
        if command.has_b:
            raw = match.group(1)
            b = parse_number(raw) if raw is not None else 0
            if b > command.b_max:
                raise AssemblyError(
                    line_no,
                    f"значение {b} не помещается в {command.b_bits} бит",
                )
        return Instruction(command.name, command.opcode, b, line_no)
    raise AssemblyError(line_no, f"неизвестная команда '{code}'")


def parse_program(text):
    """Транслирует текст программы в список Instruction."""
    program = []
    for line_no, line in enumerate(text.splitlines(), start=1):
        code = normalize(line)
        if code:
            program.append(parse_line(code, line_no))
    return program


def format_ir(program):
    """Возвращает внутреннее представление в виде строк полей."""
    return "\n".join(
        f"{instr.name:<10} {instr.fields()}" for instr in program
    )


def build_arg_parser():
    """Создаёт парсер аргументов командной строки ассемблера."""
    parser = argparse.ArgumentParser(description="Ассемблер УВМ")
    parser.add_argument("source", help="путь к файлу с текстом программы")
    parser.add_argument("output", help="путь к двоичному файлу-результату")
    parser.add_argument(
        "-t", "--test", action="store_true",
        help="режим тестирования: вывести внутреннее представление",
    )
    return parser


def main(argv=None):
    """Точка входа CLI ассемблера."""
    args = build_arg_parser().parse_args(argv)
    try:
        with open(args.source, encoding="utf-8") as src:
            program = parse_program(src.read())
    except (OSError, AssemblyError) as err:
        print(f"Ошибка: {err}", file=sys.stderr)
        return 1
    if args.test:
        print(format_ir(program))
    return 0


if __name__ == "__main__":
    sys.exit(main())
