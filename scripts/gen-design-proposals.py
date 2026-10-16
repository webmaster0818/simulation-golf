#!/usr/bin/env python3
"""SIM GOLF SEARCH のデザイン案を Nano Banana Pro で作る（2026-10-16 MediaXAI「世界一洗練されたデザインに・明るい印象に」）。
  python3 scripts/gen-design-proposals.py [logo|fv|all]   → design-proposals/（リポには入れない）
⚠️ FV の数字は facilities.json で確かめた事実だけ: 掲載1,104施設（営業中）・47都道府県・24時間営業633・個室あり159。
   料金は表記がばらばらで「最安〇円」を言えないので使わない。
"""
import base64, json, os, sys, urllib.request
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent; OUT = ROOT / "design-proposals"; MODEL = "gemini-3-pro-image-preview"
def key():
    if os.environ.get("GEMINI_API_KEY"): return os.environ["GEMINI_API_KEY"]
    for l in (Path.home() / ".openclaw/workspace/secrets/shiroari-expert-keys.env").read_text().splitlines():
        if l.startswith("GEMINI_API_KEY="): return l.split("=", 1)[1].strip().strip('"')
LOGO = ("Minimal premium brand mark for a Japanese simulation-golf facility search website 'SIM GOLF SEARCH'. Monochrome line art "
        "in deep green-black #14211b on pure white, single consistent stroke weight, geometric, elegant, generous negative space, "
        "centered, crisp vector-like edges, no gradients, no shadows, no text. Concept: ")
LOGOS = {
  "logo-a-swing-arc": "an abstract golfer at the top of a driver swing, body drawn as one continuous line, the club path forming a perfect circle around the figure",
  "logo-b-screen-trace": "a simulator screen frame (rounded rectangle) with a ball flight trace arc drawn across it and a small golf ball at the start",
  "logo-c-driver-pin": "a driver club whose head forms the round head of a map location pin, suggesting search and golf together",
  "logo-d-ball-target": "a golf ball with dimples drawn as a few dots, inside concentric target rings like a launch-monitor radar",
  "logo-e-tee-magnifier": "a golf tee and ball where the ball is the lens of a magnifying glass, the tee is the handle",
}
FV_BASE = ("Website first-view hero design mockup, 16:9 desktop, for a Japanese simulation golf facility comparison site 'SIM GOLF SEARCH'. "
  "Bright, airy, premium, world-class refined design, lots of white space, thin 1px borders, no emoji, no clip art. "
  "Palette: white, very light warm gray #f4f5f2, deep green-black #14211b text, one fresh accent green #3d9a5b used sparingly. "
  "Large photorealistic image of a beautiful, brand-new indoor simulation golf studio: a huge high-definition simulator screen showing a "
  "sunny golf course, a premium hitting mat and turf, modern launch monitor on the floor, warm and bright architectural lighting, "
  "clean wood and white interior, inviting atmosphere, no people or one golfer seen from behind. "
  "All Japanese text rendered cleanly, legibly, exactly as given, no other text: small header logo text 'SIM GOLF SEARCH' and nav "
  "「エリアから探す」「条件から探す」「ブランド」「機材」, headline 「全国1,000以上のシミュレーションゴルフから、」「ベストを最短で見つける。」, "
  "two equal prominent buttons 「エリアから探す」「条件から探す」 in the same deep green-black, a row of small outlined chips 「24時間営業」「個室」「駐車場」「トラックマン」, "
  "and a stat bar with four items 「掲載 1,104施設」「対応 47都道府県」「24時間営業 633施設」「個室あり 159施設」. ")
FVS = {
  "fv-1-fullbleed": FV_BASE + "Layout: full-bleed bright photo of the studio across the whole hero, text on the left over a soft white fade, stat bar in a white band with thin dividers below.",
  "fv-2-split": FV_BASE + "Layout: left 45% white with the text and buttons, right 55% the studio photo in a large rounded rectangle; stat bar as four bordered white cards under the hero.",
  "fv-3-screen": FV_BASE + "Layout: the photo framed edge to edge, the headline placed centered in the upper area, buttons centered below it, and a thin white translucent stat strip along the bottom of the photo.",
}
def gen(name, prompt, aspect):
    out = OUT / f"{name}.png"
    if out.exists(): print("skip", name); return
    body = json.dumps({"contents": [{"parts": [{"text": prompt}]}], "generationConfig": {"responseModalities": ["IMAGE"], "imageConfig": {"aspectRatio": aspect, "imageSize": "2K"}}}).encode()
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{MODEL}:generateContent?key={key()}"
    with urllib.request.urlopen(urllib.request.Request(url, data=body, headers={"Content-Type": "application/json"}), timeout=240) as r:
        d = json.loads(r.read())
    for p in d["candidates"][0]["content"]["parts"]:
        if "inlineData" in p: out.write_bytes(base64.b64decode(p["inlineData"]["data"])); print("ok", name); return
    print("no image", name)
if __name__ == "__main__":
    w = sys.argv[1] if len(sys.argv) > 1 else "all"; OUT.mkdir(exist_ok=True)
    if w in ("logo", "all"):
        for n, c in LOGOS.items(): gen(n, LOGO + c, "1:1")
    if w in ("fv", "all"):
        for n, p in FVS.items(): gen(n, p, "16:9")
