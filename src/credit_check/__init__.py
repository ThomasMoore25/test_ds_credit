"""AI-агент проверки целевого использования льготных кредитов.

Публичный API:
    from credit_check import extract, classify, check_subject
"""

from credit_check.extract import extract
from credit_check.classify import classify
from credit_check.check_subject import check_subject

__all__ = ["extract", "classify", "check_subject"]
__version__ = "0.6.0"
