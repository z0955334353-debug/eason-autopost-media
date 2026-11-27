# 法人對決（每日盤後短影音）— 鉛筆手繪數據＋角色

第一支：11/27「外資連賣 10 天，台股卻漲？」（out/ 內為無配音版，23.5 秒，直式 1080×1920）。

## 格式（老闆 11/27 看過前兩版「無感」後改成這版）
1. 0～8 秒｜反差謎題：左邊外資賣超（數字跳表＋連賣長條），右邊台股走勢往上，大問號「錢到底是誰在接？」
2. 8～13 秒｜把數字變有感：外資 11 月累計 ÷ 台灣人口（內政部最新月底數）＝一人幾萬
3. 13～23.5 秒｜角色對決：外資灰貓在上面丟錢袋、投信橘貓接，雙方比分，結尾「第 N+1 天？」＋留言問題
- 深色底、紅漲綠跌；字幕每個逗號換行，底線 y=1500、中心 x=500（避開 IG 右側按鈕）
- 不放免責（寫在文案）；不給買賣建議；個股金額為「張數×收盤價」估算時，配音只說「八成」「最多」

## 配音（還沒做）
Fish Audio「壹神」聲音 0bed4880ffe948efb2d5d0ebbfd7580c，speed 1.1，數字寫國字。旁白稿＝main.js 的 LINES；目前按每秒 4.8 字預排，拿到配音後把每句起訖改成實際秒數再出片。

## 角色
目前是程式手繪的簡化版貓（main.js 的 cat()）。老闆原本 Kling 做的三大法人貓定裝照（外資灰色英短＋深藍西裝紅領帶墨鏡、投信橘貓＋白襯衫黑背帶褲藍識別證、自營商賓士貓）不在任何雲端倉庫，要從 Kling 帳號下載後放到 eason/characters/cats/，再改成用圖片。

## 怎麼出片（雲端工作區）
```sh
git clone --depth 1 https://github.com/lemomo-ai/lemo-opuscar.git ~/lemo && sh ~/lemo/plugin/skills/lemo-opuscar/scripts/setup.sh deps
sh tools/fonts.sh                      # 字型不進 git
python3 mix.py out/mix.wav             # 音效
# 需要 ffmpeg 7：pip install imageio-ffmpeg，把它附的 ffmpeg-linux-x86_64-v7.* 連到 PATH 最前面的 ffmpeg
cd ~/lemo && node core/render/still.mjs <本資料夾> 1 6 12 18 --size 1080x1920      # 先看截圖
node core/render/video.mjs <本資料夾> --fps 24 --workers 3 --size 1080x1920 --out <本資料夾>/out/video.mp4
sh core/render/mux.sh <本資料夾>/out/video.mp4 <本資料夾>/out/mix.wav <成品.mp4> 24 0
```
engine.js 是 Lemo Opuscar「dataviz」風格引擎改成直式（MIT）；風格說明是 CC BY-NC，不搬進來。11/27 人工檢查過程式碼：沒有 hooks、不讀金鑰。setup.sh 每次會自動更新上游，所以只裝在雲端，不裝到放永豐金鑰的電腦。

## 每日資料
- data/fetch_bfi82u.py：抓證交所 BFI82U 逐日三大法人（工作區用 curl 才連得到，Python urllib 會被代理擋）
- 指數：FMTQIK；個股：T86＋MI_INDEX ALLBUT0999；產業別：isin.twse.com.tw strMode=2
- 11/27 數字：外資 −296.3（連賣第 10 天，10 天 −5,004.7）、11 月累計 −11,216.4、投信 +85.2；加權 39,308.08（兩天 +1,112.65）
