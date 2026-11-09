"""旅途 Reels：自動字幕＋剪停頓（11/09 工程師第 18 項）。

用法：python autocaption.py eason/reels/edl/<slug>.json
輸出：eason/reels/build/<slug>.json（給 render.py 用的完整剪輯單）
      eason/reels/build/<slug>.captions.txt（字幕逐句、給行銷長／合規看）

流程（只處理有人聲的片段；純空景原樣保留）：
1. 每個片段先用 faster-whisper 聽一次；聽不到話 → 當空景，不剪不上字。
2. 有人聲：ffmpeg silencedetect 找出超過 0.35 秒的停頓剪掉，切點前後各留 0.1 秒。
   （不要用 0.1 秒門檻，中文字和換氣會被剪碎。）
3. 字幕：OpenCC s2twp 轉台灣繁體 → 套專有名詞表 → 一句一行（最多 12 字）→
   白字黑邊約 62px、畫面約 7 成高度、專有名詞黃色。
4. 合規：字幕有禁用語（買進、賣出、賺、獲利、私訊、操盤…）→ 不產生 build，程式回報失敗，
   並寫 out/<slug>.合規未過.txt，請行銷長改剪輯單（可在剪輯單手動寫 captions 並加 "auto": false）。

剪輯單選填欄位：
  "auto": false            整支不跑自動字幕／剪停頓（手動 captions 照用）
  clips[i]."voice": false  這段當空景，不聽、不剪
  "pause": 0.35, "pad": 0.1, "noise_db": -30   停頓門檻、切點留白、靜音判定音量
"""
import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
REPO = ROOT.parent.parent
TMP = Path("/tmp/esr_cap")

# 專有名詞：正確寫法 → 常見聽錯寫法
GLOSSARY = {
    "壹神": ["一神", "易神", "億神", "依神", "伊神", "益神", "逸神"],
    "台指期": ["台指旗", "台指奇", "台指其", "臺指期", "台制期", "台指期貨期"],
    "TradingView": ["Trading View", "trading view", "Tradingview", "tradingview", "崔丁view", "崔丁View"],
    "VWAP": ["V WAP", "vwap", "VWap", "V-WAP"],
    "生命線": ["生命限", "聲明線", "生名線"],
    "停損": ["停筍", "挺損", "止損"],
    "胡志明": ["胡誌明", "胡志名", "湖志明", "胡知明"],
    "交易員": ["交易原", "交易園"],
}
KEYWORDS = list(GLOSSARY)
# 合規禁用語（字幕出現就擋下）
BANNED = ["買進", "買入", "賣出", "賺", "獲利", "私訊", "操盤", "帶單", "跟單", "明牌", "穩賺", "保證",
          "目標價", "進場", "出場", "報酬率", "飆股", "加LINE", "加賴", "老師帶"]
PROMPT = "以下是繁體中文。壹神、台指期、TradingView、VWAP、生命線、停損、胡志明、交易員。"
MAX_CHARS = 12

_model = None


def model():
    global _model
    if _model is None:
        from faster_whisper import WhisperModel
        _model = WhisperModel("small", device="cpu", compute_type="int8")
    return _model


def run(cmd):
    return subprocess.run(cmd, capture_output=True, text=True)


def to_tw(s):
    try:
        import opencc
        conv = opencc.OpenCC("s2twp")
    except Exception:
        conv = None
    if conv:
        s = conv.convert(s)
    s = s.replace("臺", "台")  # 台灣日常寫法（OpenCC 會轉成「臺」）
    for right, wrongs in GLOSSARY.items():
        for w in sorted(wrongs, key=len, reverse=True):
            s = s.replace(w, right)
    return s


def source(c, slug):
    if c.get("file"):
        p = Path(c["file"])
        return p if p.is_absolute() else REPO / p
    src = Path(f"/tmp/esr/{slug}") / f"src_{c['id']}"
    src.parent.mkdir(parents=True, exist_ok=True)
    if not src.exists():
        subprocess.run(["curl", "-sSL", "-A", "Mozilla/5.0", "-o", str(src),
                        f"https://drive.usercontent.google.com/download?id={c['id']}&export=download&confirm=t"], check=True)
    return src


def has_audio(src):
    return "audio" in run(["ffprobe", "-v", "error", "-show_entries", "stream=codec_type", "-of", "csv=p=0", str(src)]).stdout


def pcm(wav):
    """用 ffmpeg 解成 16k 單聲道 float32（不靠 PyAV，避免版本不合）。"""
    import numpy as np
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", str(wav), "-f", "f32le", "-ac", "1", "-ar", "16000", "-"],
                         capture_output=True, check=True).stdout
    return np.frombuffer(raw, dtype=np.float32).copy()


def speech_ranges(wav, dur, pause, pad, noise_db):
    """回傳要保留的區間（相對片段起點）：剪掉超過 pause 秒的停頓，前後各留 pad 秒。"""
    err = run(["ffmpeg", "-hide_banner", "-i", str(wav), "-af", f"silencedetect=noise={noise_db}dB:d={pause}", "-f", "null", "-"]).stderr
    starts = [float(x) for x in re.findall(r"silence_start: (-?[\d.]+)", err)]
    ends = [float(x) for x in re.findall(r"silence_end: ([\d.]+)", err)]
    silences = []
    for i, s in enumerate(starts):
        e = ends[i] if i < len(ends) else dur
        silences.append((max(0.0, s), min(dur, e)))
    keep, cur = [], 0.0
    for s, e in silences:
        cut0, cut1 = s + pad, e - pad
        if cut1 - cut0 <= 0.05:
            continue
        if cut0 > cur:
            keep.append((cur, cut0))
        cur = max(cur, cut1)
    if dur - cur > 0.05:
        keep.append((cur, dur))
    return [(a, b) for a, b in keep if b - a >= 0.12] or [(0.0, dur)]


def lines_from_words(words):
    """words: [(start, end, text)]（成片時間）→ 一句一行、最多 MAX_CHARS 字。"""
    out, buf, t0, t1 = [], "", None, None
    def flush():
        nonlocal buf, t0, t1
        txt = re.sub(r"[，。、！？!?,.;；：:「」『』…\"]+", " ", buf).strip()
        txt = re.sub(r"\s+", " ", txt)
        if txt:
            out.append({"start": round(t0, 2), "end": round(t1, 2), "text": txt})
        buf, t0, t1 = "", None, None
    for s, e, w in words:
        w = to_tw(w)
        brk = bool(re.search(r"[，。！？!?,.]$", w.strip()))
        if buf and len(re.sub(r"\s", "", buf + w)) > MAX_CHARS:
            flush()
        if t0 is None:
            t0 = s
        buf += w
        t1 = e
        if brk:
            flush()
    flush()
    # 專有名詞不可被切成兩行（例如「看台」／「指期」）：把前半移到下一行
    for i in range(len(out) - 1):
        a_, b_ = out[i], out[i + 1]
        for k in KEYWORDS:
            for j in range(1, len(k)):
                if a_["text"].endswith(k[:j]) and b_["text"].startswith(k[j:]):
                    a_["text"] = a_["text"][:-j].rstrip()
                    b_["text"] = k[:j] + b_["text"]
                    break
    out = [c for c in out if c["text"]]
    # 字幕不留空窗太短的閃爍：每句至少 0.6 秒，不壓到下一句
    for i, c in enumerate(out):
        nxt = out[i + 1]["start"] if i + 1 < len(out) else c["end"] + 0.6
        c["end"] = round(min(max(c["end"], c["start"] + 0.6), nxt), 2)
    return out


def main(edl_path):
    edl_path = Path(edl_path)
    e = json.loads(edl_path.read_text(encoding="utf-8"))
    slug = e["slug"]
    out_dir = REPO / e["out_dir"] if e.get("out_dir") else ROOT / "out"
    build_dir = out_dir.parent / "build" if e.get("out_dir") else ROOT / "build"
    build_dir.mkdir(parents=True, exist_ok=True)
    TMP.mkdir(parents=True, exist_ok=True)
    if e.get("auto") is False:
        (build_dir / f"{slug}.json").write_text(json.dumps(e, ensure_ascii=False, indent=1), encoding="utf-8")
        print("auto=false，照原剪輯單")
        return 0
    pause, pad, noise = float(e.get("pause", 0.35)), float(e.get("pad", 0.1)), float(e.get("noise_db", -30))
    new_clips, words, t_out = [], [], 0.0
    for i, c in enumerate(e["clips"]):
        speed = float(c.get("speed", 1.0))
        if c.get("photo"):
            new_clips.append(c)
            t_out += float(c.get("dur", 0.8))
            continue
        a, b = float(c["start"]), float(c["end"])
        src = source(c, slug)
        voiced = []
        if c.get("voice", True) and e.get("keep_audio", True) and has_audio(src):
            wav = TMP / f"{slug}_{i}.wav"
            run(["ffmpeg", "-v", "error", "-y", "-ss", str(a), "-t", str(b - a), "-i", str(src), "-vn", "-ac", "1", "-ar", "16000", str(wav)])
            segs, _ = model().transcribe(pcm(wav), language="zh", initial_prompt=PROMPT, word_timestamps=True,
                                         vad_filter=True, beam_size=5)
            for sg in segs:
                for w in (sg.words or []):
                    if w.word.strip():
                        voiced.append((w.start, w.end, w.word))
        if not voiced:  # 空景：原樣
            new_clips.append(c)
            t_out += (b - a) / speed
            continue
        keep = speech_ranges(wav, b - a, pause, pad, noise)
        print(f"片段 {i}：有人聲，{len(voiced)} 字，剪成 {len(keep)} 段，原 {b - a:.1f}s → {sum(y - x for x, y in keep):.1f}s")
        for k, (x, y) in enumerate(keep):
            nc = dict(c, start=round(a + x, 3), end=round(a + y, 3))
            if k > 0:
                nc.pop("punch", None)
            new_clips.append(nc)
            for ws, we, wt in voiced:
                mid = (ws + we) / 2
                if x <= mid < y:
                    words.append((t_out + (max(ws, x) - x) / speed, t_out + (min(we, y) - x) / speed, wt))
            t_out += (y - x) / speed
    caps = lines_from_words(words) if words else []
    caps = [c for c in caps if c["end"] <= t_out + 0.05]
    for c in caps:
        hl = [k for k in KEYWORDS if k in c["text"]]
        if hl:
            c["hl"] = hl
    bad = sorted({w for c in caps for w in BANNED if w in c["text"]})
    report = "\n".join(f"{c['start']:6.2f}-{c['end']:6.2f}  {c['text']}" for c in caps)
    (build_dir / f"{slug}.captions.txt").write_text(report + "\n", encoding="utf-8")
    print(report)
    if bad:
        out_dir.mkdir(parents=True, exist_ok=True)
        (out_dir / f"{slug}.合規未過.txt").write_text(
            f"字幕出現禁用語：{'、'.join(bad)}\n請改剪輯單：把這段剪掉，或手動寫 captions 並加 \"auto\": false。\n\n{report}\n", encoding="utf-8")
        print("合規未過：", bad)
        return 2
    final = dict(e, clips=new_clips)
    manual = e.get("captions") or []
    final["captions"] = manual + caps if not manual else manual  # 有手寫字幕就以手寫為準
    final["auto_done"] = True
    (build_dir / f"{slug}.json").write_text(json.dumps(final, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"完成：成片約 {t_out:.1f} 秒，字幕 {len(caps)} 句")
    return 0


if __name__ == "__main__":
    rc = 0
    for p in sys.argv[1:]:
        rc = max(rc, main(p))
    sys.exit(rc)
