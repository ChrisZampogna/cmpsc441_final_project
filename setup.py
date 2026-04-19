import argparse
import gzip
import json
import shutil
import sqlite3
import urllib.request
from pathlib import Path

URL = "https://kaikki.org/dictionary/raw-wiktextract-data.jsonl.gz"
RAW_DIR = Path("data/raw")
GEN_DIR = Path("data/generated")
GZ_PATH = RAW_DIR / "raw-wiktextract-data.jsonl.gz"
JSONL_PATH = RAW_DIR / "raw-wiktextract-data.jsonl"
DB_PATH = GEN_DIR / "wiktionary.db"


def download(force: bool) -> None:
    if GZ_PATH.exists() and not force:
        print(f"[download] {GZ_PATH} already exists, skipping. Use --force to re-download.")
        return

    RAW_DIR.mkdir(parents=True, exist_ok=True)
    print(f"[download] Downloading {URL} ...")

    def progress(count, block_size, total):
        mb = count * block_size / 1024 / 1024
        print(f"\r[download] {mb:.1f} MB downloaded", end="", flush=True)

    urllib.request.urlretrieve(URL, GZ_PATH, reporthook=progress)
    print()
    print(f"[download] Saved to {GZ_PATH}")


def extract(force: bool) -> None:
    if JSONL_PATH.exists() and not force:
        print(f"[extract] {JSONL_PATH} already exists, skipping. Use --force to re-extract.")
        return

    if not GZ_PATH.exists():
        raise FileNotFoundError(f"{GZ_PATH} not found. Run download step first.")

    print(f"[extract] Extracting {GZ_PATH} ...")

    with gzip.open(GZ_PATH, "rb") as f_in, open(JSONL_PATH, "wb") as f_out:
        written = 0
        while chunk := f_in.read(1024 * 1024):
            f_out.write(chunk)
            written += len(chunk)
            mb = written / 1024 / 1024
            print(f"\r[extract] {mb:.1f} MB extracted", end="", flush=True)

    print()
    print(f"[extract] Extracted to {JSONL_PATH}")


def build_db(force: bool) -> None:
    if DB_PATH.exists() and not force:
        print(f"[db] {DB_PATH} already exists, skipping. Use --force to rebuild.")
        return

    if not JSONL_PATH.exists():
        raise FileNotFoundError(f"{JSONL_PATH} not found. Run extract step first.")

    GEN_DIR.mkdir(parents=True, exist_ok=True)

    if DB_PATH.exists():
        DB_PATH.unlink()

    print(f"[db] Building SQLite database at {DB_PATH} ...")

    con = sqlite3.connect(DB_PATH)
    cur = con.cursor()
    cur.execute("PRAGMA journal_mode = WAL")
    cur.execute("PRAGMA synchronous = NORMAL")
    cur.execute("""
        CREATE TABLE entries (
            word TEXT NOT NULL,
            pos  TEXT NOT NULL,
            raw  TEXT NOT NULL
        )
    """)
    cur.execute("CREATE INDEX idx_word_pos ON entries (word, pos)")

    batch = []
    batch_size = 10_000
    row_count = 0

    with open(JSONL_PATH, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                entry = json.loads(line)
            except json.JSONDecodeError:
                continue

            word = entry.get("word")
            pos = entry.get("pos")
            if word and pos:
                batch.append((word, pos, line))

            if len(batch) >= batch_size:
                cur.executemany("INSERT INTO entries VALUES (?, ?, ?)", batch)
                row_count += len(batch)
                batch.clear()
                print(f"\r[db] {row_count:,} entries inserted", end="", flush=True)

    if batch:
        cur.executemany("INSERT INTO entries VALUES (?, ?, ?)", batch)
        row_count += len(batch)

    print(f"\r[db] {row_count:,} entries inserted")
    con.commit()
    con.close()
    print()
    print(f"[db] Database built at {DB_PATH}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Set up wiktionary data for the project.")
    parser.add_argument(
        "--force",
        action="store_true",
        help="Force re-download, re-extract, and rebuild the database even if files already exist.",
    )
    args = parser.parse_args()

    download(args.force)
    extract(args.force)
    build_db(args.force)
    print("[setup] Done.")


if __name__ == "__main__":
    main()
