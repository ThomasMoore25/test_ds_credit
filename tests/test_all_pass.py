"""Мета-тест: проверяем, что набор тестов работает."""

from __future__ import annotations

import subprocess
import sys


def test_all_tests_collect():
    """Все тесты должны собираться без ошибок."""
    result = subprocess.run(
        [sys.executable, "-m", "pytest", "--collect-only", "-q"],
        capture_output=True, text=True, cwd=__import__('pathlib').Path(__file__).resolve().parent.parent,
    )
    assert result.returncode == 0, f"Collection failed: {result.stderr}"
    assert "test" in result.stdout.lower()


def test_test_files_exist():
    """Все expected тестовые файлы на месте."""
    from pathlib import Path
    test_dir = Path(__file__).resolve().parent
    expected = [
        "test_extract.py",
        "test_classify.py",
        "test_check_subject.py",
        "test_dataset.py",
        "test_api.py",
        "test_parsers_extra.py",
        "test_mandatory.py",
    ]
    for name in expected:
        assert (test_dir / name).exists(), f"Missing: {name}"
