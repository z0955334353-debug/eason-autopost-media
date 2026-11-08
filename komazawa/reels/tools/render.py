"""依剪輯單（edl/*.json）剪出 1080x1920 的 Reels，輸出到 out/。

剪輯單格式：
{
  "slug": "20261104-kansai",                       # 檔名
  "hook": {"title": "黃色大標", "sub": "白色副標", "y": 0.13},   # 開頭 2.5 秒的標題（無底色、白字黑邊），選填；y 選填（預設 560px）
  "captions": [{"start": 9.5, "end": 12.0, "text": "糖先下鍋", "y": 0.24}],   # 畫面中的字；y 可個別指定高度（畫面比例），字不可蓋住肉、鍋、手的動作
  "end_text": ["最後入座 00:30", "今晚要不要來一鍋？"],             # 疊在最後 2.4 秒（end_secs 可改），選填；"end_y" 選填（預設 0.64）
  "pin": [{"text": "台中北區", "color": "white"}, {"text": "開到半夜的壽喜燒", "color": "0xF5C518"}],  # 抖音版：整支置頂大字，選填
  "caption_y": 0.62, "caption_size": 72,             # 字幕高度（畫面比例）與字級，選填
  "sfx": [{"file": "komazawa/reels/sfx/hit.wav", "at": 0, "vol": 0.7}],  # 音效（hit 開場、whoosh 換段落、pop 字幕出現），選填
  "live_vol": 0.9,                                  # 現場聲音音量，選填
  "live_lufs": -30,                                 # 選填：把現場聲音壓成固定的小音量背景（數字越小越小聲），音效維持清楚；有設就不再把整支拉到 -14
  （clips 裡的片段可加 "punch": true：開頭快速放大回彈，通常只用在第一個片段）
  （clips 裡的片段可加 "crop_top": 0.3／"crop_bottom": 0.1：先把原片上方（下方）這個比例裁掉，再放大填滿 1080x1920（左右置中裁）。
    行銷長 11/08：桌邊鏡頭畫面上緣有客人身體／下巴就用 crop_top 裁掉，裁完仍看得到就整段不用；照片也適用）
  （clips 裡的片段可加 "gain_db": 6：只調這一刀的現場聲（dB，正數大聲、負數小聲）。B 套剪法用：肉下鍋／冒煙那幾刀 +6～+8，備料刀 -4～0；
    整條現場聲之後仍會被 live_lufs 壓到固定響度，所以是「相對大小」）
  "clips": [{"id": "雲端檔案ID", "start": 1.5, "end": 6.0, "speed": 1.0},
            {"photo": "komazawa/pro/2V1A6971.jpg", "dur": 0.6}],   # 照片：repo 內路徑，會慢慢推近
  "keep_audio": true,                               # 保留現場聲音
  "logo": false,                                    # 右下角小 logo（預設不放）
  "masks": [{"y0": 0.26, "y1": 0.42, "start": 0, "end": 2.2}]   # 選填：遮客人臉的色帶（老闆 11/06：可以用圖樣或文字設計擋住臉）
}
masks：**老闆 2026-11-07 禁止畫面中間有任何色塊，render.py 會略過 masks 並印警告**（舊說明保留供查）。每個是一條實心色帶（預設全寬、深色 0x111111，可加 "x0"/"x1" 變成方塊、"color" 改顏色），畫在字的下面，
hook／字幕可以直接壓在色帶上當「文字設計」。秒數是成片時間；色帶要把整段裡每一格的客人臉（含側臉）都蓋住，做完一定要逐格檢查。
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


def trim(c):
    """crop_top／crop_bottom：先裁掉原片上（下）緣的比例，回傳 ffmpeg 濾鏡前綴（沒設就空字串）。"""
    t, b = float(c.get("crop_top", 0) or 0), float(c.get("crop_bottom", 0) or 0)
    if t <= 0 and b <= 0:
        return ""
    if t < 0 or b < 0 or t + b >= 0.8:
        raise SystemExit(f"crop_top + crop_bottom 要介於 0～0.8：{c}")
    return f"crop=iw:trunc(ih*{1 - t - b:.4f}/2)*2:0:trunc(ih*{t:.4f}/2)*2,"


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
            vf = (f"{trim(c)}scale={W*2}:{H*2}:force_original_aspect_ratio=increase,crop={W*2}:{H*2},"
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
        base = f"{trim(c)}scale={W}:{H}:force_original_aspect_ratio=increase:flags=lanczos,crop={W}:{H},setsar=1,fps=30,setpts=PTS/{speed}"
        cmd = ["ffmpeg", "-v", "error", "-y", "-ss", str(c["start"]), "-t", str(dur), "-i", str(src)]
        if not (has_audio and e.get("keep_audio", True)):
            cmd += ["-f", "lavfi", "-t", str(dur / speed), "-i", "anullsrc=r=48000:cl=stereo"]
            amap = ["-map", "0:v:0", "-map", "1:a:0"]
        else:
            af = f"atempo={speed}" if speed != 1.0 else "anull"
            if c.get("gain_db") is not None:  # 單刀現場聲加減（B 套：鍋裡大聲、備料小聲）
                af += f",volume={float(c['gain_db'])}dB"
            amap = ["-map", "0:v:0", "-map", "0:a:0", "-af", af]
        tail = [*amap, "-c:v", "libx264", "-preset", "medium", "-crf", "16", "-pix_fmt", "yuv420p", *COLOR,
                "-c:a", "aac", "-ar", "48000", "-ac", "2", "-shortest", str(out)]
        if c.get("punch"):  # 開場快速放大回彈：前 0.35 秒從 1.15 倍縮回 1 倍
            base = (f"{trim(c)}scale={W}:{H}:force_original_aspect_ratio=increase:flags=lanczos,crop={W}:{H},setsar=1,fps=30,setpts=PTS/{speed},"
                    f"scale=w='{W}*(1+0.15*max(0,1-t/0.35))':h='{H}*(1+0.15*max(0,1-t/0.35))':eval=frame,crop={W}:{H},setsar=1")
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
    if e.get("masks"):
        print("警告：剪輯單有 masks，老闆 2026-11-07 規定畫面中間不准有色塊，已略過。有客人臉的段落請直接不用。")
    for m in []:
        x0, x1 = float(m.get("x0", 0)), float(m.get("x1", 1))
        y0, y1 = float(m["y0"]), float(m["y1"])
        draws.append(f"drawbox=x={int(W*x0)}:y={int(H*y0)}:w={int(W*(x1-x0))}:h={int(H*(y1-y0))}:color={m.get('color', '0x111111')}@1:t=fill:"
                     f"enable='between(t,{float(m.get('start', 0)):.2f},{float(m['end']):.2f})'")
    hook = e.get("hook") or ({"title": e["title"]} if e.get("title") else None)
    if hook:
        hy = int(H * float(hook["y"])) if hook.get("y") is not None else 560  # 選填 "y"：大標高度（畫面比例），副標在下方 140px
        draws.append(text(hook["title"], 104, "0xF5C518", hy, 0, 2.5, 8))
        if hook.get("sub"):
            draws.append(text(hook["sub"], 60, "white", hy + 140, 0, 2.5))
    # 抖音式置頂大字（整支都在，無底色、粗黑邊）：避開最上方 220px 的系統列
    for j, ln in enumerate(e.get("pin", [])):
        draws.append(text(ln["text"], int(ln.get("size", 92)), ln.get("color", "white"), 250 + j * 118, 0, total + 1, 9))
    cy, cs = float(e.get("caption_y", 0.70)), int(e.get("caption_size", 62))
    for cap in e.get("captions", []):
        draws.append(text(cap["text"], int(cap.get("size", cs)), cap.get("color", "white"), int(H * float(cap.get("y", cy))), float(cap["start"]), float(cap["end"]), 7))
    end_lines = e.get("end_text") or []
    end_secs = float(e.get("end_secs", 2.4))
    for j, line in enumerate(end_lines):
        color = "0xF5C518" if j == 0 else "white"
        ey = int(H * float(e.get("end_y", 0.64)))  # 選填 "end_y"：字卡第一行高度（畫面比例），可壓在 masks 字帶上
        draws.append(text(line, 84 if j == 0 else 62, color, ey + j * (110 if j == 1 else 90), max(0, total - end_secs), total + 1))

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
    # 音效：[{"file": "komazawa/reels/sfx/pop.wav", "at": 4.8, "vol": 0.5}]，疊在現場聲音上
    sfx = [x for x in e.get("sfx", []) if (repo / x["file"]).exists() and float(x["at"]) < total]
    alabel = "0:a"
    if sfx:
        base_idx = len(inputs) // 2
        live_lufs = e.get("live_lufs")
        live_chain = f"loudnorm=I={float(live_lufs)}:TP=-3:LRA=11," if live_lufs is not None else ""
        mix = [f"[0:a]{live_chain}volume={float(e.get('live_vol', 1.0))}[live]"]
        names = ["[live]"]
        for k, x in enumerate(sfx):
            inputs += ["-i", str(repo / x["file"])]
            ms = int(float(x["at"]) * 1000)
            mix.append(f"[{base_idx + k}:a]aresample=48000,aformat=channel_layouts=stereo,volume={float(x.get('vol', 0.6))},adelay={ms}|{ms}[s{k}]")
            names.append(f"[s{k}]")
        mix.append("".join(names) + f"amix=inputs={len(names)}:duration=first:normalize=0,"
                   + ("alimiter=limit=0.89[amx]" if live_lufs is not None else "loudnorm=I=-14:TP=-1.5:LRA=11[amx]"))
        filters += mix
        alabel = "[amx]"
    cmd = ["ffmpeg", "-v", "error", "-y", *inputs]
    if filters:
        cmd += ["-filter_complex", ";".join(filters), "-map", f"[{last}]" if last != "0:v" else "0:v"]
    else:
        cmd += ["-map", "0:v"]
    cmd += ["-map", alabel, *([] if sfx else ["-af", f"loudnorm=I={float(e.get('live_lufs', -14))}:TP=-1.5:LRA=11"]), "-c:v", "libx264", "-preset", "medium", "-crf", "17",
            "-pix_fmt", "yuv420p", *COLOR, "-bsf:v", "h264_metadata=colour_primaries=1:transfer_characteristics=1:matrix_coefficients=1",
            "-c:a", "aac", "-b:a", "192k", "-ar", "48000", "-movflags", "+faststart", str(final)]
    run(cmd)
    run(["ffmpeg", "-v", "error", "-y", "-ss", "1", "-i", str(final), "-frames:v", "1", "-q:v", "3", str(out_dir / f"{e['slug']}.jpg")])
    print("完成", final, round(total, 1), "秒", final.stat().st_size // 1024, "KB")


if __name__ == "__main__":
    for p in sys.argv[1:]:
        main(p)
