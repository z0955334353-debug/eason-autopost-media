"""依剪輯單（edl/*.json）剪出 1080x1920 的 Reels，輸出到 out/。

剪輯單格式：
{
  "slug": "20261104-kansai",            # 檔名
  "title": "關西風壽喜燒的第一步",        # 上方標題列文字（選填，最多 14 字）
  "clips": [{"id": "雲端檔案ID", "start": 1.5, "end": 6.0, "speed": 1.0},
            {"photo": "komazawa/pro/2V1A6971.jpg", "dur": 0.6}],   # 照片：repo 內路徑，會慢慢推近
  "keep_audio": true,                    # 保留現場聲音
  "logo": true                           # 右下角小 logo
}
"""
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
FONT = "/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc"
LOGO = ROOT.parent.parent / "komazawa-helper" / "public" / "icon.png"
W, H = 1080, 1920


def run(cmd):
    print(" ".join(map(str, cmd))[:300])
    subprocess.run(cmd, check=True)


def main(edl_path):
    e = json.loads(Path(edl_path).read_text(encoding="utf-8"))
    tmp = Path("/tmp/kzr")
    tmp.mkdir(exist_ok=True)
    parts = []
    repo = ROOT.parent.parent
    for i, c in enumerate(e["clips"]):
        if c.get("photo"):
            dur = float(c.get("dur", 0.8))
            out = tmp / f"part{i}.mp4"
            frames = int(dur * 30)
            vf = (f"scale={W*2}:{H*2}:force_original_aspect_ratio=increase,crop={W*2}:{H*2},"
                  f"zoompan=z='1+0.04*on/{frames}':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d={frames}:s={W}x{H}:fps=30,setsar=1")
            run(["ffmpeg", "-v", "error", "-y", "-i", str(repo / c["photo"]), "-f", "lavfi", "-t", str(dur), "-i", "anullsrc=r=48000:cl=stereo",
                 "-vf", vf, "-frames:v", str(frames), "-map", "0:v", "-map", "1:a", "-c:v", "libx264", "-preset", "veryfast", "-crf", "18",
                 "-pix_fmt", "yuv420p", "-c:a", "aac", "-ar", "48000", "-ac", "2", "-shortest", str(out)])
            parts.append(out)
            continue
        src = tmp / f"src_{c['id']}"
        if not src.exists():
            run(["curl", "-sSL", "-A", "Mozilla/5.0", "-o", str(src),
                 f"https://drive.usercontent.google.com/download?id={c['id']}&export=download&confirm=t"])
        has_audio = "audio" in subprocess.run(["ffprobe", "-v", "error", "-show_entries", "stream=codec_type", "-of", "csv=p=0", str(src)],
                                              capture_output=True, text=True).stdout
        speed = float(c.get("speed", 1.0))
        dur = float(c["end"]) - float(c["start"])
        out = tmp / f"part{i}.mp4"
        vf = f"scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H},setsar=1,fps=30,setpts=PTS/{speed}"
        cmd = ["ffmpeg", "-v", "error", "-y", "-ss", str(c["start"]), "-t", str(dur), "-i", str(src)]
        if not (has_audio and e.get("keep_audio", True)):
            cmd += ["-f", "lavfi", "-t", str(dur / speed), "-i", "anullsrc=r=48000:cl=stereo"]
            amap = ["-map", "0:v", "-map", "1:a"]
        else:
            amap = ["-map", "0:v", "-map", "0:a", "-af", f"atempo={speed}" if speed != 1.0 else "anull"]
        cmd += ["-vf", vf, *amap, "-c:v", "libx264", "-preset", "veryfast", "-crf", "18", "-c:a", "aac", "-ar", "48000", "-ac", "2", "-shortest", str(out)]
        run(cmd)
        parts.append(out)
    lst = tmp / "list.txt"
    lst.write_text("".join(f"file '{p}'\n" for p in parts))
    joined = tmp / "joined.mp4"
    run(["ffmpeg", "-v", "error", "-y", "-f", "concat", "-safe", "0", "-i", str(lst), "-c", "copy", str(joined)])

    filters, inputs = [], ["-i", str(joined)]
    last = "0:v"
    if e.get("title"):
        t = e["title"].replace(":", "\\:").replace("'", "’")[:14]
        filters.append(f"[{last}]drawbox=x=0:y=150:w={W}:h=150:color=0x022C00@0.88:t=fill,"
                       f"drawtext=fontfile={FONT}:text='{t}':fontcolor=0xF4ECDF:fontsize=72:x=(w-text_w)/2:y=150+(150-text_h)/2[v1]")
        last = "v1"
    if e.get("logo", True) and LOGO.exists():
        inputs += ["-i", str(LOGO)]
        filters.append(f"[1:v]scale=150:150,format=rgba[lg];[{last}][lg]overlay=x=W-w-48:y=H-h-260[v2]")
        last = "v2"
    out_dir = ROOT / "out"
    out_dir.mkdir(exist_ok=True)
    final = out_dir / f"{e['slug']}.mp4"
    cmd = ["ffmpeg", "-v", "error", "-y", *inputs]
    if filters:
        cmd += ["-filter_complex", ";".join(filters), "-map", f"[{last}]"]
    else:
        cmd += ["-map", "0:v"]
    cmd += ["-map", "0:a", "-c:v", "libx264", "-preset", "veryfast", "-crf", "20", "-pix_fmt", "yuv420p",
            "-c:a", "aac", "-b:a", "160k", "-movflags", "+faststart", str(final)]
    run(cmd)
    run(["ffmpeg", "-v", "error", "-y", "-ss", "1", "-i", str(final), "-frames:v", "1", "-q:v", "3", str(out_dir / f"{e['slug']}.jpg")])
    print("完成", final, final.stat().st_size // 1024, "KB")


if __name__ == "__main__":
    for p in sys.argv[1:]:
        main(p)
