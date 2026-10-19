from decimal import Decimal, localcontext
import re
NUMBER = re.compile(r"[+-]?(?:[0-9]{1,18}(?:[.,][0-9]{0,12})?|[.,][0-9]{1,12})\Z")


def parse_number(text):
    text = text.strip()
    if not NUMBER.fullmatch(text):
        raise ValueError("Podaj liczbę: do 18 cyfr przed i 12 po przecinku lub kropce.")
    return Decimal(text.replace(",", "."))


def calculate(value_text, percent_text):
    value, percent = parse_number(value_text), parse_number(percent_text)
    with localcontext() as context:
        context.prec = 80
        part = value * percent / Decimal(100)
        return value, percent, part, value - part


def format_number(value):
    if value == 0:
        return "0"
    result = format(value, "f")
    if "." in result:
        result = result.rstrip("0").rstrip(".")
    return result.replace(".", ",")
