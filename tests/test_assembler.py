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

    def test_decimal_leading_zeros(self):
        """Десятичные литералы с ведущими нулями не считаются восьмеричными."""
        self.assertEqual(parse_program("push(0439)")[0].b, 439)

    def test_field_boundaries(self):
        """Ноль и максимальные значения всех трёх полей B допустимы."""
        cases = (
            ("push({})", 67_108_863),
            ("push(mem[pop() + {}])", 8191),
            ("mem[{}] = pow(pop(), pop())", 2_147_483_647),
        )
        for template, maximum in cases:
            for value in (0, maximum):
                with self.subTest(template=template, value=value):
                    program = parse_program(template.format(value))
                    self.assertEqual(program[0].b, value)


class ErrorTests(unittest.TestCase):
    """Проверка диагностики ошибок."""

    def test_unknown_command(self):
        """Неизвестная команда -- ошибка с номером строки."""
        with self.assertRaises(AssemblyError) as ctx:
            parse_program("push(1)\nfoo()")
        self.assertEqual(ctx.exception.line_no, 2)

    def test_field_overflow(self):
        """Каждое поле B отвергает значение выше своей верхней границы."""
        for source in (
            "push(67108864)",
            "push(mem[pop() + 8192])",
            "mem[2147483648] = pow(pop(), pop())",
        ):
            with self.subTest(source=source):
                with self.assertRaises(AssemblyError):
                    parse_program(source)

    def test_negative_fields(self):
        """Отрицательные значения не входят в язык ассемблера."""
        for source in (
            "push(-1)", "push(mem[pop() + -1])",
            "mem[-1] = pow(pop(), pop())",
        ):
            with self.subTest(source=source):
                with self.assertRaises(AssemblyError):
                    parse_program(source)


if __name__ == "__main__":
    unittest.main()
