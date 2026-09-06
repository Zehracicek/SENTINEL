"""Mevcut .env dosyalarının üzerine yazmaz; yalnızca eksik anahtarları doldurur."""

from __future__ import annotations

import secrets
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BACKEND_ENV = ROOT / "backend" / ".env"
FRONTEND_ENV = ROOT / "frontend" / ".env"
BACKEND_EXAMPLE = ROOT / "backend" / ".env.example"
FRONTEND_EXAMPLE = ROOT / "frontend" / ".env.example"


def _parse(path: Path) -> dict[str, str]:
    out: dict[str, str] = {}
    if not path.exists():
        return out
    for line in path.read_text(encoding="utf-8-sig").splitlines():
        if not line.strip() or line.lstrip().startswith("#") or "=" not in line:
            continue
        k, v = line.split("=", 1)
        out[k.strip()] = v.strip()
    return out


def _write(path: Path, values: dict[str, str], example: Path) -> None:
    if path.exists():
        text = path.read_text(encoding="utf-8-sig")
        lines = text.splitlines()
        seen: set[str] = set()
        new_lines: list[str] = []
        for line in lines:
            if "=" in line and not line.lstrip().startswith("#"):
                k = line.split("=", 1)[0].strip()
                seen.add(k)
                if k in values:
                    new_lines.append(f"{k}={values[k]}")
                    continue
            new_lines.append(line)
        for k, v in values.items():
            if k not in seen:
                new_lines.append(f"{k}={v}")
        path.write_text("\n".join(new_lines) + "\n", encoding="utf-8", newline="\n")
        return
    src = example.read_text(encoding="utf-8") if example.exists() else ""
    path.write_text(src, encoding="utf-8", newline="\n")
    _write(path, values, example)


def main() -> None:
    be = _parse(BACKEND_ENV)
    fe = _parse(FRONTEND_ENV)
    tok = (be.get("SENTINEL_API_TOKEN") or fe.get("VITE_API_TOKEN") or "").strip()
    if not tok:
        tok = secrets.token_urlsafe(24)
    be_updates = {}
    if not (be.get("SENTINEL_API_TOKEN") or "").strip():
        be_updates["SENTINEL_API_TOKEN"] = tok
    if "SENTINEL_ROVER_THINKING_ENABLED" not in be:
        be_updates["SENTINEL_ROVER_THINKING_ENABLED"] = "true"
    if be_updates:
        _write(BACKEND_ENV, {**be, **be_updates}, BACKEND_EXAMPLE)
        be = _parse(BACKEND_ENV)
    fe_tok = (fe.get("VITE_API_TOKEN") or "").strip()
    if fe_tok != (be.get("SENTINEL_API_TOKEN") or "").strip():
        _write(FRONTEND_ENV, {**fe, "VITE_API_TOKEN": be.get("SENTINEL_API_TOKEN", tok)}, FRONTEND_EXAMPLE)
    print("env_ok")


if __name__ == "__main__":
    main()
