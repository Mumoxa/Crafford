#!/usr/bin/env python3
import io, json, os, re
from pathlib import Path
from datetime import datetime
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "assets" / "photos" / "google-drive"
JS = ROOT / "js" / "google-drive-contributions.js"
SCOPES = ["https://www.googleapis.com/auth/drive.readonly"]
MONTHS = ["Januarie","Februarie","Maart","April","Mei","Junie","Julie","Augustus","September","Oktober","November","Desember"]
IMAGE_MIMES = {"image/jpeg","image/png","image/webp","image/gif","image/bmp","image/heic","image/heif"}

def safe_name(name):
    stem, ext = os.path.splitext(name)
    stem = re.sub(r"[^A-Za-z0-9._-]+", "-", stem).strip("-_") or "foto"
    ext = ext.lower() or ".jpg"
    return stem[:90] + ext

def filename_date(name):
    patterns = [
        r"(?:IMG|PXL|PANO|MVIMG)[ _-]?(20\d{2})(\d{2})(\d{2})",
        r"(20\d{2})(\d{2})(\d{2})[_-]?\d{2,6}",
        r"(20\d{2})[-_.](\d{1,2})[-_.](\d{1,2})",
    ]
    for p in patterns:
        m = re.search(p, name, re.I)
        if m:
            try: return datetime(*map(int, m.groups()))
            except ValueError: pass
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

def list_files(service, folder_id):
    stack = [folder_id]
    while stack:
        parent = stack.pop()
        token = None
        while True:
            res = service.files().list(
                q=f"'{parent}' in parents and trashed=false",
                fields="nextPageToken,files(id,name,mimeType,modifiedTime)",
                pageToken=token, pageSize=1000,
                supportsAllDrives=True, includeItemsFromAllDrives=True
            ).execute()
            for f in res.get("files", []):
                if f["mimeType"] == "application/vnd.google-apps.folder": stack.append(f["id"])
                elif f["mimeType"] in IMAGE_MIMES: yield f
            token = res.get("nextPageToken")
            if not token: break

def download(service, f):
    OUT.mkdir(parents=True, exist_ok=True)
    path = OUT / f"{f['id']}-{safe_name(f['name'])}"
    req = service.files().get_media(fileId=f["id"])
    with open(path, "wb") as fh:
        d = MediaIoBaseDownload(fh, req)
        done = False
        while not done: _, done = d.next_chunk()
    return path

def write_js(items):
    groups = {}
    for f, path in items:
        dt = filename_date(f["name"]) or exif_date(path)
        key = (dt.year, dt.month) if dt else None
        groups.setdefault(key, []).append((f, path, dt))
    memories = []
    for key in sorted(groups, key=lambda k: (k is None, k or (9999, 99))):
        vals = groups[key]
        if key:
            y, m = key; label = f"{MONTHS[m-1]} {y}"; mid=f"drive-{y:04d}-{m:02d}"; year=str(y); order=5000+m
        else:
            label="Datum onbekend"; mid="drive-onbekend"; year=""; order=99500
        photos=[]
        for f,path,dt in sorted(vals, key=lambda x:x[0]["name"].lower()):
            rel=path.relative_to(ROOT).as_posix()
            photos.append({"src":rel,"caption":"Uit die familie se Google Drive","year":year,"alt":f"Familiefoto van Oupa Attie — {label}"})
        memories.append({"id":mid,"dateLabel":label,"year":year,"order":order,"era":"Gedeel deur die familie","landscape":"family","title":label if key else "Nog familieherinneringe","story":"Foto’s wat deur die familie in die gedeelde Google Drive-vak gevoeg is.","photos":photos})
    JS.write_text("/* Outomaties gegenereer uit die familie se Google Drive. */\nwindow.CRAFFORD_DRIVE = { memories: " + json.dumps(memories, ensure_ascii=False) + " };\nif (window.CRAFFORD && Array.isArray(window.CRAFFORD.memories)) { window.CRAFFORD.memories.push(...window.CRAFFORD_DRIVE.memories); }\n", encoding="utf-8")

def main():
    raw = os.environ["GOOGLE_DRIVE_SERVICE_ACCOUNT"]
    folder = os.environ["GOOGLE_DRIVE_FOLDER_ID"]
    info = json.loads(raw)
    creds = service_account.Credentials.from_service_account_info(info, scopes=SCOPES)
    service = build("drive", "v3", credentials=creds, cache_discovery=False)
    files = list(list_files(service, folder))
    print(f"Google Drive: {len(files)} image(s) found")
    items=[]
    for f in files:
        p=download(service,f); items.append((f,p)); print("Downloaded:",f["name"])
    write_js(items)
    print(f"Generated {JS.relative_to(ROOT)}")

if __name__ == "__main__": main()
