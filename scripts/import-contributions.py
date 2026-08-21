#!/usr/bin/env python3
"""
Voer familie-bydraes in: uploads/ -> assets/ + js/contributions.js

* Die 21 bekend-gename foto's (die invoer-kaart in import-photos.py) gaan
  direk na hulle plekke op die tydlyn in js/content.js.
* Enige ANDER foto, video of stemnota word outomaties gesorteer:
  - datum uit die lêernaam (IMG-20210412-WA0020, 20120804_100209, 04-08-2012 ...)
  - anders uit die foto se EXIF-datum
  - anders "Datum onbekend" agteraan
* Bydraes word per maand gegroepeer as "Gedeel deur die familie" op die tydlyn.
* EXIF-draaiing (onderstebo/sywaarts) word reggedraai indien Pillow beskikbaar is.
* Gesigte en prente word NOOIT herskep of gestileer nie - net gekopieer (of reggedraai).

Gebruik:  python3 scripts/import-contributions.py [--src GIDS ...] [--dry-run]
"""
import importlib.util
import os
import re
import shutil
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
SCRIPTS = os.path.dirname(os.path.abspath(__file__))

# Hergebruik die naam-kaart van die oorspronklike invoer-skrip.
_spec = importlib.util.spec_from_file_location(
    "import_photos", os.path.join(SCRIPTS, "import-photos.py")
)
import_photos = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(import_photos)
MAP = import_photos.MAP

DEFAULT_SOURCES = [
    os.path.join(os.path.expanduser("~"), "uploads"),
    os.path.join(ROOT, "uploads"),
    "/tmp/uploads",
]

PHOTO_EXT = {".jpg", ".jpeg", ".png", ".webp", ".gif", ".bmp"}
VIDEO_EXT = {".mp4", ".m4v", ".mov", ".webm", ".3gp", ".avi", ".mkv"}
VOICE_EXT = {".mp3", ".m4a", ".wav", ".aac", ".ogg", ".opus", ".amr"}
SKIP_FILES = {"leesmy.txt", "readme.txt", "readme.md", ".keep", ".ds_store", "thumbs.db"}

MAANDE = [
    "Januarie", "Februarie", "Maart", "April", "Mei", "Juni",
    "Julie", "Augustus", "September", "Oktober", "November", "Desember",
]

DATE_PATTERNS = [
    # IMG-20210412-WA0020 / VID-20220130-0012 / PXL_20211107 / MVIMG-20210910...
    re.compile(r"(?:IMG|VID|PXL|PANO|MVIMG)[ _-]?(20\d{2})(\d{2})(\d{2})", re.I),
    # 20120804_100209 / 20120804_100209(2) / 20171209_125058
    re.compile(r"(20\d{2})(\d{2})(\d{2})[_\-]?\d{2,6}"),
    # 2021-04-12 / 2021.04.12
    re.compile(r"(20\d{2})[.\-](\d{2})[.\-](\d{2})"),
    # 04-08-2012 of 4-8-2012 (dag-maand-jaar)
    re.compile(r"\b(\d{1,2})-(\d{1,2})-(20\d{2})\b"),
]


def try_pillow():
    try:
        from PIL import Image, ImageOps  # noqa: F401
        import PIL  # noqa: F401
        return True
    except Exception:
        return False


HAS_PIL = try_pillow()


def parse_date_from_name(name):
    for pat in DATE_PATTERNS:
        m = pat.search(name)
        if not m:
            continue
        g = [int(x) for x in m.groups() if x]
        if len(g) == 3 and pat is DATE_PATTERNS[3]:
            d, mo, y = g  # dag-maand-jaar
        elif len(g) == 3:
            y, mo, d = g
        else:
            continue
        if 2000 <= y <= 2099 and 1 <= mo <= 12 and 1 <= d <= 31:
            return y, mo, d
    return None


def parse_date_from_exif(path):
    if not HAS_PIL:
        return None
    try:
        from PIL import Image
        with Image.open(path) as im:
            exif = im.getexif()
            raw = exif.get(306)  # DateTime
            if not raw:
                return None
            m = re.match(r"(20\d{2}):(\d{2}):(\d{2})", str(raw))
            if not m:
                return None
            y, mo, d = int(m.group(1)), int(m.group(2)), int(m.group(3))
            if 1 <= mo <= 12 and 1 <= d <= 31:
                return y, mo, d
    except Exception:
        return None
    return None


def exif_orientation(path):
    if not HAS_PIL:
        return None
    try:
        from PIL import Image
        with Image.open(path) as im:
            return im.getexif().get(274)  # Orientation
    except Exception:
        return None


def slugify(name):
    base = os.path.splitext(name)[0].lower()
    base = re.sub(r"[^a-z0-9]+", "-", base).strip("-")
    return (base[:40] or "bydrae")


def copy_media(src, dest, dry=False):
    """Kopieer; draai slegs reg as EXIF sê die prent is gedraai (3/6/8)."""
    ori = exif_orientation(src)
    rotated = False
    if not dry:
        os.makedirs(os.path.dirname(dest), exist_ok=True)
        if ori in (3, 6, 8) and HAS_PIL:
            try:
                from PIL import Image, ImageOps
                with Image.open(src) as im:
                    im = ImageOps.exif_transpose(im)
                    if im.mode not in ("RGB", "L"):
                        im = im.convert("RGB")
                    im.save(dest, quality=92)
                rotated = True
            except Exception:
                shutil.copy2(src, dest)
        else:
            shutil.copy2(src, dest)
    return rotated


def main():
    args = sys.argv[1:]
    dry = "--dry-run" in args
    srcs = []
    for i, a in enumerate(args):
        if a == "--src" and i + 1 < len(args):
            srcs.append(os.path.abspath(args[i + 1]))
    if not srcs:
        srcs = DEFAULT_SOURCES

    # 1) Versamel lêers
    files = []
    for folder in srcs:
        if not os.path.isdir(folder):
            continue
        for fn in sorted(os.listdir(folder)):
            p = os.path.join(folder, fn)
            if not os.path.isfile(p):
                continue
            if fn.lower() in SKIP_FILES or fn.startswith("."):
                continue
            files.append((fn, p))

    mapped, photos, videos, voices, skipped = [], [], [], [], []
    for fn, path in files:
        lower = fn.lower()
        ext = os.path.splitext(lower)[1]
        stem = os.path.splitext(fn)[0]
        # Ken die 21 oorspronklikes direk aan die tydlyn se name toe
        hit = MAP.get(fn) or next((dest for orig, dest in MAP.items() if orig.lower() == lower), None)
        if hit:
            dest = os.path.join(ROOT, "assets", "photos", hit)
            rotated = copy_media(path, dest, dry)
            mapped.append((fn, hit, rotated))
            continue
        if ext in PHOTO_EXT:
            photos.append((fn, path, ext))
        elif ext in VIDEO_EXT:
            videos.append((fn, path, ext))
        elif ext in VOICE_EXT:
            voices.append((fn, path, ext))
        else:
            skipped.append(fn)

    # 2) Kategoriseer die res volgens datum
    def dated(items):
        out = []
        for fn, path, ext in items:
            d = parse_date_from_name(fn) or parse_date_from_exif(path)
            out.append((d, fn, path, ext))
        return out

    groups = {}  # (jaar, maand) -> [items]; None -> onbekend

    def bucket(item):
        d = item[0]
        key = (d[0], d[1]) if d else None
        groups.setdefault(key, []).append(item)

    for item in dated(photos) + dated(videos) + dated(voices):
        bucket(item)

    def dest_path(item, kind):
        d, fn, path, ext = item
        tag = ("%04d%02d%02d" % (d[0], d[1], d[2])) if d else "onbekend"
        return os.path.join(ROOT, "assets", kind, "familie-%s-%s%s" % (tag, slugify(fn), ext))

    memories = []
    for key in sorted(groups, key=lambda k: (k is None, k or (0, 0))):
        items = sorted(groups[key], key=lambda x: x[1].lower())
        if key:
            jaar, maand = key
            date_label = "%s %d" % (MAANDE[maand - 1], jaar)
            mem_id = "familie-%04d-%02d" % (jaar, maand)
            order = 1000 + maand
            year = str(jaar)
        else:
            date_label = "Datum onbekend"
            mem_id = "familie-onbekend"
            order = 99000
            year = ""

        m = {
            "id": mem_id,
            "dateLabel": date_label,
            "year": year,
            "order": order,
            "era": "Gedeel deur die familie",
            "landscape": "family",
            "title": date_label if key else "’n Laai vol herinneringe",
            "story": "Gedeel deur iemand wat hom geken het — nog ’n hoekie van sy lewe wat bygehou word.",
            "photos": [],
            "videos": [],
            "voices": [],
        }
        for item in items:
            d, fn, path, ext = item
            if ext in PHOTO_EXT:
                rel = os.path.relpath(dest_path(item, "photos"), ROOT).replace("\\", "/")
                rotated = copy_media(path, os.path.join(ROOT, rel), dry)
                alt = "Familiefoto van Oupa Attie" + (" — " + date_label if key else "")
                m["photos"].append({
                    "src": rel,
                    "caption": "Gedeel deur die familie",
                    "year": year,
                    "alt": alt,
                })
            elif ext in VIDEO_EXT:
                rel = os.path.relpath(dest_path(item, "videos"), ROOT).replace("\\", "/")
                if not dry:
                    os.makedirs(os.path.dirname(os.path.join(ROOT, rel)), exist_ok=True)
                    shutil.copy2(path, os.path.join(ROOT, rel))
                m["videos"].append({"src": rel, "title": "Video — " + date_label})
            else:
                rel = os.path.relpath(dest_path(item, "voices"), ROOT).replace("\\", "/")
                if not dry:
                    os.makedirs(os.path.dirname(os.path.join(ROOT, rel)), exist_ok=True)
                    shutil.copy2(path, os.path.join(ROOT, rel))
                m["voices"].append({"src": rel, "title": "Stemnota — " + date_label,
                                    "date": date_label, "note": "Gedeel deur die familie"})
        if m["photos"] or m["videos"] or m["voices"]:
            memories.append(m)

    # 3) Skryf js/contributions.js
    out_path = os.path.join(ROOT, "js", "contributions.js")
    if not dry:
        lines = []
        lines.append("/* ============================================================")
        lines.append(" *  FAMILIE-BYDRAES — outomaties gegenereer")
        lines.append(" *  Moenie met die hand sit nie. Laai lêers in uploads/ en")
        lines.append(" *  loop:  python3 scripts/import-contributions.py")
        lines.append(" * ============================================================ */")
        lines.append("")
        lines.append("window.CRAFFORD_CONTRIB = { memories: [")
        for m in memories:
            lines.append("  {")
            lines.append('    id: "%s",' % m["id"])
            lines.append('    dateLabel: "%s",' % m["dateLabel"])
            lines.append('    year: "%s",' % m["year"])
            lines.append("    order: %d," % m["order"])
            lines.append('    era: "%s",' % m["era"])
            lines.append('    landscape: "%s",' % m["landscape"])
            lines.append('    title: "%s",' % m["title"].replace('"', '\\"'))
            lines.append('    story: "%s",' % m["story"])
            for key, label in (("photos", None), ("videos", None), ("voices", None)):
                if m[key]:
                    lines.append("    %s: [" % key)
                    for entry in m[key]:
                        lines.append("      {")
                        for k, v in entry.items():
                            if isinstance(v, (int, float)):
                                lines.append("        %s: %s," % (k, v))
                            else:
                                lines.append('        %s: "%s",' % (k, str(v).replace('"', '\\"')))
                        lines.append("      },")
                    lines.append("    ],")
            lines.append("  },")
        lines.append("] };")
        lines.append("")
        with open(out_path, "w", encoding="utf-8") as f:
            f.write("\n".join(lines))

    # 4) Verslag
    print("Bekend-gename foto's ingevoer: %d" % len(mapped))
    for fn, dest, rot in mapped:
        print("  %s -> assets/photos/%s%s" % (fn, dest, "  (reggedraai)" if rot else ""))
    if not mapped:
        print("  (geen van die 21 oorspronklike name gevind nie)")
    print("Bydraes ingevoer: %d foto's, %d video's, %d stemnotas" % (
        len(photos), len(videos), len(voices)))
    for m in memories:
        print("  %s: %d foto's, %d video's, %d stemnotas" % (
            m["id"], len(m["photos"]), len(m["videos"]), len(m["voices"])))
    if skipped:
        print("Oorgeslaan (nie 'n media-lêer nie): %s" % ", ".join(skipped))
    print("js/contributions.js geskryf met %d herinnering-groepe" % len(memories))
    if dry:
        print("(droogloop - niks geskryf nie)")


if __name__ == "__main__":
    main()
