#!/bin/bash
# 自我測試：用 espeak-ng 合成一段有停頓的中文人聲 → 自動字幕＋剪停頓 → 剪成片 → 抽格，結果放 eason/reels/selftest/
set -e
D=/tmp/esr_selftest; mkdir -p $D; cd "$(dirname "$0")/../../.."
i=0; for s in "大家好，我是壹神" "今天在胡志明的咖啡店看台指期" "先看生命線跟停損"; do
  espeak-ng -v cmn -s 150 -w $D/s$i.wav "$s"; i=$((i+1)); done
ffmpeg -v error -y -i $D/s0.wav -i $D/s1.wav -i $D/s2.wav -f lavfi -t 1.0 -i anullsrc=r=22050:cl=mono -f lavfi -t 0.8 -i anullsrc=r=22050:cl=mono \
  -filter_complex "[0][3][1][4][2]concat=n=5:v=0:a=1[a]" -map "[a]" $D/voice.wav
DUR=$(ffprobe -v error -show_entries format=duration -of csv=p=0 $D/voice.wav)
ffmpeg -v error -y -f lavfi -i "testsrc2=s=1080x1920:r=30" -i $D/voice.wav -t $DUR -c:v libx264 -c:a aac $D/voice.mp4
cat > $D/selftest.json <<J
{"slug":"selftest","out_dir":"eason/reels/selftest/out","clips":[{"file":"$D/voice.mp4","start":0,"end":$DUR}]}
J
python3 eason/reels/tools/autocaption.py $D/selftest.json
python3 eason/reels/tools/render.py eason/reels/selftest/build/selftest.json
O=eason/reels/selftest/out; rm -f $O/selftest.mp4.keep
ffmpeg -v error -y -i $O/selftest.mp4 -vf "fps=2,scale=270:-1,tile=6x2" -frames:v 1 $O/frames.jpg
echo "原長 $DUR 秒 → 成片 $(ffprobe -v error -show_entries format=duration -of csv=p=0 $O/selftest.mp4) 秒" | tee $O/result.txt
rm -f $O/selftest.mp4   # 成片不進 repo，只留抽格與字幕
