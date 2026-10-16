#!/bin/bash
# ブランドの公式サイトのキャプチャ（2026-10-16 MediaXAI「各サービス名の紹介箇所は該当の公式サイトをキャプチャの上、画像掲載して」）
#   bash scripts/capture-brands/run.sh [slug,slug]   撮影元は data/brand-captures.json。撮ったら必ず目視確認
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"; W=/tmp/capture-brands; mkdir -p "$W/png"
python3 -c "import json;print(json.dumps([[d['slug'],d['name'],d['url']] for d in json.load(open('$ROOT/data/brand-captures.json'))],ensure_ascii=False))" > "$W/items.json"
node "$(dirname "$0")/cap.mjs" "$W" "${1:-}"
python3 - "$ROOT" "$W" <<'PY'
import json,sys,datetime
from pathlib import Path
from PIL import Image
root,w=Path(sys.argv[1]),Path(sys.argv[2]); today=datetime.date.today().isoformat()
caps=json.load(open(root/'data/brand-captures.json'))
for c in caps:
    png=w/'png'/f"{c['slug']}.png"
    if not png.exists() or png.stat().st_mtime < datetime.datetime.now().timestamp()-3600: continue
    out=root/'public/images/brands'/f"{c['slug']}.webp"
    Image.open(png).convert('RGB').resize((1280,800),Image.LANCZOS).save(out,'WEBP',quality=82)
    kb=out.stat().st_size//1024; print(('⚠️ 小さい ' if kb<30 else 'ok ')+c['slug'],kb,'KB'); c['captured_at']=today
json.dump(caps,open(root/'data/brand-captures.json','w'),ensure_ascii=False,indent=1)
PY
