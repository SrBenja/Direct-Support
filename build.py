from __future__ import annotations

from pathlib import Path
import html
import os
import re
import shutil
import sys

ROOT = Path(__file__).resolve().parent
SITE = ROOT / "site"
DIST = ROOT / "dist"
TEMPLATE = SITE / "index.template.html"

PLACEHOLDERS = {
    "__TAKENOS_NAME__": "TAKENOS_NAME",
    "__TAKENOS_ACH_ACCOUNT__": "TAKENOS_ACH_ACCOUNT",
    "__TAKENOS_ACH_ROUTING__": "TAKENOS_ACH_ROUTING",
    "__TAKENOS_ACH_ACCOUNT_TYPE__": "TAKENOS_ACH_ACCOUNT_TYPE",
    "__TAKENOS_ACH_BANK__": "TAKENOS_ACH_BANK",
    "__TAKENOS_ACH_BANK_ADDRESS__": "TAKENOS_ACH_BANK_ADDRESS",
    "__TAKENOS_SEPA_IBAN__": "TAKENOS_SEPA_IBAN",
    "__TAKENOS_SEPA_BIC__": "TAKENOS_SEPA_BIC",
    "__TAKENOS_SEPA_BANK__": "TAKENOS_SEPA_BANK",
    "__TAKENOS_SEPA_BANK_ADDRESS__": "TAKENOS_SEPA_BANK_ADDRESS",
}

SENSITIVE_SOURCE_CHECKS = (
    "TAKENOS_ACH_ACCOUNT",
    "TAKENOS_ACH_ROUTING",
    "TAKENOS_SEPA_IBAN",
)


def fail(message: str) -> "NoReturn":
    print(f"Build stopped: {message}", file=sys.stderr)
    raise SystemExit(1)


def compact_text(value: str, field: str, *, max_length: int = 180) -> str:
    value = " ".join(value.split())
    if not value:
        fail(f"{field} is empty.")
    if len(value) > max_length:
        fail(f"{field} is unexpectedly long.")
    if any(ord(char) < 32 for char in value):
        fail(f"{field} contains control characters.")
    return value


def digits(value: str, field: str, *, minimum: int, maximum: int) -> str:
    value = re.sub(r"\s+", "", value)
    if not value.isdigit() or not minimum <= len(value) <= maximum:
        fail(f"{field} has an invalid numeric format.")
    return value


def validate_aba_routing(value: str) -> str:
    value = digits(value, "TAKENOS_ACH_ROUTING", minimum=9, maximum=9)
    d = [int(x) for x in value]
    checksum = 3 * (d[0] + d[3] + d[6]) + 7 * (d[1] + d[4] + d[7]) + (d[2] + d[5] + d[8])
    if checksum % 10 != 0:
        fail("TAKENOS_ACH_ROUTING failed the ABA checksum.")
    return value


def validate_iban(value: str) -> str:
    value = re.sub(r"\s+", "", value).upper()
    if not re.fullmatch(r"[A-Z]{2}[0-9]{2}[A-Z0-9]{11,30}", value):
        fail("TAKENOS_SEPA_IBAN has an invalid format.")

    rearranged = value[4:] + value[:4]
    numeric = "".join(char if char.isdigit() else str(ord(char) - 55) for char in rearranged)
    if int(numeric) % 97 != 1:
        fail("TAKENOS_SEPA_IBAN failed the IBAN checksum.")
    return value


def validate_bic(value: str) -> str:
    value = re.sub(r"\s+", "", value).upper()
    if not re.fullmatch(r"[A-Z]{4}[A-Z]{2}[A-Z0-9]{2}(?:[A-Z0-9]{3})?", value):
        fail("TAKENOS_SEPA_BIC has an invalid BIC/SWIFT format.")
    return value


def collect_values() -> dict[str, str]:
    missing = [name for name in PLACEHOLDERS.values() if not os.environ.get(name, "").strip()]
    if missing:
        print("Build stopped. Missing required environment secrets:", file=sys.stderr)
        for name in sorted(set(missing)):
            print(f" - {name}", file=sys.stderr)
        raise SystemExit(1)

    values = {
        "TAKENOS_NAME": compact_text(os.environ["TAKENOS_NAME"], "TAKENOS_NAME", max_length=120),
        "TAKENOS_ACH_ACCOUNT": digits(os.environ["TAKENOS_ACH_ACCOUNT"], "TAKENOS_ACH_ACCOUNT", minimum=4, maximum=20),
        "TAKENOS_ACH_ROUTING": validate_aba_routing(os.environ["TAKENOS_ACH_ROUTING"]),
        "TAKENOS_ACH_ACCOUNT_TYPE": compact_text(os.environ["TAKENOS_ACH_ACCOUNT_TYPE"], "TAKENOS_ACH_ACCOUNT_TYPE", max_length=60),
        "TAKENOS_ACH_BANK": compact_text(os.environ["TAKENOS_ACH_BANK"], "TAKENOS_ACH_BANK", max_length=120),
        "TAKENOS_ACH_BANK_ADDRESS": compact_text(os.environ["TAKENOS_ACH_BANK_ADDRESS"], "TAKENOS_ACH_BANK_ADDRESS"),
        "TAKENOS_SEPA_IBAN": validate_iban(os.environ["TAKENOS_SEPA_IBAN"]),
        "TAKENOS_SEPA_BIC": validate_bic(os.environ["TAKENOS_SEPA_BIC"]),
        "TAKENOS_SEPA_BANK": compact_text(os.environ["TAKENOS_SEPA_BANK"], "TAKENOS_SEPA_BANK", max_length=140),
        "TAKENOS_SEPA_BANK_ADDRESS": compact_text(os.environ["TAKENOS_SEPA_BANK_ADDRESS"], "TAKENOS_SEPA_BANK_ADDRESS"),
    }
    return values


def ensure_sensitive_values_are_not_in_source(values: dict[str, str]) -> None:
    paths = [
        ROOT / "build.py",
        ROOT / "README.md",
        ROOT / ".gitignore",
        ROOT / ".github" / "workflows" / "pages.yml",
        SITE / "index.template.html",
        SITE / "styles.css",
        SITE / "app.js",
    ]

    for secret_name in SENSITIVE_SOURCE_CHECKS:
        value = values[secret_name]
        if len(value) < 6:
            continue
        for path in paths:
            if path.exists() and value in path.read_text(encoding="utf-8"):
                fail(f"a sensitive value from {secret_name} appears in tracked source file {path.relative_to(ROOT)}.")


def main() -> None:
    if not TEMPLATE.is_file():
        fail("site/index.template.html is missing.")

    values = collect_values()
    ensure_sensitive_values_are_not_in_source(values)

    rendered = TEMPLATE.read_text(encoding="utf-8")
    for placeholder, secret_name in PLACEHOLDERS.items():
        rendered = rendered.replace(placeholder, html.escape(values[secret_name], quote=True))

    if "__TAKENOS_" in rendered:
        fail("one or more Takenos placeholders were not replaced.")

    if DIST.exists():
        shutil.rmtree(DIST)
    DIST.mkdir(parents=True, exist_ok=False)

    (DIST / "index.html").write_text(rendered, encoding="utf-8", newline="\n")
    shutil.copy2(SITE / "styles.css", DIST / "styles.css")
    shutil.copy2(SITE / "app.js", DIST / "app.js")

    print("Site built and validated successfully.")


if __name__ == "__main__":
    main()
