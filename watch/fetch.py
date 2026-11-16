"""Veille de la liste officielle des plateformes agréées (DGFiP).

Télécharge la page officielle, repère le fichier de la liste (xlsx, ods, csv ou pdf),
le normalise en CSV et écrit dans CHANGELOG.md les entrées, sorties et changements
de statut depuis le dernier passage.
"""
from __future__ import annotations

import csv
import datetime as dt
import hashlib
import io
import json
import re
import sys
import urllib.request
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urljoin

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
SOURCE_PAGE = "https://www.impots.gouv.fr/facturation-electronique-et-plateformes-agreees"
FALLBACK_PAGES = ["https://www.impots.gouv.fr/node/25455"]
UA = "annuaire-pa-watch (+https://github.com/Benalgodev/annuaire-pa-watch)"
EXT = (".xlsx", ".ods", ".csv", ".pdf")


def get(url: str) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=60) as r:
        return r.read()


class Links(HTMLParser):
    def __init__(self):
        super().__init__()
        self.links: list[tuple[str, str]] = []
        self._href: str | None = None
        self._text: list[str] = []

    def handle_starttag(self, tag, attrs):
        if tag == "a":
            self._href = dict(attrs).get("href")
            self._text = []

    def handle_data(self, data):
        if self._href:
            self._text.append(data)

    def handle_endtag(self, tag):
        if tag == "a" and self._href:
            self.links.append((self._href, " ".join(self._text).strip()))
            self._href = None


def find_list_file(page_url: str, html: str) -> str | None:
    p = Links()
    p.feed(html)
    scored = []
    for href, text in p.links:
        h = href.lower().split("?")[0]
        if not h.endswith(EXT):
            continue
        blob = f"{h} {text.lower()}"
        score = sum(k in blob for k in ("plateforme", "agre", "liste", "pa_", "pdp"))
        score += {".xlsx": 3, ".ods": 3, ".csv": 3, ".pdf": 0}[Path(h).suffix]
        scored.append((score, urljoin(page_url, href)))
    return max(scored)[1] if scored else None


def to_rows(name: str, blob: bytes) -> list[dict[str, str]]:
    suffix = Path(name.split("?")[0]).suffix.lower()
    if suffix == ".csv":
        text = blob.decode("utf-8-sig", errors="replace")
        return [dict(r) for r in csv.DictReader(io.StringIO(text), delimiter=";" if ";" in text[:500] else ",")]
    if suffix == ".xlsx":
        from openpyxl import load_workbook
        ws = load_workbook(io.BytesIO(blob), read_only=True, data_only=True).active
        rows = [[("" if c is None else str(c).strip()) for c in r] for r in ws.iter_rows(values_only=True)]
        rows = [r for r in rows if any(r)]
        head_i = next(i for i, r in enumerate(rows) if sum(bool(c) for c in r) >= 2)
        head = [h or f"col{i}" for i, h in enumerate(rows[head_i])]
        return [dict(zip(head, r)) for r in rows[head_i + 1:]]
    if suffix == ".pdf":
        import pdfplumber
        out: list[dict[str, str]] = []
        head = None
        with pdfplumber.open(io.BytesIO(blob)) as pdf:
            for page in pdf.pages:
                for table in page.extract_tables():
                    for r in table:
                        r = [(c or "").replace("\n", " ").strip() for c in r]
                        if head is None:
                            head = r
                        elif r != head and any(r):
                            out.append(dict(zip(head, r)))
        return out
    raise ValueError(f"Format non géré : {suffix}")


def key_of(row: dict[str, str]) -> str:
    for k, v in row.items():
        if re.search(r"siren|immatricul|num", k, re.IGNORECASE) and v:
            return re.sub(r"\s", "", v)
    return next((v for v in row.values() if v), "")


def diff(old: dict[str, dict], new: dict[str, dict]) -> list[str]:
    lines = []
    for k in sorted(new.keys() - old.keys()):
        lines.append(f"- Ajout : {' | '.join(v for v in new[k].values() if v)}")
    for k in sorted(old.keys() - new.keys()):
        lines.append(f"- Retrait : {' | '.join(v for v in old[k].values() if v)}")
    for k in sorted(old.keys() & new.keys()):
        changed = [f"{c} : {old[k].get(c, '')} → {new[k][c]}" for c in new[k]
                   if old[k].get(c, "") != new[k][c]]
        if changed:
            lines.append(f"- Modification {k} : " + " ; ".join(changed))
    return lines


def main() -> int:
    DATA.mkdir(exist_ok=True)
    file_url = None
    for page in [SOURCE_PAGE, *FALLBACK_PAGES]:
        try:
            file_url = find_list_file(page, get(page).decode("utf-8", errors="replace"))
        except Exception as e:  # noqa: BLE001
            print(f"page indisponible {page}: {e}", file=sys.stderr)
        if file_url:
            break
    if not file_url:
        print("Fichier de la liste introuvable sur la page officielle", file=sys.stderr)
        return 1

    blob = get(file_url)
    sha = hashlib.sha256(blob).hexdigest()
    meta_path = DATA / "meta.json"
    meta = json.loads(meta_path.read_text()) if meta_path.exists() else {}
    if meta.get("sha256") == sha:
        print("Aucun changement")
        return 0

    rows = to_rows(file_url, blob)
    new = {key_of(r): r for r in rows if key_of(r)}
    snap = DATA / "plateformes.json"
    old = json.loads(snap.read_text()) if snap.exists() else {}
    changes = diff(old, new) if old else [f"- Première capture : {len(new)} plateformes"]

    snap.write_text(json.dumps(new, ensure_ascii=False, indent=1, sort_keys=True))
    if rows:
        with open(DATA / "plateformes.csv", "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=list(rows[0].keys()), delimiter=";")
            w.writeheader()
            w.writerows(rows)
    today = dt.datetime.now(dt.timezone.utc).date().isoformat()
    meta_path.write_text(json.dumps({"sha256": sha, "source": file_url, "date": today,
                                     "count": len(new)}, indent=1))
    cl = ROOT / "CHANGELOG.md"
    prev = cl.read_text() if cl.exists() else "# Historique de la liste des plateformes agréées\n"
    head, _, rest = prev.partition("\n")
    entry = f"\n## {today} — {len(new)} plateformes\n\nSource : {file_url}\n\n" + "\n".join(changes) + "\n"
    cl.write_text(head + "\n" + entry + rest)
    print(f"{len(changes)} changement(s)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
