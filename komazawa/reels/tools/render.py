"""依剪輯單（edl/*.json）剪出 1080x1920 的 Reels，輸出到 out/。

剪輯單格式：
{
  "slug": "20261104-kansai",                       # 檔名
  "hook": {"title": "黃色大標", "sub": "白色副標"},   # 開頭 2.5 秒的標題（無底色、白字黑邊），選填；位置固定在 TITLE_Y（IG 主頁格子安全區），不可自訂
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
  （clips 裡的片段可加 "zoom": {"x": 0.5, "y": 0.65, "w": 0.55}：老闆 11/11「放大鍋物、閃掉客人就好」。以 (x, y) 為中心（原片比例）
    裁出寬度 w（0.4～1）的直式畫面再放大填滿，用來只留鍋、肉、手。有 zoom 就不看 crop_top／crop_bottom；照片也適用）
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
hook 可改寫 "stack": ["台中北區", "半夜十二點", "還能開這一鍋"]（最多 3 行、每行 8 字內）：取代 title，0／0.45／0.9 秒一行一行疊出來，
  前面幾行白字、最後一行黃字，全部掛到 2.5 秒；sub 會自動排在最後一行下面（11/20 加，參考 @want.2.eat 54 萬「台中新開→200多元→吃到飽」）。
舊格式的 "title" 會當成 hook 的大標（不再畫上方的色塊標題列）。
長度建議 25～35 秒，每 2～3 秒換一個畫面。
警告（只印、不擋出片，11/11 加）：同一支原片合計超過 5 秒；zoom 後保留寬度不到 640 像素（1080p 原片 w < 0.6 會偏糊）。
警告（11/13 加）：hook／置頂／字幕／片尾的字（去空白後）重複；同時有 hook 和 pin 時 pin 自動延到 2.5 秒後才出現（不再疊字）。
警告（11/12 加）：剪輯單用了 "photo"（老闆 11/12：Reels 全部要影片）；開場同一場景超過 3 秒才換畫面；單句字幕掛超過 4.5 秒（字要跟著畫面換）。
警告（11/14 加）：clip 可選填 "nofood": true（沒有能吃的東西：空鍋、木桶、招牌、店門…）與 "tag": "倒醬油"（動作名稱）；
  前 10 秒 nofood > 1.5 秒、全片 nofood > 3 秒、同一 tag 在不相鄰的位置再出現、-ig 片段合計不在 30～35 秒（-tiktok 27～32 秒）都會印⚠️。
警告（11/15 加）：第一刀標了 nofood 會印⚠️（第一格一定要是食物）；slug 含 "-short"（單品快版，額外加做、不取代 IG／抖音主片）片段合計不在 7～15 秒會印⚠️。
警告（11/16 加）：同一支原片、原片時間相隔不到 4 秒的兩刀（不論相不相鄰）印⚠️「可能同一動作切兩次」；兩刀標了不同 tag 就不算。
警告（11/18 加）：同義動作算同一個 tag（冒煙／起霧／倒醬油→淋醬油、化糖／撒糖→下糖，見 ACTION_ALIAS）；
  tag 是 抹油／下糖／空鍋／加水／木桶／招牌／店門（NOFOOD_TAGS）就算沒標 nofood 也算「沒有食物」。
警告（11/19 加）：生肉貼糖的各種 tag（下肉／拎起和牛／煎香／貼糖煎）與沾蛋（蛋碗／滑進蛋）也算同一動作；
  -ig／-tiktok 主片要寫 "format": "類型名"（倒帶型、單品快版、一鏡到底、品項連發、情境型、特寫型、開店前EP、二選一），
  沒寫、或前 2 天同平台都是同一型（舊剪輯單沒寫 format 視為倒帶型）印⚠️。
警告（11/17 加）：相鄰同 tag（「翻生肉」「翻肉」視為同一動作）連續合計 > 3.5 秒、或相鄰同 tag 來自不同原片（換角度），印⚠️；最後一刀不算。
警告（11/21 加）：某一刀在前 7 天剪輯單已有 2 天用過同一段（第 5 條最多 2 次）、第一刀前 3 天用過、或全片 ≥ 50% 秒數是前 7 天用過的；音效 > 6 個、或 ≥ 3 個音效貼著字幕出現（B 套字幕不配啵），印⚠️。
"copy": {"ig": "IG 文案", "tiktok": "抖音文案"}：選填。有寫的話會跟畫面上的字一起做「禁用說法」檢查（BANNED，老闆 11/09：只有開鍋由店員服務），
  命中就直接停止、不出片；推 LINE 前請把文案也放進剪輯單讓程式檢查。
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
TITLE_Y = 400  # 封面標題的固定高度：IG 主頁 3:4 格子只顯示 y 240～1680，標題放 400 起才不會被切
TONEMAP = ("zscale=t=linear:npl=100,format=gbrpf32le,zscale=p=bt709,tonemap=tonemap=hable:desat=0,"
           "zscale=t=bt709:m=bt709:r=tv,format=yuv420p")
# 老闆 2026-11-13：食物看起來死白 → 一律加暖色、提飽和與對比（剪輯單可用 "grade": false 關掉）
# 老闆 2026-11-23：舊版調色太弱，肉還是死白／偏冷 → 先把冷白燈校成暖色溫，再加飽和、對比、暖色（店內白光燈拍的素材都要）
# 老闆 2026-11-23 17:30：重調色把和牛油花紋路吃掉 → 改輕微校正：只把冷白燈拉回一點點暖、對比飽和幾乎不動，紋路優先
GRADE = "colortemperature=temperature=5900:mix=0.6,eq=contrast=1.04:saturation=1.04"
COLOR = ["-colorspace", "bt709", "-color_primaries", "bt709", "-color_trc", "bt709"]


def run(cmd, check=True):
    print(" ".join(map(str, cmd))[:300])
    return subprocess.run(cmd, check=check)


def fetch(fid, tmp):
    """先用 repo 裡的備份（raw/<ID>.mp4），沒有才去雲端抓；雲端被刪就清楚說明。"""
    raw = ROOT / "raw" / f"{fid}.mp4"
    if raw.exists():
        return raw
    src = tmp / f"src_{fid}"
    if not src.exists():
        run(["curl", "-sSL", "-A", "Mozilla/5.0", "-o", str(src),
             f"https://drive.usercontent.google.com/download?id={fid}&export=download&confirm=t"], check=False)
        kind = subprocess.run(["file", "-b", "--mime-type", str(src)], capture_output=True, text=True).stdout.strip() if src.exists() else ""
        if not kind.startswith("video/"):
            src.unlink(missing_ok=True)
            sys.exit(f"素材 {fid} 沒有備份，雲端也抓不到（可能已被刪除）→ 這支剪輯單請換片段")
    return src


def probe(src, entries):
    return subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries", entries, "-of", "csv=p=0", str(src)],
                          capture_output=True, text=True).stdout.strip()


def esc(t):
    return str(t).replace("\\", "\\\\").replace(":", "\\:").replace("'", "’").replace("%", "\\%")


def text(t, size, color, y, start, end, border=6):
    return (f"drawtext=fontfile={FONT}:text='{esc(t)}':fontsize={size}:fontcolor={color}:borderw={border}:bordercolor=black@0.85:"
            f"x=(w-text_w)/2:y={y}:enable='between(t,{start:.2f},{end:.2f})'")


def trim(c):
    """zoom 或 crop_top／crop_bottom：先裁原片，回傳 ffmpeg 濾鏡前綴（沒設就空字串）。"""
    z = c.get("zoom")
    if z:  # 老闆 11/11：放大鍋物、閃掉客人。{"x": 中心橫向比例, "y": 中心直向比例, "w": 保留寬度比例 0.4～1}
        w, cx, cy = float(z.get("w", 0.6)), float(z.get("x", 0.5)), float(z.get("y", 0.5))
        if not (0.4 <= w <= 1 and 0 <= cx <= 1 and 0 <= cy <= 1):
            raise SystemExit(f"zoom 的 w 要 0.4～1、x／y 要 0～1：{c}")
        return (f"crop=w='trunc(iw*{w:.4f}/2)*2':h='trunc(min(ih,iw*{w:.4f}*16/9)/2)*2':"
                f"x='max(0,min(iw-out_w,iw*{cx:.4f}-out_w/2))':y='max(0,min(ih-out_h,ih*{cy:.4f}-out_h/2))',")
    t, b = float(c.get("crop_top", 0) or 0), float(c.get("crop_bottom", 0) or 0)
    if t <= 0 and b <= 0:
        return ""
    if t < 0 or b < 0 or t + b >= 0.8:
        raise SystemExit(f"crop_top + crop_bottom 要介於 0～0.8：{c}")
    return f"crop=iw:trunc(ih*{1 - t - b:.4f}/2)*2:0:trunc(ih*{t:.4f}/2)*2,"


BANNED = ["幫你煎好", "全程幫你煎", "只要負責吃", "負責吃就好", "全程幫你", "全程代煎", "幫你顧到好"]  # 老闆 2026-11-09 更正桌邊服務說法


def check_words(e):
    """畫面上的字＋選填文案（copy）裡有禁用說法就停止。回傳命中清單（測試用）。"""
    texts = []
    h = e.get("hook") or {}
    texts += [h.get("title", ""), h.get("sub", ""), e.get("title", "")] + list(h.get("stack", []))
    texts += [c.get("text", "") for c in e.get("captions", [])]
    texts += list(e.get("end_text", []))
    texts += [p.get("text", "") for p in e.get("pin", [])]
    texts += [str(v) for v in (e.get("copy") or {}).values()]
    hits = sorted({w for t in texts for w in BANNED if w in str(t)})
    if hits:
        raise SystemExit(f"剪輯單／文案有禁用說法 {hits}：老闆 11/09 更正只有「開鍋」由店員桌邊服務，請改成「店員桌邊開鍋」「第一鍋店員幫你開」。")
    return hits


def warn_scenes(e):
    """同一支原片（同檔名）合計超過 5 秒就警告（PLAYBOOK：同一場景總長不超過 5 秒）。只印警告、不擋出片。回傳超標清單（測試用）。"""
    try:
        names = {k: v.get("name", k).upper() for k, v in json.loads((ROOT / "manifest.json").read_text(encoding="utf-8")).items()}
    except Exception:
        names = {}
    tot = {}
    for c in e.get("clips", []):
        if c.get("id"):
            n = names.get(c["id"], c["id"])
            tot[n] = tot.get(n, 0) + (float(c["end"]) - float(c["start"])) / float(c.get("speed", 1.0))
    over = {n: round(t, 1) for n, t in tot.items() if t > 5.05}
    for n, t in over.items():
        print(f"⚠️ 同一場景 {n} 合計 {t} 秒（規則 5 秒內），挑最好的兩刀就好")
    return over


def warn_pacing(e):
    """11/12 研究：照片、開場太久不換、字幕掛太久。只印警告、不擋出片。回傳警告清單（測試用）。"""
    msgs = []
    clips = e.get("clips", [])
    if any(c.get("photo") for c in clips):
        msgs.append("剪輯單有 photo：老闆 11/12「全部都要影片，不要硬塞圖片」，請換成影片片段")
    first, t = None, 0.0
    for c in clips:
        key = c.get("id") or c.get("photo")
        if first is None:
            first = key
        if key != first:
            break
        t += float(c.get("dur", 0.8)) if c.get("photo") else (float(c["end"]) - float(c["start"])) / float(c.get("speed", 1.0))
    if t > 3.05:
        msgs.append(f"開場同一場景連續 {t:.1f} 秒才換畫面（高流量片 1～2 秒就切到食物），開場那刀剪到 3 秒內")
    for cap in e.get("captions", []):
        d = float(cap["end"]) - float(cap["start"])
        if d > 4.55:
            msgs.append(f"字幕「{cap.get('text', '')}」掛了 {d:.1f} 秒，超過 4.5 秒：畫面換了字也要換，或縮短那段")
    for m in msgs:
        print("⚠️ " + m)
    return msgs


def warn_dupes(e):
    """11/13 研究：抖音 v4 置頂字「醬油最後才淋」跟最後一句字幕重複、開場 2.5 秒 hook 跟 pin 疊在同一高度變亂碼。
    字（去空白）在 hook／pin／字幕／片尾之間重複就警告（老闆規則：字不重複）。只印不擋，回傳警告清單（測試用）。"""
    msgs, seen = [], {}
    h = e.get("hook") or {}
    srcs = [("hook", h.get("title", "")), ("hook", h.get("sub", ""))] + [("hook", t) for t in h.get("stack", [])]
    srcs += [("置頂", p.get("text", "")) for p in e.get("pin", [])]
    srcs += [("字幕", c.get("text", "")) for c in e.get("captions", [])]
    srcs += [("片尾", t) for t in e.get("end_text", [])]
    for where, t in srcs:
        k = "".join(str(t).split())
        if not k:
            continue
        if k in seen:
            msgs.append(f"「{t}」在{seen[k]}和{where}重複出現（字不重複）：刪掉其中一處")
        else:
            seen[k] = where
    if h and e.get("pin"):
        msgs.append("同時有 hook 和 pin：兩個都放在 TITLE_Y 會疊字，pin 已自動改成 2.5 秒後才出現（B 套抖音建議不用 pin）")
    for m in msgs:
        print("⚠️ " + m)
    return msgs


def clip_dur(c):
    return float(c.get("dur", 0.8)) if c.get("photo") else (float(c["end"]) - float(c["start"])) / float(c.get("speed", 1.0))


# 11/18 檢討：開場「淋醬油」與第 16 秒「冒煙」是同一支原片相隔 0.6 秒的同一次淋醬油（tag 不同，舊警告都沒抓到）；
# 4.8～10.8 秒抹油、下糖、化糖 6 秒只有空鍋與糖水，只有「抹油」標 nofood。
# → 同義動作視為同一個 tag；這些動作即使沒標 nofood 也算「沒有食物」。
ACTION_ALIAS = {"冒煙": "淋醬油", "起霧": "淋醬油", "倒醬油": "淋醬油", "淋醬汁": "淋醬油",
                "化糖": "下糖", "撒糖": "下糖", "翻生肉": "翻肉", "翻熟肉": "翻肉",
                # 11/19 檢討：IG 5～14 秒「下肉→拎起和牛→煎香→貼糖煎」4 個 tag 都是生和牛躺在糖上，連續 8.4 秒沒變色；
                # 開場「夾起」與第 21 秒「蛋碗」都是夾肉滑進蛋碗，同一動作出現兩次。
                "下肉": "生肉貼糖", "拎起和牛": "生肉貼糖", "煎香": "生肉貼糖", "貼糖煎": "生肉貼糖", "貼糖": "生肉貼糖",
                "蛋碗": "沾蛋", "滑進蛋": "沾蛋", "夾起進蛋": "沾蛋"}
NOFOOD_TAGS = {"抹油", "下糖", "空鍋", "加水", "木桶", "招牌", "店門"}


def canon(tag):
    return ACTION_ALIAS.get(tag, tag) if tag else None


def is_nofood(c):
    return bool(c.get("nofood")) or canon(c.get("tag")) in NOFOOD_TAGS


def warn_food(e):
    """11/14 檢討：v3 第 2～12 秒是空湯鍋、木桶、招牌，10 秒沒有食物；倒醬油出現 3 次（老闆 11/14：同一動作只留一次）。
    clip 可選填 "nofood": true（畫面沒有能吃的東西）與 "tag": "倒醬油"（動作名稱）。只印不擋，回傳警告清單（測試用）。"""
    msgs, t, nf_all, nf_early, last_tag, used = [], 0.0, 0.0, 0.0, None, set()
    for c in e.get("clips", []):
        d = clip_dur(c)
        if is_nofood(c):
            nf_all += d
            nf_early += max(0.0, min(t + d, 10.0) - min(t, 10.0))
        tag = canon(c.get("tag"))
        if tag and tag != last_tag:
            if tag in used:
                msgs.append(f"動作「{tag}」在片中出現不只一次（老闆 11/14：同一動作只留最好的一段）")
            used.add(tag)
        last_tag = tag
        t += d
    if nf_early > 1.55:
        msgs.append(f"前 10 秒有 {nf_early:.1f} 秒沒有食物（nofood），最多 1.5 秒：老闆「越看越想吃」")
    if nf_all > 3.05:
        msgs.append(f"沒有食物的畫面合計 {nf_all:.1f} 秒，最多 1 刀（3 秒內）")
    clips = e.get("clips", [])
    if clips and is_nofood(clips[0]):
        msgs.append("第一刀沒有食物（nofood）：11/15 研究 5 支高流量片有 4 支第 0.2 秒就是食物（和牛盤、夾起拉高、整隻雞吊起）")
    slug = str(e.get("slug", ""))
    rng = (30, 35) if "-ig" in slug else (27, 32) if "-tiktok" in slug else (7, 15) if "-short" in slug else None
    if rng and not (rng[0] - 0.05 <= t <= rng[1] + 0.05):
        msgs.append(f"片段合計 {t:.1f} 秒，不在 {rng[0]}～{rng[1]} 秒（不含片尾延長）：補一刀食物或剪短")
    for m in msgs:
        print("⚠️ " + m)
    return msgs


def warn_near(e, gap=4.0):
    """11/16 檢討：IG 倒醬油用了原片 86.8～89.6 與 92.8～95.6 兩刀（只有一刀標 tag，程式沒抓到），
    生肉在鍋裡也在 7.6 秒與 15.4 秒各出現一次。同一支原片、原片時間相隔不到 gap 秒的兩刀，
    多半是同一個動作被切兩次 → 印⚠️ 提醒（兩刀標了不同 tag 就不算）。只印不擋，回傳警告清單（測試用）。"""
    msgs, seen = [], []
    for i, c in enumerate(e.get("clips", [])):
        if not c.get("id"):
            continue
        s, en = float(c["start"]), float(c["end"])
        for j, (fid, s2, e2, tag2) in seen:
            if fid != c["id"]:
                continue
            tag = canon(c.get("tag"))
            if tag and tag2 and tag != canon(tag2):
                continue
            dist = max(s - e2, s2 - en, 0.0)
            if dist < gap:
                msgs.append(f"第 {j + 1} 刀（原片 {s2:g}～{e2:g}）和第 {i + 1} 刀（原片 {s:g}～{en:g}）只差 {dist:.1f} 秒，"
                            "可能是同一動作切兩次（老闆 11/14：一個動作只留最好的一段）；確定不同就各標不同 tag")
        seen.append((i, (c["id"], s, en, c.get("tag"))))
    for m in msgs:
        print("⚠️ " + m)
    return msgs


def warn_run(e, limit=3.5):
    """11/17 檢討：IG 16～22 秒「翻生肉」「翻肉」「翻肉」連 3 刀共 6.6 秒，其中兩刀「翻肉」是不同原片（換角度）相鄰，
    warn_food 只抓不相鄰的重複、warn_near 只抓同一原片，兩個都沒抓到。
    → 相鄰同 tag（或 tag 去掉「生／熟」後相同）連續合計 > limit 秒、或相鄰同 tag 來自不同原片，印⚠️。
    最後一刀（片尾停格）不算。只印不擋，回傳警告清單（測試用）。"""
    msgs, clips = [], e.get("clips", [])
    norm = lambda t: canon(str(t).replace("生", "").replace("熟", "")) if t else None
    i = 0
    while i < len(clips):
        tag = norm(clips[i].get("tag"))
        j = i
        while tag and j + 1 < len(clips) and norm(clips[j + 1].get("tag")) == tag:
            j += 1
        if tag and j > i and j < len(clips) - 1:
            run_d = sum(clip_dur(c) for c in clips[i:j + 1])
            ids = {c.get("id") or c.get("photo") for c in clips[i:j + 1]}
            if run_d > limit:
                msgs.append(f"第 {i + 1}～{j + 1} 刀都是「{tag}」，連續 {run_d:.1f} 秒（同一動作最多 {limit:g} 秒，留最好的一刀，換下一個更想吃的畫面）")
            elif len(ids) > 1:
                msgs.append(f"第 {i + 1}～{j + 1} 刀「{tag}」是不同原片換角度接在一起（老闆 11/14：一個動作只留最好的一段）")
        i = j + 1
    for m in msgs:
        print("⚠️ " + m)
    return msgs


FORMATS = ("倒帶型", "單品快版", "一鏡到底", "品項連發", "情境型", "特寫型", "開店前EP", "二選一")


def warn_format(e, edl_path=None, days=2):
    """11/19 行銷長第 11 條（老闆：怕觀眾看了會疲乏）：主片類型每天輪替，連續 3 天不能同一型。
    -ig／-tiktok 主片沒寫 "format" 印⚠️；同目錄前 days 天的同平台剪輯單都是同一型也印⚠️。只印不擋，回傳警告清單（測試用）。"""
    msgs, slug = [], str(e.get("slug", ""))
    plat = "-ig" if "-ig" in slug else "-tiktok" if "-tiktok" in slug else None
    if not plat:
        return msgs
    fmt = e.get("format")
    if not fmt:
        msgs.append(f"主片沒寫 \"format\"（類型名，例：{'、'.join(FORMATS[:4])}…）：行銷長 11/19 主片類型每天輪替")
    elif edl_path and slug[:8].isdigit():
        import datetime as _dt
        d0 = _dt.date(int(slug[:4]), int(slug[4:6]), int(slug[6:8]))
        prev = []
        for k in range(1, days + 1):
            day = (d0 - _dt.timedelta(days=k)).strftime("%Y%m%d")
            f = Path(edl_path).parent / f"{day}{plat}.json"
            if f.exists():
                try:
                    prev.append(json.loads(f.read_text(encoding="utf-8")).get("format") or "倒帶型")
                except Exception:
                    pass
        if len(prev) == days and all(x == fmt for x in prev):
            msgs.append(f"「{fmt}」已連續 {days + 1} 天（含今天），老闆 11/19：連續 3 天不能用同一型，換一型")
    for m in msgs:
        print("⚠️ " + m)
    return msgs


def _overlap(a, b):
    return max(0.0, min(float(a["end"]), float(b["end"])) - max(float(a["start"]), float(b["start"])))


def warn_reuse(e, edl_path=None, days=7, ratio=0.5):
    """11/21 檢討：情境型換了 hook 字，但結尾「肉躺在蛋碗裡」（1kMucL 30.3～34.6 秒）11/19 主片、抖音、單品快版、11/21 兩支都用，
    第 5 條「同一片段 7 天內不要用超過 2 次」程式沒抓（老闆 11/19：怕觀眾疲乏）。比對同目錄前 days 天所有剪輯單（同一支原片、重疊 ≥ 1 秒）：
    某一刀在前 7 天已有 2 天用過（今天是第 3 天）、第一刀前 3 天用過、或全片 ≥ ratio 秒數是前 7 天用過的，印⚠️。只印不擋，回傳警告清單（測試用）。"""
    msgs, slug = [], str(e.get("slug", ""))
    if not (edl_path and slug[:8].isdigit()):
        return msgs
    import datetime as _dt
    d0 = _dt.date(int(slug[:4]), int(slug[4:6]), int(slug[6:8]))
    old = []
    for k in range(1, days + 1):
        day = (d0 - _dt.timedelta(days=k)).strftime("%Y%m%d")
        for f in sorted(Path(edl_path).parent.glob(f"{day}-*.json")):
            try:
                old += [(k, day, c) for c in json.loads(f.read_text(encoding="utf-8")).get("clips", []) if c.get("id")]
            except Exception:
                pass
    clips = [c for c in e.get("clips", []) if c.get("id")]
    if not clips or not old:
        return msgs
    tot = sum(float(c["end"]) - float(c["start"]) for c in clips)
    rep = 0.0
    for i, c in enumerate(clips):
        hits = [(k, d) for k, d, o in old if o["id"] == c["id"] and _overlap(c, o) >= 1.0]
        used = sorted({d for _, d in hits})
        if hits:
            rep += max(_overlap(c, o) for _, _, o in old if o["id"] == c["id"])
        if len(used) >= 2:
            msgs.append(f"第 {i + 1} 刀（{c.get('tag') or c['id'][:6]} {c['start']}～{c['end']}）前 {days} 天已在 {'、'.join(used)} 用過：第 5 條同一片段 7 天內最多 2 次，換一段")
        elif i == 0 and any(k <= 3 for k, _ in hits):
            msgs.append(f"第一刀跟 {used[0]} 剪過的是同一段原片：開場畫面要換（類型換了，畫面也要換）")
    if tot and rep / tot >= ratio:
        msgs.append(f"全片 {rep:.1f}/{tot:.1f} 秒（{rep / tot:.0%}）是前 {days} 天剪過的同一段：換類型也要換畫面")
    for m in msgs:
        print("⚠️ " + m)
    return msgs


def warn_sfx(e, limit=6):
    """11/21 檢討：IG 版 11 個音效，7 個 bubble 每句字幕各配一個（B 套：音效最多 4 個＋點綴 2 個，字幕不再配啵）。
    音效 > limit 個、或 ≥ 3 個音效剛好落在字幕出現的那一刻（±0.1 秒），印⚠️。只印不擋，回傳警告清單（測試用）。"""
    msgs, sfx = [], e.get("sfx", [])
    starts = [float(c["start"]) for c in e.get("captions", [])]
    on_cap = sum(1 for x in sfx if any(abs(float(x.get("at", -9)) - t) <= 0.1 for t in starts))
    if len(sfx) > limit:
        msgs.append(f"音效 {len(sfx)} 個，超過 {limit} 個（B 套：開場／換段落／片尾 4 個＋點綴最多 2 個）")
    if on_cap >= 3:
        msgs.append(f"{on_cap} 個音效落在字幕出現的那一刻：B 套字幕不再配啵，只留換段落與片尾")
    for m in msgs:
        print("⚠️ " + m)
    return msgs


def warn_layout(e):
    """11/23 檢討：①IG／抖音「生啤酒」單句 y=0.8 掉到畫面下方，其他字幕都在上方（老闆 11/23：每段小字幕位置每支固定一致，不要忽上忽下）；
    ②開場淋醬油（1faSx 10.2～12.5）跟第 13～18 秒「洋蔥 豆腐 蔥段」是同一支原片、同一個鍋同一個擺法，觀眾會覺得同一畫面看兩次。
    字幕個別指定 y 且跟 caption_y 差 > 0.05、或第一刀的原片在片中又用一次，印⚠️。只印不擋，回傳警告清單（測試用）。"""
    msgs, cy = [], float(e.get("caption_y", 0.1))
    for cap in e.get("captions", []):
        if "y" in cap and abs(float(cap["y"]) - cy) > 0.05:
            msgs.append(f"字幕「{cap.get('text')}」y={cap['y']} 跟其他字幕（caption_y {cy}）不同高：老闆 11/23 小字幕位置要固定，換畫面或改字，不要移字")
    clips = [c for c in e.get("clips", []) if c.get("id")]
    if clips:
        again = [i + 1 for i, c in enumerate(clips[1:], 1) if c["id"] == clips[0]["id"]]
        if again:
            msgs.append(f"第一刀的原片在第 {'、'.join(map(str, again))} 刀又出現（同一個鍋、同一個擺法）：開場畫面片中不要再看到，換另一支原片")
    for m in msgs:
        print("⚠️ " + m)
    return msgs


def warn_zoom(c, src):
    """zoom 後保留的寬度太少（< 640 像素）會放大太多、畫面偏糊，印警告（11/11 研究：1080p 原片 w 0.55 已偏軟）。"""
    z = c.get("zoom")
    if not z:
        return None
    try:
        short = min(int(x) for x in probe(src, "stream=width,height").split(",")[:2])
    except Exception:
        return None
    px = int(short * float(z.get("w", 0.6)))
    if px < 640:
        print(f"⚠️ {c.get('id')} zoom 後只剩約 {px} 像素寬，要放大 {W / px:.1f} 倍會偏糊：1080p 原片 w 用 0.6 以上，或改用 4K 原片")
    return px


def main(edl_path):
    e = json.loads(Path(edl_path).read_text(encoding="utf-8"))
    check_words(e)
    warn_scenes(e)
    warn_pacing(e)
    warn_dupes(e)
    warn_food(e)
    warn_near(e)
    warn_run(e)
    warn_format(e, edl_path)
    warn_reuse(e, edl_path)
    warn_sfx(e)
    warn_layout(e)
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
        src = fetch(c["id"], tmp)
        warn_zoom(c, src)
        has_audio = "audio" in subprocess.run(["ffprobe", "-v", "error", "-show_entries", "stream=codec_type", "-of", "csv=p=0", str(src)],
                                              capture_output=True, text=True).stdout
        hdr = probe(src, "stream=color_transfer") in ("arib-std-b67", "smpte2084")
        speed = float(c.get("speed", 1.0))
        dur = float(c["end"]) - float(c["start"])
        base = f"{trim(c)}scale={W}:{H}:force_original_aspect_ratio=increase:flags=lanczos,crop={W}:{H},setsar=1,setpts=PTS/{speed},fps=30"
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
            base = (f"{trim(c)}scale={W}:{H}:force_original_aspect_ratio=increase:flags=lanczos,crop={W}:{H},setsar=1,setpts=PTS/{speed},fps=30,"
                    f"scale=w='{W}*(1+0.15*max(0,1-t/0.35))':h='{H}*(1+0.15*max(0,1-t/0.35))':eval=frame,crop={W}:{H},setsar=1")
        if e.get("grade", True):
            base = f"{base},{GRADE}"
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
        # 封面標題固定位置（老闆 2026-11-09：IG 主頁格子會把 9:16 裁成 3:4，上下各切掉 240px，標題位置不一致又會被切掉）
        # 一律放在 TITLE_Y，不再接受剪輯單自訂高度，讓主頁每一格的標題都在同一個位置、完整看得到
        hy = TITLE_Y
        stack = [str(x) for x in hook.get("stack", []) if str(x).strip()][:3]
        if stack:  # 11/20 研究：大標一行一行疊出來（@want.2.eat 54 萬：台中新開→200多元→吃到飽，每 0.5 秒多一行）
            for j, ln in enumerate(stack):
                last = j == len(stack) - 1
                draws.append(text(ln, 104, "0xF5C518" if last else "white", hy + j * 124, round(j * 0.45, 2), 2.5, 8))
            if hook.get("sub"):
                draws.append(text(hook["sub"], 60, "white", hy + len(stack) * 124 + 16, 0, 2.5))
        else:
            draws.append(text(hook["title"], 104, "0xF5C518", hy, 0, 2.5, 8))
            if hook.get("sub"):
                draws.append(text(hook["sub"], 60, "white", hy + 140, 0, 2.5))
    # 抖音式置頂大字（整支都在，無底色、粗黑邊）：避開最上方 220px 的系統列
    pin_t0 = 2.5 if hook else 0  # 11/13：hook 跟 pin 同高度會疊成亂碼 → 有 hook 時 pin 等 hook 結束才出現
    for j, ln in enumerate(e.get("pin", [])):
        draws.append(text(ln["text"], int(ln.get("size", 92)), ln.get("color", "white"), TITLE_Y + j * 118, pin_t0, total + 1, 9))
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
    # IG 主頁格子預覽（中間 3:4），檢查標題有沒有完整出現在格子裡
    run(["ffmpeg", "-v", "error", "-y", "-i", str(out_dir / f"{e['slug']}.jpg"), "-vf", "crop=1080:1440:0:240", "-q:v", "3",
         str(out_dir / f"{e['slug']}_grid.jpg")])
    print("完成", final, round(total, 1), "秒", final.stat().st_size // 1024, "KB")


if __name__ == "__main__":
    for p in sys.argv[1:]:
        main(p)
