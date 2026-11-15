#!/usr/bin/env bash
# narration (one pass, word cues) -> score -> map render -> SFX bed -> mix (voice always clear) -> master + share copy -> audio QA
# usage: ./make_video.sh <slug> [--skip-voice] [--skip-render]
set -euo pipefail
cd "$(dirname "$0")"
EP=${1:?usage: ./make_video.sh <slug>}; shift || true
BD=build/$EP; mkdir -p $BD out; TMP=${TMPDIR:-/tmp}
[[ " $* " == *" --skip-voice "* ]] || env -u HTTP_PROXY -u HTTPS_PROXY -u http_proxy -u https_proxy -u ALL_PROXY -u all_proxy python3 voice.py episodes/$EP.json
python3 qa.py check $EP
read END HITS < <(python3 -c "import importlib,sys;sys.path.insert(0,'.');e=importlib.import_module('episodes.$EP');print(e.END, ','.join(str(round(x,2)) for x in e.HITS))" | tail -n 1)
python3 music.py "$END" "$HITS" $BD/music.wav
[[ " $* " == *" --skip-render "* ]] || python3 render.py $EP
python3 sfx.py $EP $BD/sfx.wav
ffmpeg -y -v error -i $BD/video.mp4 -i $BD/narration.wav -i $BD/music.wav -i $BD/sfx.wav -filter_complex \
 "[1:a]aresample=48000:resampler=soxr,highpass=f=80,equalizer=f=250:t=q:w=1:g=-2.5,equalizer=f=3800:t=q:w=1.4:g=2.5,equalizer=f=9000:t=h:w=0.7:g=1.5,deesser=i=0.35,acompressor=threshold=-22dB:ratio=2.5:attack=12:release=220:knee=6,loudnorm=I=-14:TP=-2:LRA=6,asplit=2[vo][sc];\
  [2:a]loudnorm=I=-34:TP=-9:LRA=11,aecho=0.8:0.5:60:0.10[m];\
  [3:a]volume=-7dB,equalizer=f=2500:t=q:w=1.2:g=-6,equalizer=f=1000:t=q:w=1:g=-3[fx0];[fx0][sc]sidechaincompress=threshold=0.02:ratio=10:attack=8:release=350:makeup=1[fx];\
  [vo][fx][m]amix=inputs=3:normalize=0:duration=first,alimiter=limit=0.89:level=false[a]" \
 -map 0:v -map "[a]" -c:v copy -c:a aac -b:a 192k -shortest -movflags +faststart $TMP/${EP}_master.mp4
cp $TMP/${EP}_master.mp4 out/${EP}_master.mp4
ffmpeg -y -v error -i $TMP/${EP}_master.mp4 -c:v libx264 -preset medium -crf 22 -c:a copy -movflags +faststart $TMP/${EP}_1080p.mp4
cp $TMP/${EP}_1080p.mp4 out/${EP}_1080p.mp4
python3 qa.py audio $EP
python3 qa.py describe $EP > out/${EP}_description.txt || true
ls -lh out/ | grep $EP
echo DONE
