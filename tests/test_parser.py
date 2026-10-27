import unittest
from cnab400 import BradescoReturnParser, CnabFormatError

def record(kind="1", fields=None):
    line = [" "] * 400; line[0] = kind
    for (start, end), value in (fields or {}).items(): line[start:end] = str(value).ljust(end-start)[:end-start]
    return "".join(line)

class ParserTests(unittest.TestCase):
    def setUp(self):
        self.text = "\n".join([
            record("0", {(1,4): "237"}),
            record(fields={(32,37): "12345", (70,82): "000000000123", (108,110): "06", (110,116): "150326", (146,152): "300326", (153,165): "0000000012345", (254,266): "0000000012345", (295,301): "160326", (318,328): "00"}),
            record(fields={(32,37): "12345", (70,82): "000000000124", (108,110): "02", (110,116): "150326", (146,152): "300326", (153,165): "0000000009900", (254,266): "0000000000000", (295,301): "000000", (318,328): "02"}),
            record("9", {(57,62): "00002", (62,74): "0000000022245", (74,86): "0000000012345", (86,91): "00001", (103,108): "00000", (108,120): "0000000000000"})
        ])
    def test_parse_details_and_trailer(self):
        result = BradescoReturnParser().parse_text(self.text)
        self.assertEqual(result.header.bank_code, "237")
        self.assertEqual(len(result.details), 2)
        self.assertEqual(result.details[0].our_number, "000000000123")
        self.assertEqual(str(result.details[0].paid_amount), "123.45")
        self.assertIsNone(result.details[1].credit_date)
        self.assertEqual(result.trailer.settled_count, 1)
    def test_rejects_wrong_length(self):
        with self.assertRaises(CnabFormatError): BradescoReturnParser().parse_text(self.text[:-2])
    def test_rejects_bad_total(self):
        with self.assertRaisesRegex(CnabFormatError, "Trailer inconsistente"): BradescoReturnParser().parse_text(self.text.replace("00002", "00003", 1))

if __name__ == "__main__": unittest.main()
