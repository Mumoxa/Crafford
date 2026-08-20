#!/usr/bin/env python3
"""Kopieer opgelaaide familie-foto’s na assets/photos met web-vriendelike name."""
import os
import shutil

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
DEST = os.path.join(ROOT, "assets", "photos")

MAP = {
    "4x4.jpg": "4x4-01.jpg",
    "4x4 2.jpg": "4x4-02.jpg",
    "4x4 3.jpg": "4x4-03.jpg",
    "4x4 christo.jpg": "4x4-see-christo.jpg",
    "101_0852.jpg": "dans-wink.jpg",
    "101_0858.jpg": "dans-lag.jpg",
    "101_0859.jpg": "dans-saam.jpg",
    "347.JPG": "fiets-op.jpg",
    "348.JPG": "fiets-twee.jpg",
    "351.JPG": "fiets-vmax.jpg",
    "353.JPG": "fiets-gesin.jpg",
    "364.JPG": "fiets-pad.jpg",
    "365.JPG": "fiets-pyp.jpg",
    "20120630_215454.jpg": "kombuis-2012.jpg",
    "20120804_100209.jpg": "rit-1stop-2012.jpg",
    "20120804_100222.jpg": "rit-engen-2012.jpg",
    "20120804_200556.jpg": "kampvuur-2012.jpg",
    "20120804_213805.jpg": "kamp-nag-2012.jpg",
    "20171209_125058.jpg": "rugby-2017.jpg",
    "20210412_205854 (2).jpg": "portret-2021.jpg",
    "IMG-20161103-WA0009.jpg": "kamp-tent-2016.jpg",
}

SEARCH = [
    os.path.join(os.path.expanduser("~"), "uploads"),
    os.path.join(ROOT, "uploads"),
    "/tmp/uploads",
]


def find_source(name):
    for folder in SEARCH:
        if not os.path.isdir(folder):
            continue
        direct = os.path.join(folder, name)
        if os.path.isfile(direct):
            return direct
        lower = name.lower()
        for fn in os.listdir(folder):
            if fn.lower() == lower:
                return os.path.join(folder, fn)
    return None


def main():
    os.makedirs(DEST, exist_ok=True)
    copied = 0
    missing = []
    for src_name, dest_name in MAP.items():
        src = find_source(src_name)
        if not src:
            missing.append(src_name)
            continue
        dest = os.path.join(DEST, dest_name)
        shutil.copy2(src, dest)
        copied += 1
        print("ok", src_name, "->", dest_name)
    print("copied", copied, "missing", len(missing))
    for m in missing:
        print(" missing:", m)


if __name__ == "__main__":
    main()
