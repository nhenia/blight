"""Ingest OSM blight-adjacent features (abandoned, ruins, brownfields) within NOLA bbox.

Replaces the contents of the `osm_features` worksheet on each run.

Required env: GOOGLE_CREDENTIALS.
Invoke: python -m scripts.ingest_osm
"""
from __future__ import annotations
import json
import os
import sys
import gspread
from google.oauth2.service_account import Credentials

from scripts.lib.osm import fetch_features

SPREADSHEET_ID = '1O5zIhogpzmZLRn36X1Rt6cZUkWeYb2dzUgBTQszq_oE'
TAB_NAME = 'osm_features'
TAB_HEADER = ["id", "osm_type", "category", "lat", "lng", "name", "tags_summary"]


def _open_book():
    creds = json.loads(os.environ["GOOGLE_CREDENTIALS"])
    scopes = ['https://www.googleapis.com/auth/spreadsheets']
    return gspread.authorize(Credentials.from_service_account_info(creds, scopes=scopes)).open_by_key(SPREADSHEET_ID)


def _get_or_create_tab(book):
    try:
        ws = book.worksheet(TAB_NAME)
    except gspread.exceptions.WorksheetNotFound:
        ws = book.add_worksheet(title=TAB_NAME, rows=5000, cols=len(TAB_HEADER))
        ws.update([TAB_HEADER], "A1")
    return ws


def main() -> int:
    print("Querying Overpass...", file=sys.stderr)
    rows = fetch_features()
    print(f"  {len(rows)} OSM features.", file=sys.stderr)

    book = _open_book()
    ws = _get_or_create_tab(book)
    ingest_streetlamps(book)
    ingest_surveillance(book)
    payload = [TAB_HEADER] + [
        [r["id"], r["osm_type"], r["category"], r["lat"], r["lng"], r["name"], r["tags_summary"]]
        for r in rows
    ]
    ws.clear()
    ws.update(payload, "A1")
    print(f"Wrote {len(rows)} rows to `{TAB_NAME}` tab.", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

def ingest_streetlamps(book):
    print("Querying Streetlamps...", file=sys.stderr)
    rows = fetch_streetlamps()
    header = ["id", "lat", "lng"]
    ws = _get_or_create_tab_named(book, "streetlamps", header)
    payload = [header] + [[r["id"], r["lat"], r["lng"]] for r in rows]
    ws.clear()
    ws.update(payload, "A1")
    print(f"  {len(rows)} streetlamps.", file=sys.stderr)

def ingest_surveillance(book):
    print("Querying Surveillance...", file=sys.stderr)
    rows = fetch_surveillance()
    header = ["id", "lat", "lng", "type"]
    ws = _get_or_create_tab_named(book, "surveillance", header)
    payload = [header] + [[r["id"], r["lat"], r["lng"], r["type"]] for r in rows]
    ws.clear()
    ws.update(payload, "A1")
    print(f"  {len(rows)} cameras.", file=sys.stderr)

def _get_or_create_tab_named(book, name, header):
    try:
        ws = book.worksheet(name)
    except gspread.exceptions.WorksheetNotFound:
        ws = book.add_worksheet(title=name, rows=10000, cols=len(header))
        ws.update([header], "A1")
    return ws

from scripts.lib.osm import fetch_streetlamps, fetch_surveillance
