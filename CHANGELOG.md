# Changelog

## 1.1.0 — 2026-10-19

- Accept either a decimal comma or decimal point and reject non-finite or ambiguous input.
- Calculate percentage amounts and remaining values with decimal arithmetic.
- Show readable results and inline errors in a resizable window; Enter calculates.
- Add regression tests and a hidden-window self-test of the packaged Windows application.
- Verify the Windows package and checksums before publishing a new release.

Supported input uses up to 18 integer digits and 12 fractional digits, without grouping separators or exponent notation. Negative values and percentages above 100 are supported.
