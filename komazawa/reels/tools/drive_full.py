"""把公開雲端資料夾（含子資料夾）的檔案原檔照原樣抓下來備用（不縮圖）。
用法：python drive_full.py <資料夾ID> <輸出資料夾>
"""
import html, re, subprocess, sys, urllib.request
from pathlib import Path
UA = {"User-Agent": "Mozilla/5.0"}
def get(u):
    with urllib.request.urlopen(urllib.request.Request(u, headers=UA), timeout=120) as r: return r.read()
def walk(fid, rel="", depth=0):
    page = get(f"https://drive.google.com/embeddedfolderview?id={fid}").decode("utf-8", "replace")
    for m in re.finditer(r'<a href="([^"]+)"[^>]*>.*?<div class="flip-entry-title">(.*?)</div>', page, re.S):
        href, title = html.unescape(m.group(1)), html.unescape(m.group(2)).strip()
        i = re.search(r"/(?:file/d|folders)/([A-Za-z0-9_-]+)", href)
        if not i: continue
        if "/folders/" in href:
            if depth < 3: yield from walk(i.group(1), f"{rel}{title}/", depth + 1)
        else:
            yield i.group(1), rel + title
out = Path(sys.argv[2]); n = 0
for fid, name in walk(sys.argv[1]):
    dest = out / name
    if dest.exists(): continue
    dest.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(["curl", "-sSL", "-A", "Mozilla/5.0", "-o", str(dest),
                    f"https://drive.usercontent.google.com/download?id={fid}&export=download&confirm=t"], check=True)
    kind = subprocess.run(["file", "-b", str(dest)], capture_output=True, text=True).stdout.strip()
    print(name, dest.stat().st_size, kind[:80]); n += 1
print("共下載", n, "個")
