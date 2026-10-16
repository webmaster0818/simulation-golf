#!/usr/bin/env python3
"""ロゴA（ドライバーを振り上げた人・スイング軌道の円）の色付け案（2026-10-16 MediaXAI「Aで、もっと色使い鮮やかに」）"""
import base64, json, urllib.request, importlib.util
from pathlib import Path
spec = importlib.util.spec_from_file_location("g", Path(__file__).parent / "gen-design-proposals.py"); g = importlib.util.module_from_spec(spec); spec.loader.exec_module(g)
OUT = Path(__file__).resolve().parent.parent / "design-proposals"
ref = base64.b64encode((OUT / "logo-a-swing-arc.png").read_bytes()).decode()
BASE = ("Using the attached logo as the exact base (keep the same composition: a golfer at the top of a driver swing drawn as one continuous "
        "line, with the circular swing path around the figure), create a vivid, colorful, premium version for the brand 'SIM GOLF SEARCH'. "
        "Flat vector, crisp, white background, centered, no text. ")
V = {
 "logo-a-color-1": BASE + "Palette: vivid fairway green #1fae5b circle, sky blue #2a9df4 inner sky segment behind the upper body, deep navy #12263a golfer line, a small bright yellow #ffc93c golf ball flying off the circle.",
 "logo-a-color-2": BASE + "Palette: the swing circle as a smooth vivid gradient from sky blue #2a9df4 at the top to fresh green #22c55e at the bottom (like sky to turf), golfer in deep navy #0f2238, a white golf ball with a thin trace.",
 "logo-a-color-3": BASE + "Palette: solid vivid green #16a34a circle badge with the golfer in white negative space, a thin bright lime #a3e635 ball-flight arc leaving the circle at the top right.",
}
for n, p in V.items():
    out = OUT / f"{n}.png"
    if out.exists(): continue
    body = json.dumps({"contents": [{"parts": [{"inlineData": {"mimeType": "image/png", "data": ref}}, {"text": p}]}],
                       "generationConfig": {"responseModalities": ["IMAGE"], "imageConfig": {"aspectRatio": "1:1", "imageSize": "2K"}}}).encode()
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{g.MODEL}:generateContent?key={g.key()}"
    with urllib.request.urlopen(urllib.request.Request(url, data=body, headers={"Content-Type": "application/json"}), timeout=240) as r:
        d = json.loads(r.read())
    for part in d["candidates"][0]["content"]["parts"]:
        if "inlineData" in part: out.write_bytes(base64.b64decode(part["inlineData"]["data"])); print("ok", n); break
