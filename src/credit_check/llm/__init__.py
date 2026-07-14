"""LLM-обёртки для credit_check."""

from credit_check.llm.subject_checker import check_subject_with_llm, is_llm_available

__all__ = ["check_subject_with_llm", "is_llm_available"]
