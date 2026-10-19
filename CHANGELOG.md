# Changelog

## 1.2.0 — 2026-10-19

- Replace the Tkinter interface with the approved native SwirUI dark/light design.
- Add quick percentage buttons, copy result and the value after adding the percentage.
- Preserve the tested Decimal calculation core and decimal-comma input.
- Fix the inherited resize cursor: restore a normal pointer in the client area while preserving all resize borders.
- Apply one shared icon policy: assets/icons/app.ico takes precedence; otherwise use the original SwirUI icon.
- Embed the selected icon in the Windows EXE and assign both native window icon sizes.
- Verify exact EXE icon resources, icon selection, cursor transitions and the extracted/downloaded runtime before publishing.
- Include current screenshots, source/build provenance and SHA-256 checksums.

Windows x64; the EXE includes SwirUI 0.1.0b1. A compatible graphics driver is required. The interface remains Polish.

## 1.1.0 — 2026-10-19

- Accept either a decimal comma or decimal point and reject non-finite or ambiguous input.
- Calculate percentage amounts and remaining values with decimal arithmetic.
- Show readable results and inline errors in a resizable window; Enter calculates.
- Add regression tests and a hidden-window self-test of the packaged Windows application.
- Verify the Windows package and checksums before publishing a new release.

Supported input uses up to 18 integer digits and 12 fractional digits, without grouping separators or exponent notation. Negative values and percentages above 100 are supported.
