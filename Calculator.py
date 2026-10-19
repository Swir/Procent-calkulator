"""Offline percentage calculator with a separately testable calculation core."""
from decimal import Decimal, localcontext
import json
from pathlib import Path
import re
import sys
import tkinter as tk
from tkinter import ttk

VERSION = "1.1.0"
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


class CalculatorApp:
    def __init__(self, root):
        self.root = root
        root.title(f"Kalkulator procentów {VERSION}")
        root.minsize(480, 280)
        root.columnconfigure(0, weight=1)
        root.rowconfigure(0, weight=1)
        frame = ttk.Frame(root, padding=18)
        frame.grid(sticky="nsew")
        frame.columnconfigure(1, weight=1)
        self.value = tk.StringVar(root)
        self.percent = tk.StringVar(root)
        self.result = tk.StringVar(root, "Wpisz wartość i procent, następnie wybierz Oblicz.")
        self.error = tk.StringVar(root)
        ttk.Label(frame, text="Wartość:").grid(row=0, column=0, sticky="w", padx=(0, 12), pady=6)
        self.value_entry = ttk.Entry(frame, textvariable=self.value, width=32)
        self.value_entry.grid(row=0, column=1, sticky="ew", pady=6)
        ttk.Label(frame, text="Procent:").grid(row=1, column=0, sticky="w", pady=6)
        self.percent_entry = ttk.Entry(frame, textvariable=self.percent, width=32)
        self.percent_entry.grid(row=1, column=1, sticky="ew", pady=6)
        self.calculate_button = ttk.Button(frame, text="Oblicz", command=self.on_calculate)
        self.calculate_button.grid(row=2, column=0, columnspan=2, pady=12)
        ttk.Label(frame, textvariable=self.error, foreground="#a02020", wraplength=440).grid(row=3, column=0, columnspan=2, sticky="ew")
        self.result_label = ttk.Label(frame, textvariable=self.result, wraplength=440, justify="left")
        self.result_label.grid(row=4, column=0, columnspan=2, sticky="ew", pady=(8, 0))
        frame.bind("<Configure>", lambda event: self.result_label.configure(wraplength=max(200, event.width - 36)))
        root.bind("<Return>", lambda _event: self.on_calculate())

    def on_calculate(self):
        try:
            value, percent, part, remaining = calculate(self.value.get(), self.percent.get())
        except ValueError as error:
            self.error.set(str(error))
            self.result.set("")
            return False
        self.error.set("")
        self.result.set(f"{format_number(percent)}% z {format_number(value)} = {format_number(part)}\nPozostało: {format_number(remaining)}")
        return True


def self_test(report):
    root = None
    result = {"application": "Procent-Calculator", "version": VERSION, "passed": False}
    try:
        root = tk.Tk()
        root.withdraw()
        app = CalculatorApp(root)
        root.update_idletasks()
        app.value.set("1000")
        app.percent.set("20")
        app.calculate_button.invoke()
        assert app.result.get() == "20% z 1000 = 200\nPozostało: 800"
        app.value.set("0,3")
        app.percent.set("10")
        assert app.on_calculate() and "0,03" in app.result.get()
        app.value.set("NaN")
        assert not app.on_calculate() and app.error.get() and not app.result.get()
        result.update(passed=True, checks=["Tk widgets", "button calculation", "decimal comma", "invalid input"])
    except Exception as error:
        result["error"] = f"{type(error).__name__}: {error}"
    finally:
        if root is not None:
            root.destroy()
        Path(report).write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    return 0 if result["passed"] else 1


def main():
    if len(sys.argv) == 3 and sys.argv[1] == "--self-test":
        return self_test(sys.argv[2])
    root = tk.Tk()
    CalculatorApp(root)
    root.mainloop()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
