#!/usr/bin/env python3
import json, os, re
from pathlib import Path
from datetime import datetime
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload
from PIL import Image, ImageOps

ROOT = Path(__file__).resolve().parents[1]
PHOTO_OUT = ROOT / "assets" / "photos" / "google-drive"
VOICE_OUT = ROOT / "assets" / "voices" / "google-drive"
JS = ROOT / "js" / "google-drive-contributions.js"
MANIFEST = ROOT / "data" / "google-drive-manifest.json"
SCOPES = ["https://www.googleapis.com/auth/drive.readonly"]
MONTHS = ["Januarie","Februarie","Maart","April","Mei","Junie","Julie","Augustus","September","Oktober","November","Desember"]
IMAGE_MIMES = {"image/jpeg","image/png","image/webp","image/gif","image/bmp","image/heic","image/heif"}
AUDIO_MIMES = {
    "audio/mpeg", "audio/mp3", "audio/mp4", "audio/x-m4a", "audio/m4a",
    "audio/wav", "audio/x-wav", "audio/aac", "audio/ogg", "application/ogg",
    "audio/opus", "audio/amr", "audio/3gpp", "audio/3gpp2",
}
AUDIO_EXTS = {".oga", ".ogg", ".opus", ".m4a", ".mp3", ".wav", ".aac", ".amr", ".3gp", ".3gpp"}
BATCH_SIZE = int(os.environ.get("GOOGLE_DRIVE_BATCH_SIZE", "40"))
MAX_SIDE = 1800
JPEG_QUALITY = 85


def safe_stem(name):
    stem = Path(name).stem
    stem = re.sub(r"[^A-Za-z0-9._-]+", "-", stem).strip("-_") or "media"
    return stem[:90]


def filename_date(name):
    patterns = [
        r"(?:IMG|VID|PXL|PANO|MVIMG)[ _-]?(20\d{2})(\d{2})(\d{2})",
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


def media_kind(f):
    mime = (f.get("mimeType") or "").lower()
    ext = Path(f.get("name", "")).suffix.lower()
    if mime in IMAGE_MIMES or mime.startswith("image/"):
        return "photo"
    if mime in AUDIO_MIMES or mime.startswith("audio/") or ext in AUDIO_EXTS:
        return "voice"
    return None


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
                elif media_kind(f):
                    yield f
            token = res.get("nextPageToken")
            if not token:
                break


def download_raw(service, file_id, dest):
    dest.parent.mkdir(parents=True, exist_ok=True)
    req = service.files().get_media(fileId=file_id)
    with open(dest, "wb") as fh:
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
    kind = media_kind(f)
    if kind == "photo":
        PHOTO_OUT.mkdir(parents=True, exist_ok=True)
        temp = PHOTO_OUT / (".tmp-" + f["id"])
        dest = PHOTO_OUT / f"{f['id']}-{safe_stem(f['name'])}.jpg"
        download_raw(service, f["id"], temp)
        try:
            optimise_image(temp, dest)
        finally:
            temp.unlink(missing_ok=True)
        return kind, dest

    ext = Path(f.get("name", "")).suffix.lower()
    if ext not in AUDIO_EXTS:
        ext = ".ogg" if (f.get("mimeType") or "").lower() in {"audio/ogg", "application/ogg", "audio/opus"} else ".m4a"
    VOICE_OUT.mkdir(parents=True, exist_ok=True)
    dest = VOICE_OUT / f"{f['id']}-{safe_stem(f['name'])}{ext}"
    download_raw(service, f["id"], dest)
    return "voice", dest


def write_js(manifest):
    groups = {}
    for file_id, meta in manifest["files"].items():
        rel = meta.get("path")
        if not rel:
            continue
        path = ROOT / rel
        if not path.exists():
            continue
        kind = meta.get("kind") or ("voice" if "/voices/" in rel else "photo")
        dt = filename_date(meta.get("name", ""))
        if not dt and kind == "photo":
            dt = exif_date(path)
        key = (dt.year, dt.month) if dt else None
        groups.setdefault(key, []).append((meta, path, dt, kind))

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
        voices = []
        for meta, path, dt, kind in sorted(vals, key=lambda x: x[0].get("name", "").lower()):
            rel = path.relative_to(ROOT).as_posix()
            if kind == "voice":
                voices.append({
                    "src": rel,
                    "title": Path(meta.get("name", "Stemnota")).stem,
                    "date": label,
                    "note": "Uit die familie se Google Drive",
                })
            else:
                photos.append({
                    "src": rel,
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
            "story": "Foto’s en stemnotas wat deur die familie in die gedeelde Google Drive-vak gevoeg is.",
            "photos": photos,
            "voices": voices,
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
        expected_kind = media_kind(f)
        if (
            not old
            or old.get("modifiedTime") != f.get("modifiedTime")
            or old.get("kind", expected_kind) != expected_kind
            or not (ROOT / old.get("path", "")).exists()
        ):
            pending.append(f)

    photos_found = sum(1 for f in remote if media_kind(f) == "photo")
    voices_found = sum(1 for f in remote if media_kind(f) == "voice")
    print(f"Google Drive: {photos_found} photo(s), {voices_found} voice note(s) found")
    print(f"Already synced: {len(remote) - len(pending)}")
    print(f"Pending: {len(pending)}")

    processed = 0
    for f in pending[:BATCH_SIZE]:
        try:
            kind, dest = sync_one(service, f)
        except Exception as exc:
            print(f"Skipped {f['name']}: {exc}")
            continue
        manifest["files"][f["id"]] = {
            "name": f["name"],
            "modifiedTime": f.get("modifiedTime", ""),
            "path": dest.relative_to(ROOT).as_posix(),
            "kind": kind,
        }
        processed += 1
        print(f"Synced {kind}:", f["name"])

    save_manifest(manifest)
    write_js(manifest)
    remaining = max(0, len(pending) - processed)
    print(f"Processed this run: {processed}")
    print(f"Remaining after this run: {remaining}")
    print(f"Generated {JS.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
