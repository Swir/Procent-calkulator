from decimal import Decimal
import unittest
from calculation import calculate, format_number, parse_number


class CalculatorTests(unittest.TestCase):
    def test_percentage_and_remainder(self):
        self.assertEqual(calculate("1000", "20")[2:], (Decimal("200"), Decimal("800")))

    def test_decimal_comma_without_float_rounding(self):
        self.assertEqual(calculate("0,3", "10")[2:], (Decimal("0.03"), Decimal("0.27")))

    def test_zero_negative_and_over_one_hundred(self):
        cases = [("0", "20", "0", "0"), ("100", "0", "0", "100"),
                 ("-100", "20", "-20", "-80"), ("100", "150", "150", "-50"),
                 ("100", "-20", "-20", "120")]
        for value, percent, part, rest in cases:
            with self.subTest(value=value, percent=percent):
                self.assertEqual(calculate(value, percent)[2:], (Decimal(part), Decimal(rest)))

    def test_accepts_trimmed_signed_and_fractional_values(self):
        for text, expected in [(" +12,50 ", "12.50"), (".5", ".5"), ("-,5", "-.5"), ("12.", "12")]:
            with self.subTest(text=text):
                self.assertEqual(parse_number(text), Decimal(expected))

    def test_rejects_non_finite_ambiguous_and_excessive_inputs(self):
        for text in ["", "NaN", "nan", "inf", "-Infinity", "1e9999", "1,2.3", "1 000", "²", "１２", "1" * 19, "0." + "1" * 13, "--1"]:
            with self.subTest(text=text), self.assertRaises(ValueError):
                parse_number(text)

    def test_smallest_supported_input_is_not_rounded_to_zero(self):
        part = calculate("0.000000000001", "0.000000000001")[2]
        self.assertEqual(part, Decimal("1e-26"))
        self.assertNotEqual(format_number(part), "0")

    def test_readable_formatting(self):
        for value, expected in [("1000", "1000"), ("1.2500", "1,25"), ("-0.00", "0")]:
            self.assertEqual(format_number(Decimal(value)), expected)


if __name__ == "__main__":
    unittest.main()
