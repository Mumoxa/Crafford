#!/usr/bin/env python3
import io, json, os, re
from pathlib import Path
from datetime import datetime
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload
from PIL import Image, ImageOps

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "assets" / "photos" / "google-drive"
JS = ROOT / "js" / "google-drive-contributions.js"
MANIFEST = ROOT / "data" / "google-drive-manifest.json"
SCOPES = ["https://www.googleapis.com/auth/drive.readonly"]
MONTHS = ["Januarie","Februarie","Maart","April","Mei","Junie","Julie","Augustus","September","Oktober","November","Desember"]
IMAGE_MIMES = {"image/jpeg","image/png","image/webp","image/gif","image/bmp","image/heic","image/heif"}
BATCH_SIZE = int(os.environ.get("GOOGLE_DRIVE_BATCH_SIZE", "40"))
MAX_SIDE = 1800
JPEG_QUALITY = 85


def safe_name(name):
    stem = Path(name).stem
    stem = re.sub(r"[^A-Za-z0-9._-]+", "-", stem).strip("-_") or "foto"
    return stem[:90]


def filename_date(name):
    patterns = [
        r"(?:IMG|PXL|PANO|MVIMG)[ _-]?(20\d{2})(\d{2})(\d{2})",
        r"(20\d{2})(\d{2})(\d{2})[_-]?\d{2,6}",
        r"(20\d{2})[-_.](\d{1,2})[-_.](\d{1,2})",
        r"\b(\d{1,2})-(\d{1,2})-(20\d{2})\b",
    ]
    for i, p in enumerate(patterns):
        m = re.search(p, name, re.I)
        if not m:
            continue
        try:
            vals = list(map(int, m.groups()))
            if i == 3:
                d, mo, y = vals
                return datetime(y, mo, d)
            y, mo, d = vals
            return datetime(y, mo, d)
        except ValueError:
            pass
    return None


def exif_date(path):
    try:
        with Image.open(path) as im:
            ex = im.getexif()
            raw = ex.get(36867) or ex.get(306)
            if raw:
                return datetime.strptime(str(raw)[:19], "%Y:%m:%d %H:%M:%S")
    except Exception:
        pass
    return None


def load_manifest():
    if not MANIFEST.exists():
        return {"files": {}}
    try:
        data = json.loads(MANIFEST.read_text(encoding="utf-8"))
        if not isinstance(data, dict) or not isinstance(data.get("files"), dict):
            raise ValueError("invalid manifest")
        return data
    except Exception:
        return {"files": {}}


def save_manifest(manifest):
    MANIFEST.parent.mkdir(parents=True, exist_ok=True)
    MANIFEST.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def list_files(service, folder_id):
    stack = [folder_id]
    while stack:
        parent = stack.pop()
        token = None
        while True:
            res = service.files().list(
                q=f"'{parent}' in parents and trashed=false",
                fields="nextPageToken,files(id,name,mimeType,modifiedTime,size)",
                pageToken=token,
                pageSize=1000,
                supportsAllDrives=True,
                includeItemsFromAllDrives=True,
            ).execute()
            for f in res.get("files", []):
                if f["mimeType"] == "application/vnd.google-apps.folder":
                    stack.append(f["id"])
                elif f["mimeType"] in IMAGE_MIMES:
                    yield f
            token = res.get("nextPageToken")
            if not token:
                break


def download_raw(service, file_id, temp_path):
    req = service.files().get_media(fileId=file_id)
    with open(temp_path, "wb") as fh:
        d = MediaIoBaseDownload(fh, req)
        done = False
        while not done:
            _, done = d.next_chunk()


def optimise_image(src, dest):
    with Image.open(src) as im:
        im = ImageOps.exif_transpose(im)
        if im.mode not in ("RGB", "L"):
            im = im.convert("RGB")
        if im.mode == "L":
            im = im.convert("RGB")
        im.thumbnail((MAX_SIDE, MAX_SIDE), Image.Resampling.LANCZOS)
        dest.parent.mkdir(parents=True, exist_ok=True)
        im.save(dest, "JPEG", quality=JPEG_QUALITY, optimize=True, progressive=True)


def sync_one(service, f):
    OUT.mkdir(parents=True, exist_ok=True)
    temp = OUT / (".tmp-" + f["id"])
    dest = OUT / f"{f['id']}-{safe_name(f['name'])}.jpg"
    download_raw(service, f["id"], temp)
    try:
        optimise_image(temp, dest)
    finally:
        temp.unlink(missing_ok=True)
    return dest


def write_js(manifest):
    groups = {}
    for file_id, meta in manifest["files"].items():
        rel = meta.get("path")
        if not rel:
            continue
        path = ROOT / rel
        if not path.exists():
            continue
        dt = filename_date(meta.get("name", "")) or exif_date(path)
        key = (dt.year, dt.month) if dt else None
        groups.setdefault(key, []).append((meta, path, dt))

    memories = []
    for key in sorted(groups, key=lambda k: (k is None, k or (9999, 99))):
        vals = groups[key]
        if key:
            y, m = key
            label = f"{MONTHS[m-1]} {y}"
            mid = f"drive-{y:04d}-{m:02d}"
            year = str(y)
            order = 5000 + m
        else:
            label = "Datum onbekend"
            mid = "drive-onbekend"
            year = ""
            order = 99500

        photos = []
        for meta, path, dt in sorted(vals, key=lambda x: x[0].get("name", "").lower()):
            photos.append({
                "src": path.relative_to(ROOT).as_posix(),
                "caption": "Uit die familie se Google Drive",
                "year": year,
                "alt": f"Familiefoto van Oupa Attie — {label}",
            })

        memories.append({
            "id": mid,
            "dateLabel": label,
            "year": year,
            "order": order,
            "era": "Gedeel deur die familie",
            "landscape": "family",
            "title": label if key else "Nog familieherinneringe",
            "story": "Foto’s wat deur die familie in die gedeelde Google Drive-vak gevoeg is.",
            "photos": photos,
        })

    JS.write_text(
        "/* Outomaties gegenereer uit die familie se Google Drive. */\n"
        "window.CRAFFORD_DRIVE = { memories: " + json.dumps(memories, ensure_ascii=False) + " };\n"
        "if (window.CRAFFORD && Array.isArray(window.CRAFFORD.memories)) { "
        "window.CRAFFORD.memories.push(...window.CRAFFORD_DRIVE.memories); }\n",
        encoding="utf-8",
    )


def main():
    raw = os.environ["GOOGLE_DRIVE_SERVICE_ACCOUNT"]
    folder = os.environ["GOOGLE_DRIVE_FOLDER_ID"]
    info = json.loads(raw)
    creds = service_account.Credentials.from_service_account_info(info, scopes=SCOPES)
    service = build("drive", "v3", credentials=creds, cache_discovery=False)

    remote = list(list_files(service, folder))
    remote.sort(key=lambda f: (f.get("modifiedTime", ""), f.get("name", "")))
    manifest = load_manifest()

    pending = []
    for f in remote:
        old = manifest["files"].get(f["id"])
        if not old or old.get("modifiedTime") != f.get("modifiedTime") or not (ROOT / old.get("path", "")).exists():
            pending.append(f)

    print(f"Google Drive: {len(remote)} image(s) found")
    print(f"Already synced: {len(remote) - len(pending)}")
    print(f"Pending: {len(pending)}")

    processed = 0
    for f in pending[:BATCH_SIZE]:
        try:
            dest = sync_one(service, f)
        except Exception as exc:
            print(f"Skipped {f['name']}: {exc}")
            continue
        manifest["files"][f["id"]] = {
            "name": f["name"],
            "modifiedTime": f.get("modifiedTime", ""),
            "path": dest.relative_to(ROOT).as_posix(),
        }
        processed += 1
        print("Synced:", f["name"])

    save_manifest(manifest)
    write_js(manifest)
    remaining = max(0, len(pending) - processed)
    print(f"Processed this run: {processed}")
    print(f"Remaining after this run: {remaining}")
    print(f"Generated {JS.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
