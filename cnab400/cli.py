"""Interface de linha de comando do leitor CNAB 400."""
from __future__ import annotations
import argparse, json, sys
from pathlib import Path
from .bradesco import BradescoReturnParser, CnabFormatError

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="cnab400", description="Valida e lê um retorno de cobrança Bradesco CNAB 400.")
    parser.add_argument("arquivo", type=Path, help="caminho do arquivo .RET")
    parser.add_argument("--csv", type=Path, help="exporta os detalhes para CSV")
    parser.add_argument("--json", dest="json_path", type=Path, help="exporta o resumo para JSON")
    parser.add_argument("--encoding", default="cp1252", help="codificação do arquivo")
    parser.add_argument("--allow-total-mismatch", action="store_true", help="não falha quando o trailer difere das linhas lidas")
    return parser

def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        result = BradescoReturnParser(encoding=args.encoding, validate_totals=not args.allow_total_mismatch).parse(args.arquivo)
        if args.csv: result.write_csv(args.csv)
        if args.json_path: result.write_json(args.json_path)
        print(json.dumps(result.to_dict(), ensure_ascii=False, indent=2))
        return 0
    except (OSError, CnabFormatError) as error:
        print(f"Erro: {error}", file=sys.stderr)
        return 2

if __name__ == "__main__":
    raise SystemExit(main())
