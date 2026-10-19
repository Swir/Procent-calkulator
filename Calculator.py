"""Native SwirUI preview for the percentage calculator."""
from dataclasses import replace
from decimal import localcontext
from pathlib import Path
import argparse
import json
import sys
import time

from swirui import App, Button, ButtonVariant, Input, Label, Panel, Palette, Theme, ThemeSurface, SurfaceStyle, Window, mount
from swirui.clipboard import ClipboardError, MemoryClipboard
from swirui.rendering import Color, Rect, WgpuRenderer
from calculation import calculate, format_number, parse_number
from native_window import CursorWin32Backend

VERSION = "1.2.0"
DARK = Theme(palette=Palette(
    canvas="#080D17", surface="#101A2B", raised="#0A1220", hover="#192D46",
    pressed="#203A57", border="#24364F", focus="#72D9FF", accent="#72D9FF",
    accent_hover="#A3E8FF", accent_pressed="#43B9E8", on_accent="#071322",
    text="#EDF5FF", muted="#94A9C3", disabled="#162235", disabled_text="#62758D",
    selection="#1D536E", success="#7FE5BA", warning="#F4CF86", error="#FFA7AE"),
    control_radius=14, font_family="Segoe UI",
    surface_style=SurfaceStyle(kind="glass", tint_opacity=.88, blur_radius=18,
                               elevation=8, glow_radius=6, depth_layers=0, depth_spacing=4))
LIGHT = replace(DARK, palette=Palette(
    canvas="#EEF3FA", surface="#FFFFFF", raised="#EDF3FA", hover="#DFEAF7",
    pressed="#CCDDED", border="#C7D6E7", focus="#006EA6", accent="#006EA6",
    accent_hover="#005D90", accent_pressed="#004B72", on_accent="#FFFFFF",
    text="#14283F", muted="#516982", disabled="#E1E8F1", disabled_text="#7A8B9E",
    selection="#B9D9F0", success="#177953", warning="#8A5900", error="#B32949"))
TRANSPARENT = Color(0, 0, 0, 0)


class CalculatorApp:
    def __init__(self, window):
        self.window = window
        self.dark = True
        self.current = None
        self.updating = False
        self.root = Panel(bounds=Rect(0, 0, 1080, 740), theme=DARK,
                          background=DARK.surface_color("canvas"))
        self.labels = []
        self.badge = Panel(bounds=Rect(0, 0, 1, 1), corner_radius=13)
        self.brand_icon = self.label("%", 28, "on_accent")
        self.brand = self.label("ŚWIR / KALKULATOR", 15)
        self.edition = self.label("SwirUI · 1.2.0", 13, "muted")
        self.mode = Button("Jasny motyw", bounds=Rect(0, 0, 1, 1), variant=ButtonVariant.SECONDARY, font_size=14)
        self.mode.on("click", lambda _: self.toggle_theme())
        self.title = self.label("Procenty. Po prostu.", 40)
        self.subtitle = self.label("Wpisz wartość, wybierz procent i zobacz dokładny wynik.", 16, "muted")
        self.form = Panel(bounds=Rect(0, 0, 1, 1), border_width=1, corner_radius=22)
        self.result_surface = ThemeSurface(bounds=Rect(0, 0, 1, 1))
        self.form_heading = self.label("Dane do obliczeń", 19)
        self.value_label = self.label("Wartość bazowa", 14, "muted")
        self.value = Input("1000", bounds=Rect(0, 0, 1, 1), font_size=25, padding=16,
                           max_length=40, accessible_name="Wartość bazowa", placeholder="np. 1000")
        self.percent_label = self.label("Procent", 14, "muted")
        self.percent = Input("20", bounds=Rect(0, 0, 1, 1), font_size=25, padding=16,
                             max_length=40, accessible_name="Procent", placeholder="np. 20")
        self.percent_sign = self.label("%", 22, "muted")
        self.quick = {}
        for value in (10, 15, 20, 23, 50):
            button = Button(f"{value}%", bounds=Rect(0, 0, 1, 1), variant=ButtonVariant.SECONDARY, font_size=14, padding=6)
            button.on("click", lambda _, value=value: self.use_percent(value))
            self.quick[value] = button
        self.go = Button("Oblicz wynik  →", bounds=Rect(0, 0, 1, 1), font_size=17)
        self.go.on("click", lambda _: self.compute())
        self.clear = Button("Wyczyść", bounds=Rect(0, 0, 1, 1), variant=ButtonVariant.GHOST, font_size=14)
        self.clear.on("click", lambda _: self.reset())
        self.message = self.label("Możesz użyć przecinka lub kropki.", 13, "muted")
        self.result_heading = self.label("TWÓJ WYNIK", 13, "accent")
        self.answer = Input("", bounds=Rect(0, 0, 1, 1), read_only=True,
                            font_size=72, padding=0, background=TRANSPARENT,
                            focused_background=TRANSPARENT, accessible_name="Wynik obliczenia")
        self.formula = self.label("", 19, "muted")
        self.divider = Panel(bounds=Rect(0, 0, 1, 1))
        self.rest_label = self.label("Po odjęciu procentu", 15, "muted")
        self.rest = Input("", bounds=Rect(0, 0, 1, 1), read_only=True, font_size=27, padding=0,
                          background=TRANSPARENT, focused_background=TRANSPARENT, accessible_name="Wartość po odjęciu procentu")
        self.plus_label = self.label("Po dodaniu procentu", 15, "muted")
        self.plus = Input("", bounds=Rect(0, 0, 1, 1), read_only=True, font_size=27, padding=0,
                          background=TRANSPARENT, focused_background=TRANSPARENT, accessible_name="Wartość po dodaniu procentu")
        self.copy = Button("Kopiuj wynik", bounds=Rect(0, 0, 1, 1), variant=ButtonVariant.SECONDARY, font_size=14)
        self.copy.on("click", lambda _: self.copy_result())
        self.footer = self.label("Dokładne obliczenia  /  Działa offline", 12, "muted")
        self.keyboard = self.label("Enter — oblicz   ·   Tab — następne pole", 12, "muted")
        self.form.add(self.form_heading, self.value_label, self.value, self.percent_label,
                      self.percent, self.percent_sign, *self.quick.values(), self.go, self.clear, self.message)
        self.result_surface.add(self.result_heading, self.answer, self.formula, self.divider,
                                self.rest_label, self.rest, self.plus_label, self.plus, self.copy)
        self.root.add(self.badge, self.brand_icon, self.brand, self.edition, self.mode,
                      self.title, self.subtitle, self.form, self.result_surface, self.footer, self.keyboard)
        for field in (self.value, self.percent):
            field.on("submitted", lambda _: self.compute())
            field.on("changed", lambda _: self.mark_pending())
        window.on("resized", lambda _: self.resize(window.width, window.height))
        self.resize(window.width, window.height)
        self.apply_theme()
        self.compute()

    def label(self, text, size=16, role="text"):
        widget = Label(text, bounds=Rect(0, 0, 1, 1), font_size=size, clip_to_bounds=True)
        self.labels.append((widget, role))
        return widget

    def apply_theme(self):
        theme = DARK if self.dark else LIGHT
        self.root.theme = theme
        self.root.background = theme.surface_color("canvas")
        self.badge.background = theme.surface_color("accent")
        self.divider.background = theme.surface_color("border")
        for label, role in self.labels:
            label.color = theme.text_color(role)
        self.mode.text = "Jasny motyw" if self.dark else "Ciemny motyw"
        self.message.color = theme.text_color("error" if self.message.text.startswith("Sprawdź") else "muted")

    def toggle_theme(self):
        self.dark = not self.dark
        self.apply_theme()

    def resize(self, width, height):
        self.root.bounds = Rect(0, 0, width, height)
        margin, gap, top = 36, 24, 196
        left = round((width - 2 * margin - gap) * .44)
        right_x, right_w = margin + left + gap, width - margin - (margin + left + gap)
        card_height = height - top - 56
        def box(widget, x, y, w, h):
            widget.bounds = Rect(x, y, max(1, w), max(1, h))
        box(self.badge, margin, 28, 44, 44)
        box(self.brand_icon, margin + 10, 30, 32, 40)
        box(self.brand, margin + 60, 27, 270, 25)
        box(self.edition, margin + 60, 52, 270, 22)
        box(self.mode, width - margin - 145, 31, 145, 40)
        box(self.title, margin, 100, width - margin * 2, 58)
        box(self.subtitle, margin, 157, width - margin * 2, 28)
        box(self.form, margin, top, left, card_height)
        box(self.result_surface, right_x, top, right_w, card_height)
        x, inner = margin + 24, left - 48
        box(self.form_heading, x, top + 23, inner, 30)
        box(self.value_label, x, top + 70, inner, 23)
        box(self.value, x, top + 98, inner, 59)
        box(self.percent_label, x, top + 177, inner, 23)
        box(self.percent, x, top + 205, inner - 46, 59)
        box(self.percent_sign, x + inner - 30, top + 215, 30, 38)
        quick_w = (inner - 24) / 5
        for i, button in enumerate(self.quick.values()):
            box(button, x + i * (quick_w + 6), top + 282, quick_w, 36)
        box(self.go, x, top + 342, inner - 91, 50)
        box(self.clear, x + inner - 84, top + 342, 84, 50)
        box(self.message, x, top + 408, inner, max(24, card_height - 420))
        rx, ri = right_x + 28, right_w - 56
        box(self.result_heading, rx, top + 28, ri, 26)
        box(self.answer, rx - 2, top + 73, ri, 102)
        box(self.formula, rx, top + 184, ri, 48)
        box(self.divider, rx, top + 248, ri, 1)
        small = (ri - 18) / 2
        box(self.rest_label, rx, top + 273, small, 42)
        box(self.rest, rx, top + 320, small, 48)
        box(self.plus_label, rx + small + 18, top + 273, small, 42)
        box(self.plus, rx + small + 18, top + 320, small, 48)
        box(self.copy, rx, top + card_height - 68, ri, 42)
        box(self.footer, margin, height - 35, 340, 22)
        box(self.keyboard, width - margin - 330, height - 35, 330, 22)
        self.fit_result()

    def fit_result(self):
        for field, maximum in ((self.answer, 72), (self.rest, 27), (self.plus, 27)):
            # Retained read-only inputs remain horizontally navigable for extreme values.
            size = min(maximum, max(17, field.bounds.width / max(1, len(field.value) * .62)))
            field.font_size = size

    def mark_pending(self):
        if self.updating:
            return
        self.current = None
        self.answer.value = ""
        self.rest.value = ""
        self.plus.value = ""
        self.formula.text = "Gotowe? Wybierz „Oblicz wynik”."
        self.copy.enabled = False
        self.copy.text = "Kopiuj wynik"
        self.message.text = "Możesz użyć przecinka lub kropki."
        self.apply_theme()
        for button in self.quick.values():
            button.variant = ButtonVariant.SECONDARY

    def compute(self):
        try:
            value, percent, part, remaining = calculate(self.value.value, self.percent.value)
            with localcontext() as context:
                context.prec = 80
                increased = value + part
        except ValueError:
            self.mark_pending()
            self.formula.text = "Wynik pojawi się po poprawieniu danych."
            self.message.text = "Sprawdź liczby: do 18 cyfr przed\ni 12 po przecinku lub kropce."
            self.apply_theme()
            return False
        self.current = part
        self.answer.value = format_number(part)
        self.rest.value = format_number(remaining)
        self.plus.value = format_number(increased)
        self.formula.text = f"{format_number(percent)}% z {format_number(value)}"
        self.message.text = "Możesz użyć przecinka lub kropki."
        self.copy.enabled = True
        self.copy.text = "Kopiuj wynik"
        for amount, button in self.quick.items():
            button.variant = ButtonVariant.PRIMARY if percent == amount else ButtonVariant.SECONDARY
        self.apply_theme()
        self.fit_result()
        return True

    def use_percent(self, value):
        self.percent.value = str(value)
        self.compute()

    def reset(self):
        self.updating = True
        self.value.value = ""
        self.percent.value = ""
        self.updating = False
        self.mark_pending()
        self.formula.text = "Wpisz wartość i procent, aby zacząć."
        self.window.focus_component(self.value)

    def copy_result(self):
        if self.current is None:
            return False
        try:
            self.window.set_clipboard_text(format_number(self.current))
        except ClipboardError:
            self.message.text = "Schowek jest zajęty. Spróbuj ponownie."
            return False
        self.copy.text = "Skopiowano"
        return True


def create_app(testing=False):
    renderer = WgpuRenderer()
    app = App("Świr — Kalkulator procentów", renderer=renderer, platform_backend=CursorWin32Backend())
    window = app.add_window(Window(title="Świr — Kalkulator procentów 1.2.0",
        width=1080, height=740, min_width=900, min_height=720,
        clipboard=MemoryClipboard("unchanged") if testing else None))
    view = CalculatorApp(window)
    mount(window, view.root)
    return app, window, view, renderer


def run_preview_check(destination, report_path=None):
    """Render the real GPU scene and exercise controls without injecting OS input."""
    from PIL import Image
    from cursor_verification import check_window_cursor
    destination = Path(destination).resolve()
    destination.mkdir(parents=True, exist_ok=True)
    app, window, view, renderer = create_app(testing=True)
    checks = []
    try:
        app.start()
        for _ in range(4):
            app.process_events()
            time.sleep(.04)
        cursor_checks = check_window_cursor(window.native_handle.value)
        checks.append("normal pointer restored after all eight resize borders and two inherited cursors")
        icon_check = app.platform_backend.verify_window_icons(window.native_handle)
        checks.append("native small and large window icons")
        def render(filename):
            app.invalidate(window)
            app.render_pending(app._frame_schedulers[window].stats.last_frame_time + 1)
            context = renderer._contexts[window.native_handle.value]
            width, height, pixels = context.read_scene_rgba()
            assert width > 100 and height > 100 and len(pixels) == width * height * 4
            Image.frombytes("RGBA", (width, height), bytes(pixels)).save(destination / filename)
        assert view.answer.value == "200" and view.rest.value == "800" and view.plus.value == "1200"
        render("kalkulator-swirui-ciemny.png")
        checks.append("native GPU rendering and default calculation")
        view.mode.emit("click")
        assert not view.dark and view.value.value == "1000"
        render("kalkulator-swirui-jasny.png")
        checks.append("live theme switch preserves values")
        view.mode.emit("click")
        view.value.value = "0,3"
        view.percent.value = "10"
        view.percent.emit("submitted")
        assert view.answer.value == "0,03" and view.rest.value == "0,27"
        checks.append("decimal comma and Enter submission")
        view.value.value = "1000"
        view.quick[23].emit("click")
        assert view.answer.value == "230" and view.plus.value == "1230"
        view.copy.emit("click")
        assert window.get_clipboard_text() == "230"
        checks.append("quick percentages and isolated clipboard")
        view.value.value = "NaN"
        view.go.emit("click")
        assert view.current is None and not view.copy.enabled and view.answer.value == ""
        render("kalkulator-swirui-blad.png")
        checks.append("invalid data clears stale result")
        view.value.value = "999999999999999999,999999999999"
        view.percent.value = "999999999999999999,999999999999"
        view.go.emit("click")
        assert view.current is not None and view.copy_result()
        assert window.get_clipboard_text() == format_number(view.current)
        checks.append("large exact values remain copyable")
        view.clear.emit("click")
        assert view.value.value == view.percent.value == "" and not view.copy.enabled
        assert window.focused_component is view.value
        checks.append("clear and keyboard focus")
        view.value.value = "1000"
        view.percent.value = "20"
        view.go.emit("click")
        window.resize(900, 720)
        app.process_events()
        render("kalkulator-swirui-kompakt.png")
        assert view.copy.bounds.bottom < view.result_surface.bounds.bottom
        assert view.message.bounds.bottom <= view.form.bounds.bottom
        checks.append("compact 900x720 layout")
        report = {"application": "Procent-Calculator", "passed": True, "version": VERSION, "swirui": "0.1.0b1",
                  "adapter": renderer.adapter_name, "backend": renderer.graphics_backend,
                  "checks": checks, "cursor_checks": cursor_checks, "icon": icon_check}
        (destination / "verification.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
        if report_path is not None:
            Path(report_path).write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
        print(json.dumps(report, ensure_ascii=True))
    finally:
        app.stop()
    return 0


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--preview-check", metavar="OUTPUT_DIRECTORY")
    parser.add_argument("--self-test", metavar="REPORT_JSON")
    args = parser.parse_args()
    if args.preview_check:
        return run_preview_check(args.preview_check)
    if args.self_test:
        import tempfile
        report = Path(args.self_test).resolve()
        report.parent.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(prefix="swirui-check-", dir=report.parent) as scratch:
            return run_preview_check(scratch, report_path=report)
    app, _, _, _ = create_app()
    try:
        return app.run()
    finally:
        app.stop()


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception:
        import traceback
        log = Path(sys.executable).parent if getattr(sys, "frozen", False) else Path(__file__).resolve().parent
        try:
            (log / "error.log").write_text(traceback.format_exc(), encoding="utf-8")
        except OSError:
            pass
        raise
