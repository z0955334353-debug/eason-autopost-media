"""把公開（知道連結可檢視）的雲端資料夾裡的新素材抓下來，做成「給 Claude 看的」縮圖表與資料。

用法：python import_drive.py <資料夾ID> [<資料夾ID> ...]
- 影片：每 1 秒擷取一張畫面，拼成一張有時間標記的縮圖表（inbox/<日期>/<檔名>.jpg）
        並記錄長度、解析度、是否有聲音（inbox/<日期>/<檔名>.json）
- 照片：縮到長邊 1600px 存到 inbox/<日期>/photos/
- 已處理過的檔案記在 manifest.json，不重複處理
原始影片不進 repo（太大），剪片時再用檔案 ID 重新下載。
"""
import html
import json
import re
import subprocess
import sys
import urllib.request
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parent.parent
MANIFEST = ROOT / "manifest.json"
TZ = ZoneInfo("Asia/Taipei")
UA = {"User-Agent": "Mozilla/5.0"}
VIDEO_EXT = (".mp4", ".mov", ".m4v", ".3gp", ".avi", ".mkv")
PHOTO_EXT = (".jpg", ".jpeg", ".png", ".heic", ".heif", ".webp")


def get(url):
    with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=120) as r:
        return r.read()


def list_folder(folder_id, depth=0):
    """用公開的 embeddedfolderview 頁面列出檔案（含子資料夾，最多 2 層）。"""
    page = get(f"https://drive.google.com/embeddedfolderview?id={folder_id}").decode("utf-8", "replace")
    out = []
    for m in re.finditer(r'<a href="([^"]+)"[^>]*>.*?<div class="flip-entry-title">(.*?)</div>', page, re.S):
        href, title = html.unescape(m.group(1)), html.unescape(m.group(2)).strip()
        fid = re.search(r"/(?:file/d|folders)/([A-Za-z0-9_-]+)", href)
        if not fid:
            continue
        if "/folders/" in href:
            if depth < 2:
                out += list_folder(fid.group(1), depth + 1)
        else:
            out.append({"id": fid.group(1), "name": title})
    return out


def download(fid, dest):
    url = f"https://drive.usercontent.google.com/download?id={fid}&export=download&confirm=t"
    subprocess.run(["curl", "-sSL", "-A", "Mozilla/5.0", "-o", str(dest), url], check=True)


def probe(path):
    r = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration:stream=codec_type,width,height:stream_tags=rotate",
                        "-of", "json", str(path)], capture_output=True, text=True)
    d = json.loads(r.stdout or "{}")
    streams = d.get("streams", [])
    v = next((s for s in streams if s.get("codec_type") == "video"), {})
    return {
        "duration": round(float(d.get("format", {}).get("duration", 0) or 0), 2),
        "width": v.get("width"), "height": v.get("height"),
        "has_audio": any(s.get("codec_type") == "audio" for s in streams),
    }


def contact_sheet(src, dest, duration):
    """每秒一格，5 欄，左上角標秒數。"""
    n = max(1, min(int(duration) + 1, 40))
    step = max(1.0, duration / n) if duration > 40 else 1.0
    vf = (f"fps=1/{step},scale=240:-2,"
          "drawtext=fontfile=/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf:"
          f"text='%{{eif\\:n*{step}\\:d}}s':x=6:y=6:fontsize=20:fontcolor=white:box=1:boxcolor=black@0.6,"
          f"tile=5x{(n + 4) // 5}:padding=4:margin=4")
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(src), "-frames:v", "1", "-vf", vf, str(dest)], check=True)


def main(folder_ids):
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8")) if MANIFEST.exists() else {}
    day = datetime.now(TZ).strftime("%Y%m%d")
    inbox = ROOT / "inbox" / day
    tmp = Path("/tmp/kz")
    tmp.mkdir(exist_ok=True)
    new = []
    for folder in folder_ids:
        for f in list_folder(folder):
            if f["id"] in manifest:
                continue
            name = f["name"]
            low = name.lower()
            if not low.endswith(VIDEO_EXT + PHOTO_EXT):
                manifest[f["id"]] = {"name": name, "skipped": "不是影片或照片"}
                continue
            src = tmp / f"{f['id']}{Path(low).suffix}"
            try:
                download(f["id"], src)
                kind = subprocess.run(["file", "-b", "--mime-type", str(src)], capture_output=True, text=True).stdout.strip()
                stem = re.sub(r"[^\w\-]+", "_", Path(name).stem)[:60] + "_" + f["id"][:6]
                if kind.startswith("video/"):
                    inbox.mkdir(parents=True, exist_ok=True)
                    info = probe(src)
                    contact_sheet(src, inbox / f"{stem}.jpg", info["duration"])
                    rec = {"id": f["id"], "name": name, "type": "video", **info,
                           "sheet": f"inbox/{day}/{stem}.jpg"}
                elif kind.startswith("image/"):
                    (inbox / "photos").mkdir(parents=True, exist_ok=True)
                    out = inbox / "photos" / f"{stem}.jpg"
                    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(src), "-vf",
                                    "scale='if(gt(iw,ih),min(1600,iw),-2)':'if(gt(iw,ih),-2,min(1600,ih))'", "-q:v", "3", str(out)], check=True)
                    rec = {"id": f["id"], "name": name, "type": "photo", "file": f"inbox/{day}/photos/{stem}.jpg"}
                else:
                    rec = {"id": f["id"], "name": name, "skipped": f"下載到的不是媒體檔（{kind}），資料夾可能沒開『知道連結可檢視』"}
                if "skipped" not in rec:
                    (inbox / f"{stem}.json").write_text(json.dumps(rec, ensure_ascii=False, indent=1), encoding="utf-8")
                    new.append(rec)
                manifest[f["id"]] = {"name": name, "imported": day, **{k: rec[k] for k in rec if k in ("type", "skipped")}}
            except Exception as e:  # noqa: BLE001
                print("失敗", name, e)
            finally:
                src.unlink(missing_ok=True)
    MANIFEST.write_text(json.dumps(manifest, ensure_ascii=False, indent=1), encoding="utf-8")
    summary = {"date": day, "new": new}
    (ROOT / "inbox" / "latest.json").write_text(json.dumps(summary, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"新素材 {len(new)} 個：影片 {sum(r['type']=='video' for r in new)}、照片 {sum(r['type']=='photo' for r in new)}")


if __name__ == "__main__":
    main(sys.argv[1:])
