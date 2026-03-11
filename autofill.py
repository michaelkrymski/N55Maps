# autofill_v2.py
# Fast map autofill for grid editors: types values left->right, then home (left×N) and down.
# Inputs: CSV/TSV (--csv), JSON/Python 2D array string (--array), clipboard (--from-clipboard), or stdin (--paste).
# Defaults to ~3ms per action as requested.

import time
import csv
import argparse
import json
import sys
from typing import List, Any

import pyautogui
try:
    import pyperclip
    USE_CLIP = True
except Exception:
    USE_CLIP = False


def press(key: str, n: int = 1, pause: float = 0.003):
    for _ in range(n):
        pyautogui.press(key)
        if pause:
            time.sleep(pause)

def paste_text(text: Any, pause: float = 0.003):
    s = "" if text is None else str(text)
    if USE_CLIP:
        try:
            pyperclip.copy(s)
            pyautogui.hotkey('ctrl', 'v')
        except Exception:
            pyautogui.typewrite(s, interval=0.0)
    else:
        pyautogui.typewrite(s, interval=0.0)
    if pause:
        time.sleep(pause)


def _normalize_rows(rows: List[List[str]]):
    if not rows:
        return
    max_len = max(len(r) for r in rows)
    for r in rows:
        if len(r) < max_len:
            r += [""] * (max_len - len(r))


def load_table_csv(path: str, delimiter: str | None = None) -> List[List[str]]:
    if delimiter is None:
        with open(path, 'r', newline='', encoding='utf-8-sig') as f:
            sample = f.read(2048)
            try:
                dialect = csv.Sniffer().sniff(sample, delimiters=",\t; ")
                delimiter = dialect.delimiter
            except Exception:
                delimiter = ','
    rows: List[List[str]] = []
    with open(path, 'r', newline='', encoding='utf-8-sig') as f:
        reader = csv.reader(f, delimiter=delimiter)
        for row in reader:
            if not row:
                continue
            rows.append([c.strip() for c in row])
    _normalize_rows(rows)
    return rows


def parse_2d(text: str) -> List[List[str]]:
    """Parse a 2D structure from JSON, Python-list-ish, or plain text block.
    Accepts:
      - JSON: [[1,2],[3,4]]
      - Python-ish: [ [1, 2], [3, 4] ]
      - Plain: lines separated by newlines; cells by comma/tab/semicolon/whitespace
    """
    t = text.strip()
    # Try JSON
    try:
        data = json.loads(t)
        if isinstance(data, list) and all(isinstance(r, list) for r in data):
            rows = [[str(c).strip() for c in r] for r in data]
            _normalize_rows(rows)
            return rows
    except Exception:
        pass
    # Try a restricted eval on Python-like lists
    if t.startswith('[') and t.endswith(']'):
        try:
            data = eval(t, {"__builtins__": {}}, {})
            if isinstance(data, list) and all(isinstance(r, list) for r in data):
                rows = [[str(c).strip() for c in r] for r in data]
                _normalize_rows(rows)
                return rows
        except Exception:
            pass
    # Fallback: split lines then pick a delimiter
    lines = [ln for ln in t.splitlines() if ln.strip()]
    rows: List[List[str]] = []
    for ln in lines:
        for sep in (',', '\t', ';'):
            if sep in ln:
                cells = [c.strip() for c in ln.split(sep)]
                break
        else:
            cells = ln.split()
        rows.append(cells)
    _normalize_rows(rows)
    return rows


def main():
    ap = argparse.ArgumentParser(description="Autofill a 2D map into a grid using keyboard arrows.")
    src = ap.add_mutually_exclusive_group(required=True)
    src.add_argument("--csv", dest="csv_path", help="Path to CSV/TSV file containing the map.")
    src.add_argument("--array", dest="array_text", help="JSON/Python-style 2D array, or a newline block.")
    src.add_argument("--paste", action="store_true", help="Read a 2D block from STDIN until EOF (Ctrl-D/Ctrl-Z).")
    src.add_argument("--from-clipboard", action="store_true", help="Read 2D data from clipboard (requires pyperclip).")

    ap.add_argument("--delimiter", default=None, help="Delimiter for CSV (default: auto-detect).")
    ap.add_argument("--delay", type=float, default=0.003, help="Per-keystroke pause in seconds (default 0.003).")
    ap.add_argument("--clear", action="store_true", help="Backspace-clear each cell before typing.")
    ap.add_argument("--countdown", type=float, default=3.0, help="Seconds to wait before starting (default 3).")

    args = ap.parse_args()

    # Load data
    if args.csv_path:
        table = load_table_csv(args.csv_path, delimiter=args.delimiter)
    elif args.array_text:
        table = parse_2d(args.array_text)
    elif args.paste:
        buf = sys.stdin.read()
        table = parse_2d(buf)
    else:  # from-clipboard
        if not USE_CLIP:
            print("pyperclip not available. Install it or use --paste/--array/--csv.")
            sys.exit(1)
        table = parse_2d(pyperclip.paste())

    rows = len(table)
    cols = len(table[0]) if rows else 0
    if rows == 0 or cols == 0:
        print("No data found to type.")
        sys.exit(1)

    # Configure pyautogui
    pyautogui.FAILSAFE = True   # Move mouse to a corner to abort
    pyautogui.PAUSE = 0.0       # no implicit delay; we handle it

    print(f"Loaded table: {rows} rows x {cols} cols")
    print(f"Starting in {args.countdown:.1f}s… click the TOP-LEFT target cell now. (Failsafe: move mouse to a screen corner)")
    time.sleep(args.countdown)

    for r_idx, row in enumerate(table):
        for c_idx, val in enumerate(row):
            if args.clear:
                press('backspace', n=4, pause=args.delay)
            if val != "":
                paste_text(val, pause=args.delay)
            press('right', n=1, pause=args.delay)
        # go back to first column and down one row (except after last row)
        press('left', n=cols, pause=args.delay)
        if r_idx != rows - 1:
            press('down', n=1, pause=args.delay)

    print("Done.")


if __name__ == "__main__":
    main()
