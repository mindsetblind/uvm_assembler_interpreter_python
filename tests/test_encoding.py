"""Побайтовые проверки машинного представления варианта 29."""

import unittest

from uvm.assembler import (
    encode_instruction,
    encode_program,
    format_bytes,
    parse_program,
)


class EncodingTests(unittest.TestCase):
    """Точные последовательности PDF и границы битовых полей."""

    def test_specification_bytes(self):
        """Все команды дают последовательности из спецификации."""
        cases = (
            ("push(439)", "e6 6d 00 00 00"),
            ("push(mem[pop() + 201])", "7f 32 00 00 00"),
            ("mem[pop()] = pop()", "3e 00 00 00 00"),
            ("mem[782] = pow(pop(), pop())", "8e c3 00 00 00"),
        )
        for source, expected in cases:
            with self.subTest(source=source):
                instruction = parse_program(source)[0]
                self.assertEqual(
                    encode_instruction(instruction), bytes.fromhex(expected),
                )

    def test_highest_field_values(self):
        """Старшие биты B сохранены, неиспользуемые биты равны нулю."""
        cases = (
            ("push(67108863)", "e6 ff ff ff 00"),
            ("push(mem[pop() + 8191])", "ff ff 07 00 00"),
            ("mem[2147483647] = pow(pop(), pop())", "ce ff ff ff 1f"),
        )
        for source, expected in cases:
            with self.subTest(source=source):
                self.assertEqual(
                    encode_program(parse_program(source)),
                    bytes.fromhex(expected),
                )

    def test_zero_operands(self):
        """Нулевые операнды не изменяют шестибитовые коды операций."""
        source = (
            "push(0)\npush(mem[pop()])\n"
            "mem[pop()] = pop()\nmem[0] = pow(pop(), pop())"
        )
        self.assertEqual(
            encode_program(parse_program(source)),
            bytes.fromhex(
                "26 00 00 00 00 3f 00 00 00 00 "
                "3e 00 00 00 00 0e 00 00 00 00"
            ),
        )

    def test_command_order(self):
        """Команды идут подряд без заголовка, разделителей и пропусков."""
        source = "push(1)\npush(2)\nmem[pop()] = pop()"
        self.assertEqual(
            encode_program(parse_program(source)),
            bytes.fromhex("66 00 00 00 00 a6 00 00 00 00 3e 00 00 00 00"),
        )

    def test_empty_program(self):
        """Пустой список команд даёт пустые машинный код и его вывод."""
        self.assertEqual(encode_program([]), b"")
        self.assertEqual(format_bytes(b""), "")
