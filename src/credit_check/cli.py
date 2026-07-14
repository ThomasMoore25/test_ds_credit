"""CLI для credit_check.

Примеры запуска:
    credit-check extract dataset/contract_001.txt
    credit-check classify dataset/contract_001.txt
    credit-check check-subject "Поставка удобрений"
    credit-check run dataset/        # обработать всю папку
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from credit_check import classify, check_subject, extract


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _cmd_extract(args: argparse.Namespace) -> int:
    text = _read(Path(args.file))
    result = extract(text)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


def _cmd_classify(args: argparse.Namespace) -> int:
    text = _read(Path(args.file))
    doc_type, confidence = classify(text)
    print(f"{doc_type}\t{confidence:.3f}")
    return 0


def _cmd_check_subject(args: argparse.Namespace) -> int:
    matches, confidence, reason = check_subject(args.subject)
    label = "PASS" if matches else "FAIL"
    print(f"{label}\t{confidence:.3f}\t{reason}")
    return 0


def _cmd_run(args: argparse.Namespace) -> int:
    folder = Path(args.folder)
    rows = []
    for path in sorted(folder.glob("*.txt")):
        text = _read(path)
        result = extract(text)
        doc_type, conf = classify(text)
        rows.append({
            "file": path.name,
            "extract": result,
            "classify": {"type": doc_type, "confidence": round(conf, 3)},
        })
    print(json.dumps(rows, ensure_ascii=False, indent=2))
    return 0


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="credit-check", description=__doc__)
    sub = p.add_subparsers(dest="cmd", required=True)

    p_e = sub.add_parser("extract", help="extract fields from a file")
    p_e.add_argument("file")
    p_e.set_defaults(func=_cmd_extract)

    p_c = sub.add_parser("classify", help="classify document type")
    p_c.add_argument("file")
    p_c.set_defaults(func=_cmd_classify)

    p_s = sub.add_parser("check-subject", help="check subject against agri program")
    p_s.add_argument("subject")
    p_s.set_defaults(func=_cmd_check_subject)

    p_r = sub.add_parser("run", help="process all .txt files in a folder")
    p_r.add_argument("folder")
    p_r.set_defaults(func=_cmd_run)

    return p


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
