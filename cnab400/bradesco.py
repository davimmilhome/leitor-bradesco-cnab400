"""Parser do retorno de cobrança Bradesco no leiaute CNAB 400."""
from __future__ import annotations
import csv, json
from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from pathlib import Path
from typing import TextIO

RECORD_LENGTH = 400

class CnabFormatError(ValueError):
    """Arquivo fora da estrutura CNAB 400 esperada."""

@dataclass(frozen=True, slots=True)
class HeaderRecord:
    record_type: str
    bank_code: str
    raw: str

@dataclass(frozen=True, slots=True)
class DetailRecord:
    line_number: int
    account: str
    our_number: str
    occurrence_code: str
    occurrence_date: date | None
    due_date: date | None
    title_amount: Decimal
    paid_amount: Decimal
    credit_date: date | None
    reason: str
    raw: str
    def to_dict(self) -> dict[str, object]:
        return {"linha": self.line_number, "conta": self.account, "nosso_numero": self.our_number, "ocorrencia": self.occurrence_code, "data_ocorrencia": _date_text(self.occurrence_date), "data_vencimento": _date_text(self.due_date), "valor_titulo": _decimal_text(self.title_amount), "valor_pago": _decimal_text(self.paid_amount), "data_credito": _date_text(self.credit_date), "motivo": self.reason}

@dataclass(frozen=True, slots=True)
class TrailerSummary:
    detail_count: int
    registered_amount: Decimal
    settled_count: int
    settled_amount: Decimal
    cancelled_count: int
    cancelled_amount: Decimal
    raw: str
    def to_dict(self) -> dict[str, object]:
        return {"quantidade_registros": self.detail_count, "valor_registrado": _decimal_text(self.registered_amount), "quantidade_liquidado": self.settled_count, "valor_liquidado": _decimal_text(self.settled_amount), "quantidade_baixa": self.cancelled_count, "valor_baixado": _decimal_text(self.cancelled_amount)}

@dataclass(frozen=True, slots=True)
class BradescoReturnFile:
    source: str
    header: HeaderRecord
    details: tuple[DetailRecord, ...]
    trailer: TrailerSummary
    def to_dict(self) -> dict[str, object]:
        return {"arquivo": self.source, "header": {"tipo_registro": self.header.record_type, "codigo_banco": self.header.bank_code}, "transacoes": [d.to_dict() for d in self.details], "trailer": self.trailer.to_dict()}
    def write_csv(self, destination: str | Path, *, encoding: str = "utf-8-sig") -> None:
        fields = ["linha", "conta", "nosso_numero", "ocorrencia", "data_ocorrencia", "data_vencimento", "valor_titulo", "valor_pago", "data_credito", "motivo"]
        with Path(destination).open("w", encoding=encoding, newline="") as file:
            writer = csv.DictWriter(file, fieldnames=fields, delimiter=";")
            writer.writeheader(); writer.writerows(d.to_dict() for d in self.details)
    def write_json(self, destination: str | Path, *, encoding: str = "utf-8") -> None:
        with Path(destination).open("w", encoding=encoding) as file:
            json.dump(self.to_dict(), file, ensure_ascii=False, indent=2); file.write("\n")

class BradescoReturnParser:
    """Parser sem estado global para retorno Bradesco CNAB 400 tipo 1."""
    def __init__(self, *, encoding: str = "cp1252", validate_totals: bool = True) -> None:
        self.encoding, self.validate_totals = encoding, validate_totals
    def parse(self, source: str | Path) -> BradescoReturnFile:
        path = Path(source)
        try:
            with path.open("r", encoding=self.encoding, newline="") as file: return self.parse_stream(file, source=str(path))
        except UnicodeDecodeError as error: raise CnabFormatError(f"Não foi possível decodificar {path} como {self.encoding}.") from error
    def parse_text(self, text: str, *, source: str = "<memória>") -> BradescoReturnFile:
        from io import StringIO
        return self.parse_stream(StringIO(text), source=source)
    def parse_stream(self, stream: TextIO, *, source: str) -> BradescoReturnFile:
        lines = [line.rstrip("\r\n") for line in stream]
        if not lines: raise CnabFormatError("O arquivo está vazio.")
        for number, line in enumerate(lines, 1):
            if not line: raise CnabFormatError(f"Linha {number}: registro vazio.")
            if len(line) != RECORD_LENGTH: raise CnabFormatError(f"Linha {number}: esperado registro com 400 posições; recebido {len(line)}.")
        if lines[0][0] != "0": raise CnabFormatError("O primeiro registro deve ser um header tipo 0.")
        if lines[-1][0] != "9": raise CnabFormatError("O último registro deve ser um trailer tipo 9.")
        for number, line in enumerate(lines, 1):
            if line[0] not in {"0", "1", "9"}: raise CnabFormatError(f"Linha {number}: tipo de registro inesperado {line[0]!r}.")
        details_lines = lines[1:-1]
        for number, line in enumerate(details_lines, 2):
            if line[0] != "1": raise CnabFormatError(f"Linha {number}: esperado registro detalhe tipo 1.")
        header = HeaderRecord("0", lines[0][1:4].strip(), lines[0])
        details = tuple(self._parse_detail(line, number) for number, line in enumerate(details_lines, 2))
        trailer = self._parse_trailer(lines[-1])
        if self.validate_totals and trailer.detail_count != len(details): raise CnabFormatError(f"Trailer inconsistente: quantidade de registros informada ({trailer.detail_count}) difere dos detalhes lidos ({len(details)}).")
        return BradescoReturnFile(source, header, details, trailer)
    @staticmethod
    def _parse_detail(line: str, line_number: int) -> DetailRecord:
        return DetailRecord(line_number, line[32:37].strip(), line[70:82].strip(), line[108:110].strip(), _parse_date(line[110:116], line_number, "data da ocorrência"), _parse_date(line[146:152], line_number, "data de vencimento"), _parse_cents(line[153:165], line_number, "valor do título"), _parse_cents(line[254:266], line_number, "valor pago"), _parse_date(line[295:301], line_number, "data de crédito"), line[318:328].strip(), line)
    @staticmethod
    def _parse_trailer(line: str) -> TrailerSummary:
        return TrailerSummary(_parse_integer(line[57:62], 0, "quantidade de registros"), _parse_cents(line[62:74], 0, "valor registrado"), _parse_integer(line[86:91], 0, "quantidade liquidada"), _parse_cents(line[74:86], 0, "valor liquidado"), _parse_integer(line[103:108], 0, "quantidade baixada"), _parse_cents(line[108:120], 0, "valor baixado"), line)

def _parse_integer(value: str, line_number: int, field: str) -> int:
    value = value.strip()
    if not value or not value.isdigit(): raise CnabFormatError(f"{'Linha ' + str(line_number) + ': ' if line_number else 'Trailer: '}{field} inválida: {value!r}.")
    return int(value)
def _parse_cents(value: str, line_number: int, field: str) -> Decimal:
    return Decimal(_parse_integer(value, line_number, field)) / Decimal(100)
def _parse_date(value: str, line_number: int, field: str) -> date | None:
    value = value.strip()
    if not value or value == "000000": return None
    if len(value) != 6 or not value.isdigit(): raise CnabFormatError(f"Linha {line_number}: {field} inválida: {value!r}.")
    try: return date(2000 + int(value[4:]), int(value[2:4]), int(value[:2]))
    except ValueError as error: raise CnabFormatError(f"Linha {line_number}: {field} inválida: {value!r}.") from error
def _date_text(value: date | None) -> str: return value.isoformat() if value else ""
def _decimal_text(value: Decimal) -> str: return f"{value:.2f}"
