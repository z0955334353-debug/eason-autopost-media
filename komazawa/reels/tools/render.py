"""依剪輯單（edl/*.json）剪出 1080x1920 的 Reels，輸出到 out/。

剪輯單格式：
{
  "slug": "20261104-kansai",                       # 檔名
  "hook": {"title": "黃色大標", "sub": "白色副標"},   # 開頭 2.5 秒的標題（無底色、白字黑邊），選填
  "captions": [{"start": 9.5, "end": 12.0, "text": "糖先下鍋"}],   # 畫面中的字（約 7 成高度），選填
  "end_text": ["最後入座 00:30", "今晚要不要來一鍋？"],             # 疊在最後 2.4 秒，選填
  "pin": [{"text": "台中北區", "color": "white"}, {"text": "開到半夜的壽喜燒", "color": "0xF5C518"}],  # 抖音版：整支置頂大字，選填
  "caption_y": 0.62, "caption_size": 72,             # 字幕高度（畫面比例）與字級，選填
  "clips": [{"id": "雲端檔案ID", "start": 1.5, "end": 6.0, "speed": 1.0},
            {"photo": "komazawa/pro/2V1A6971.jpg", "dur": 0.6}],   # 照片：repo 內路徑，會慢慢推近
  "keep_audio": true,                               # 保留現場聲音
  "logo": false                                     # 右下角小 logo（預設不放）
}
舊格式的 "title" 會當成 hook 的大標（不再畫上方的色塊標題列）。
長度建議 25～35 秒，每 2～3 秒換一個畫面。
"""
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
FONT = "/usr/share/fonts/opentype/noto/NotoSansCJK-Black.ttc"
if not Path(FONT).exists():
    FONT = "/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc"
LOGO = ROOT.parent.parent / "komazawa-helper" / "public" / "icon.png"
W, H = 1080, 1920
TONEMAP = ("zscale=t=linear:npl=100,format=gbrpf32le,zscale=p=bt709,tonemap=tonemap=hable:desat=0,"
           "zscale=t=bt709:m=bt709:r=tv,format=yuv420p")
COLOR = ["-colorspace", "bt709", "-color_primaries", "bt709", "-color_trc", "bt709"]


def run(cmd, check=True):
    print(" ".join(map(str, cmd))[:300])
    return subprocess.run(cmd, check=check)


def probe(src, entries):
    return subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries", entries, "-of", "csv=p=0", str(src)],
                          capture_output=True, text=True).stdout.strip()


def esc(t):
    return str(t).replace("\\", "\\\\").replace(":", "\\:").replace("'", "’").replace("%", "\\%")


def text(t, size, color, y, start, end, border=6):
    return (f"drawtext=fontfile={FONT}:text='{esc(t)}':fontsize={size}:fontcolor={color}:borderw={border}:bordercolor=black@0.85:"
            f"x=(w-text_w)/2:y={y}:enable='between(t,{start:.2f},{end:.2f})'")


def main(edl_path):
    e = json.loads(Path(edl_path).read_text(encoding="utf-8"))
    tmp = Path("/tmp/kzr")
    tmp.mkdir(exist_ok=True)
    parts = []
    repo = ROOT.parent.parent
    for i, c in enumerate(e["clips"]):
        out = tmp / f"part{i}.mp4"
        if c.get("photo"):
            dur = float(c.get("dur", 0.8))
            frames = int(dur * 30)
            vf = (f"scale={W*2}:{H*2}:force_original_aspect_ratio=increase,crop={W*2}:{H*2},"
                  f"zoompan=z='1+0.04*on/{frames}':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d={frames}:s={W}x{H}:fps=30,setsar=1")
            run(["ffmpeg", "-v", "error", "-y", "-i", str(repo / c["photo"]), "-f", "lavfi", "-t", str(dur), "-i", "anullsrc=r=48000:cl=stereo",
                 "-vf", vf, "-frames:v", str(frames), "-map", "0:v", "-map", "1:a", "-c:v", "libx264", "-preset", "medium", "-crf", "16",
                 "-pix_fmt", "yuv420p", *COLOR, "-c:a", "aac", "-ar", "48000", "-ac", "2", "-shortest", str(out)])
            parts.append(out)
            continue
        src = tmp / f"src_{c['id']}"
        if not src.exists():
            run(["curl", "-sSL", "-A", "Mozilla/5.0", "-o", str(src),
                 f"https://drive.usercontent.google.com/download?id={c['id']}&export=download&confirm=t"])
        has_audio = "audio" in subprocess.run(["ffprobe", "-v", "error", "-show_entries", "stream=codec_type", "-of", "csv=p=0", str(src)],
                                              capture_output=True, text=True).stdout
        hdr = probe(src, "stream=color_transfer") in ("arib-std-b67", "smpte2084")
        speed = float(c.get("speed", 1.0))
        dur = float(c["end"]) - float(c["start"])
        base = f"scale={W}:{H}:force_original_aspect_ratio=increase:flags=lanczos,crop={W}:{H},setsar=1,fps=30,setpts=PTS/{speed}"
        cmd = ["ffmpeg", "-v", "error", "-y", "-ss", str(c["start"]), "-t", str(dur), "-i", str(src)]
        if not (has_audio and e.get("keep_audio", True)):
            cmd += ["-f", "lavfi", "-t", str(dur / speed), "-i", "anullsrc=r=48000:cl=stereo"]
            amap = ["-map", "0:v:0", "-map", "1:a:0"]
        else:
            amap = ["-map", "0:v:0", "-map", "0:a:0", "-af", f"atempo={speed}" if speed != 1.0 else "anull"]
        tail = [*amap, "-c:v", "libx264", "-preset", "medium", "-crf", "16", "-pix_fmt", "yuv420p", *COLOR,
                "-c:a", "aac", "-ar", "48000", "-ac", "2", "-shortest", str(out)]
        ok = False
        if hdr:  # iPhone 的 HDR（HLG）影片要轉成一般色彩，不然上傳後會變灰變淡
            ok = run(cmd + ["-vf", f"{TONEMAP},{base}"] + tail, check=False).returncode == 0
        if not ok:
            run(cmd + ["-vf", base] + tail)
        parts.append(out)
    lst = tmp / "list.txt"
    lst.write_text("".join(f"file '{p}'\n" for p in parts))
    joined = tmp / "joined.mp4"
    run(["ffmpeg", "-v", "error", "-y", "-f", "concat", "-safe", "0", "-i", str(lst), "-c", "copy", str(joined)])
    total = float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(joined)],
                                 capture_output=True, text=True).stdout.strip())

    draws = []
    hook = e.get("hook") or ({"title": e["title"]} if e.get("title") else None)
    if hook:
        draws.append(text(hook["title"], 104, "0xF5C518", 560, 0, 2.5, 8))
        if hook.get("sub"):
            draws.append(text(hook["sub"], 60, "white", 700, 0, 2.5))
    # 抖音式置頂大字（整支都在，無底色、粗黑邊）：避開最上方 220px 的系統列
    for j, ln in enumerate(e.get("pin", [])):
        draws.append(text(ln["text"], int(ln.get("size", 92)), ln.get("color", "white"), 250 + j * 118, 0, total + 1, 9))
    cy, cs = float(e.get("caption_y", 0.70)), int(e.get("caption_size", 62))
    for cap in e.get("captions", []):
        draws.append(text(cap["text"], cs, cap.get("color", "white"), int(H * cy), float(cap["start"]), float(cap["end"]), 7))
    end_lines = e.get("end_text") or []
    for j, line in enumerate(end_lines):
        color = "0xF5C518" if j == 0 else "white"
        draws.append(text(line, 76 if j == 0 else 62, color, int(H * 0.66) + j * 100, max(0, total - 2.4), total + 1))

    filters, inputs = [], ["-i", str(joined)]
    last = "0:v"
    if draws:
        filters.append(f"[{last}]" + ",".join(draws) + "[v1]")
        last = "v1"
    if e.get("logo", False) and LOGO.exists():
        inputs += ["-i", str(LOGO)]
        filters.append(f"[1:v]scale=120:120,format=rgba[lg];[{last}][lg]overlay=x=W-w-40:y=H-h-300[v2]")
        last = "v2"
    out_dir = ROOT / "out"
    out_dir.mkdir(exist_ok=True)
    final = out_dir / f"{e['slug']}.mp4"
    cmd = ["ffmpeg", "-v", "error", "-y", *inputs]
    if filters:
        cmd += ["-filter_complex", ";".join(filters), "-map", f"[{last}]"]
    else:
        cmd += ["-map", "0:v"]
    cmd += ["-map", "0:a", "-af", "loudnorm=I=-14:TP=-1.5:LRA=11", "-c:v", "libx264", "-preset", "medium", "-crf", "17",
            "-pix_fmt", "yuv420p", *COLOR, "-bsf:v", "h264_metadata=colour_primaries=1:transfer_characteristics=1:matrix_coefficients=1",
            "-c:a", "aac", "-b:a", "192k", "-ar", "48000", "-movflags", "+faststart", str(final)]
    run(cmd)
    run(["ffmpeg", "-v", "error", "-y", "-ss", "1", "-i", str(final), "-frames:v", "1", "-q:v", "3", str(out_dir / f"{e['slug']}.jpg")])
    print("完成", final, round(total, 1), "秒", final.stat().st_size // 1024, "KB")


if __name__ == "__main__":
    for p in sys.argv[1:]:
        main(p)
