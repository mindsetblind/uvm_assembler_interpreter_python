"""Проверки CLI этапа 1 через реальный скрипт запуска."""

import pathlib
import subprocess
import tempfile
import unittest

ROOT = pathlib.Path(__file__).resolve().parent.parent
EXPECTED_IR = (
    "load_const A=38, B=439\n"
    "read_mem   A=63, B=201\n"
    "write_mem  A=62\n"
    "pow        A=14, B=782\n"
)


class CliTests(unittest.TestCase):
    """Контракт CLI: аргументы, IR и диагностика ошибок."""

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
        """Тестовый режим выдаёт все поля из PDF в ожидаемом формате."""
        for flag in ("--test", "-t"):
            with self.subTest(flag=flag):
                result = self.run_cli(
                    "asm", ROOT / "programs/spec_tests.asm", self.output,
                    flag,
                )
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertEqual(result.stdout, EXPECTED_IR)
                self.assertEqual(result.stderr, "")
                self.assertFalse(self.output.exists())

    def test_normal_mode(self):
        """Без флага ассемблер проверяет исходник без генерации бинарника."""
        result = self.run_cli(
            "asm", ROOT / "programs/spec_tests.asm", self.output,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout, "")
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
