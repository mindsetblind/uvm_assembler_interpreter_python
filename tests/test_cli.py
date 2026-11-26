"""Проверки CLI этапа 2 через реальный скрипт запуска."""

import pathlib
import subprocess
import tempfile
import unittest

ROOT = pathlib.Path(__file__).resolve().parent.parent
EXPECTED_BYTES = bytes.fromhex(
    "e6 6d 00 00 00 7f 32 00 00 00 3e 00 00 00 00 8e c3 00 00 00"
)
EXPECTED_OUTPUT = (
    "Ассемблировано команд: 4\n"
    "0xE6, 0x6D, 0x00, 0x00, 0x00\n"
    "0x7F, 0x32, 0x00, 0x00, 0x00\n"
    "0x3E, 0x00, 0x00, 0x00, 0x00\n"
    "0x8E, 0xC3, 0x00, 0x00, 0x00\n"
)


class CliTests(unittest.TestCase):
    """Контракт CLI: аргументы, бинарный файл и диагностика ошибок."""

    def setUp(self):
        """Создаёт отдельный каталог для каждого запуска."""
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.directory = pathlib.Path(directory.name)
        self.output = self.directory / "out.bin"

    def run_cli(self, *args):
        """Запускает инструменты из каталога вне проекта."""
        return subprocess.run(
            [str(ROOT / "run.sh"), *map(str, args)],
            cwd=self.directory, capture_output=True, text=True,
            encoding="utf-8", check=False,
        )

    def test_specification_output(self):
        """Оба тестовых флага выводят и записывают точные байты PDF."""
        for flag in ("--test", "-t"):
            with self.subTest(flag=flag):
                result = self.run_cli(
                    "asm", ROOT / "programs/spec_tests.asm", self.output,
                    flag,
                )
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertEqual(result.stdout, EXPECTED_OUTPUT)
                self.assertEqual(result.stderr, "")
                self.assertEqual(self.output.read_bytes(), EXPECTED_BYTES)

    def test_normal_mode(self):
        """Без тестового флага создаётся бинарник и выводится число команд."""
        result = self.run_cli(
            "asm", ROOT / "programs/spec_tests.asm", self.output,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout, "Ассемблировано команд: 4\n")
        self.assertEqual(self.output.read_bytes(), EXPECTED_BYTES)

    def test_empty_program(self):
        """Пустая программа даёт пустой файл и ноль команд."""
        source = self.directory / "empty.asm"
        source.write_text("# Только комментарий\n", encoding="utf-8")
        result = self.run_cli("asm", source, self.output, "--test")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout, "Ассемблировано команд: 0\n")
        self.assertEqual(self.output.read_bytes(), b"")

    def test_output_error(self):
        """Ошибка пути результата не выдаётся за успешную сборку."""
        output = self.directory / "missing" / "out.bin"
        result = self.run_cli(
            "asm", ROOT / "programs/spec_tests.asm", output, "--test",
        )
        self.assertEqual(result.returncode, 1)
        self.assertEqual(result.stdout, "")
        self.assertIn("Ошибка:", result.stderr)
        self.assertNotIn("Traceback", result.stderr)

    def test_invalid_source_preserves_output(self):
        """Ошибка исходника не повреждает ранее собранный бинарник."""
        self.output.write_bytes(EXPECTED_BYTES)
        source = self.directory / "invalid.asm"
        source.write_text("foo()", encoding="utf-8")
        result = self.run_cli("asm", source, self.output)
        self.assertEqual(result.returncode, 1)
        self.assertEqual(self.output.read_bytes(), EXPECTED_BYTES)

    def test_invalid_encoding(self):
        """Не-UTF-8 исходник даёт диагностическое сообщение."""
        source = self.directory / "invalid.asm"
        source.write_bytes(b"\xff\xfe")
        result = self.run_cli("asm", source, self.output)
        self.assertEqual(result.returncode, 1)
        self.assertIn("Ошибка:", result.stderr)
        self.assertNotIn("Traceback", result.stderr)
        self.assertFalse(self.output.exists())

    def test_missing_source(self):
        """Отсутствие исходника даёт понятную ошибку без traceback."""
        result = self.run_cli("asm", "missing.asm", self.output, "--test")
        self.assertEqual(result.returncode, 1)
        self.assertIn("Ошибка:", result.stderr)
        self.assertNotIn("Traceback", result.stderr)

    def test_invalid_source(self):
        """Ошибка команды содержит номер строки исходника."""
        source = self.directory / "invalid.asm"
        source.write_text("push(1)\nfoo()\n", encoding="utf-8")
        result = self.run_cli("asm", source, self.output, "--test")
        self.assertEqual(result.returncode, 1)
        self.assertIn("строка 2:", result.stderr)
        self.assertNotIn("Traceback", result.stderr)
        self.assertFalse(self.output.exists())

    def test_oversized_number(self):
        """Слишком длинное число диагностируется без traceback."""
        source = self.directory / "large.asm"
        source.write_text("push(" + "9" * 5000 + ")\n", encoding="utf-8")
        result = self.run_cli("asm", source, self.output, "--test")
        self.assertEqual(result.returncode, 1)
        self.assertIn("строка 1:", result.stderr)
        self.assertNotIn("Traceback", result.stderr)

    def test_missing_arguments(self):
        """Скрипт и ассемблер отклоняют неполный набор аргументов."""
        for args in ((), ("asm",), ("unknown",)):
            with self.subTest(args=args):
                result = self.run_cli(*args)
                self.assertEqual(result.returncode, 2)
                self.assertIn("usage:", result.stderr)
