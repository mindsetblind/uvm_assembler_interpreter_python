"""Спецификация учебной виртуальной машины (УВМ), вариант 29.

Каждая команда занимает 5 байт. Поле A (код операции) занимает
биты 0-5, поле B (если есть) начинается с бита 6.
"""

from dataclasses import dataclass

COMMAND_SIZE = 5
OPCODE_BITS = 6
B_SHIFT = OPCODE_BITS


@dataclass(frozen=True)
class CommandSpec:
    """Описание одной команды УВМ.

    name   -- мнемоническое имя команды во внутреннем представлении;
    opcode -- значение поля A;
    b_bits -- ширина поля B в битах (0, если поля B нет).
    """

    name: str
    opcode: int
    b_bits: int

    @property
    def has_b(self):
        """Возвращает True, если у команды есть поле B."""
        return self.b_bits > 0

    @property
    def b_max(self):
        """Максимально допустимое значение поля B."""
        return (1 << self.b_bits) - 1


LOAD_CONST = CommandSpec("load_const", 38, 26)
READ_MEM = CommandSpec("read_mem", 63, 13)
WRITE_MEM = CommandSpec("write_mem", 62, 0)
POW = CommandSpec("pow", 14, 31)

COMMANDS = (LOAD_CONST, READ_MEM, WRITE_MEM, POW)
BY_NAME = {cmd.name: cmd for cmd in COMMANDS}
BY_OPCODE = {cmd.opcode: cmd for cmd in COMMANDS}
