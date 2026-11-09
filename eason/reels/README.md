# 壹神 旅途 Reels（行銷長｜壹神個人品牌）

**規格以 eason-reels-editing 技能為準**（本檔不另訂規格，有衝突以技能為準）。重點：
- 長度 15～25 秒（最長 35 秒），**第一秒就要有聲音**（人聲或現場聲），前 2 秒放最有張力的畫面＋一句鉤子字幕。
- **畫面不放免責聲明**（老闆 11/09 決定）：免責一律寫在 post.json 文案最後，IG／抖音／YouTube 說明欄都要有。資料來源與期間可以留在畫面。
- 沒有 logo、沒有片尾卡；字幕白字黑邊約 62px、畫面約 7 成高度、一句一行、專有名詞黃色、不蓋臉。
- 連載「交易老師的移動辦公室 Day N」；每支至少一個電腦／看盤／時間差畫面。

## 素材
Google 雲端「壹神_旅途素材」（ID 1kGm7kWAHZzCWpAU2M0j6EI_VcEiLIYpV）。已處理的檔記在 manifest.json。

## 一鍵流程（行銷長只要寫剪輯單）
1. 把剪輯單放到 `eason/reels/edl/<日期>-dayN.json`（格式見 tools/render.py 開頭說明）並 push。
2. GitHub Actions「壹神旅途 Reels」自動跑：
   - **自動字幕**（tools/autocaption.py）：有人聲的片段用 faster-whisper 轉文字 → OpenCC 轉台灣繁體 → 套專有名詞表（壹神、台指期、TradingView、VWAP、生命線、停損、胡志明、交易員）→ 一句一行字幕。
   - **剪停頓**：有人聲的片段把超過 0.35 秒的停頓剪掉，切點前後各留 0.1 秒；純空景不處理。
   - **合規檢查**：字幕有禁用語（買進、賣出、賺、獲利、私訊、操盤…）就不剪，留 `out/<slug>.合規未過.txt`。
   - 剪成片 `out/<slug>.mp4`＋封面 `.jpg`；逐句字幕在 `build/<slug>.captions.txt` 給 AI 設計師＋合規審。單支失敗不影響其他支。
3. 審過後排程到 eason-autopost/queue/ 隔天 12:30（文案最後要有免責）。

不要自動字幕：剪輯單加 `"auto": false` 並自己寫 captions；某段當空景：該片段加 `"voice": false`。
自我測試：Actions 頁按「Run workflow」勾 selftest，結果在 `selftest/out/`。

駒澤屋的檔案（komazawa/）一律不動。
