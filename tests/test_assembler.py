"""Тесты этапа 1: перевод программы во внутреннее представление."""

import pathlib
import unittest

from uvm.assembler import AssemblyError, Instruction, parse_program

PROGRAMS = pathlib.Path(__file__).resolve().parent.parent / "programs"


class SpecTests(unittest.TestCase):
    """Проверка соответствия полей тестам из спецификации УВМ."""

    def test_spec_program(self):
        """Программа spec_tests.asm даёт поля из спецификации."""
        text = (PROGRAMS / "spec_tests.asm").read_text(encoding="utf-8")
        fields = [(i.a, i.b) for i in parse_program(text)]
        self.assertEqual(
            fields, [(38, 439), (63, 201), (62, None), (14, 782)]
        )

    def test_load_const(self):
        """push(N) -- загрузка константы."""
        self.assertEqual(
            parse_program("push(439)"),
            [Instruction("load_const", 38, 439, 1)],
        )

    def test_read_without_offset(self):
        """Смещение чтения по умолчанию равно 0."""
        instr = parse_program("push(mem[pop()])")[0]
        self.assertEqual((instr.a, instr.b), (63, 0))

    def test_hex_and_spaces(self):
        """Поддерживаются шестнадцатеричные литералы и пробелы."""
        instr = parse_program("  mem[ 0x30E ] = pow( pop(), pop() ) ;")[0]
        self.assertEqual((instr.a, instr.b), (14, 782))

    def test_comments_and_empty_lines(self):
        """Комментарии и пустые строки пропускаются."""
        program = parse_program("# comment\n\nmem[pop()] = pop() # w\n")
        self.assertEqual(program, [Instruction("write_mem", 62, None, 3)])


class ErrorTests(unittest.TestCase):
    """Проверка диагностики ошибок."""

    def test_unknown_command(self):
        """Неизвестная команда -- ошибка с номером строки."""
        with self.assertRaises(AssemblyError) as ctx:
            parse_program("push(1)\nfoo()")
        self.assertEqual(ctx.exception.line_no, 2)

    def test_field_overflow(self):
        """Смещение чтения ограничено 13 битами."""
        with self.assertRaises(AssemblyError):
            parse_program("push(mem[pop() + 8192])")


if __name__ == "__main__":
    unittest.main()
