#!/usr/bin/env python3
"""Рендира презентацията: снимка на всяка стъпка на всеки слайд (qa/shots), PDF (presentation/The_Last_Light_zashtita.pdf)
и DOM проверки (препълване, най-малък шрифт, контраст). Ползва Playwright от системния Python:
  /Library/Frameworks/Python.framework/Versions/3.13/bin/python3 build/render_deck.py [--w 1920 --h 1080]"""
import json, sys, argparse, os
from pathlib import Path
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
ap = argparse.ArgumentParser(); ap.add_argument("--w", type=int, default=1920); ap.add_argument("--h", type=int, default=1080)
ap.add_argument("--tag", default="full"); ap.add_argument("--no-pdf", action="store_true")
ap.add_argument("--deck", type=Path, default=ROOT / "presentation", help="Extracted jury ZIP directory")
a = ap.parse_args()
OUT = ROOT / "qa" / f"shots_{a.tag}"; OUT.mkdir(parents=True, exist_ok=True)

CHECK = """
() => {
  const res = []; const stage = document.getElementById('stage'); const sl = document.querySelector('.slide.on');
  const sb = stage.getBoundingClientRect();
  const kids = sl.querySelectorAll('*');
  let minFont = 999, minEl = '';
  kids.forEach(e => {
    const cs = getComputedStyle(e);
    if (cs.display === 'none' || cs.visibility === 'hidden' || +cs.opacity === 0) return;
    const r = e.getBoundingClientRect();
    if (r.width === 0 || r.height === 0) return;
    const hasText = Array.from(e.childNodes).some(n => n.nodeType === 3 && n.textContent.trim().length > 0);
    if (hasText) {
      const fs = parseFloat(cs.fontSize) * (sb.width / 1920);
      const fsDesign = parseFloat(cs.fontSize);
      if (fsDesign < minFont) { minFont = fsDesign; minEl = (e.className || e.tagName) + ': ' + e.textContent.trim().slice(0, 40); }
      // text outside the stage
      if (r.left < sb.left - 1 || r.right > sb.right + 1 || r.top < sb.top - 1 || r.bottom > sb.bottom + 1) res.push('outside stage: ' + e.textContent.trim().slice(0, 50));
      // text overflowing its own box
      if (e.scrollWidth > e.clientWidth + 2 && cs.overflow !== 'visible' && e.tagName !== 'VIDEO') res.push('h-overflow: ' + e.textContent.trim().slice(0, 50));
    }
  });
  // overlaps between visible text blocks of the main layers
  const blocks = Array.from(sl.querySelectorAll('.title, .kicker, .opts, .radio, .ask, .cards, .proof, .code, .tbl, .cap2, .flow, .metric, .callum, .cols, .banner, .mx, .endimg, .mxnote, .two, .who2, .big, .bars, .unc, .src, .final, .opts2, .links, .thanks, .vid, .cap, .bar, .stat'))
    .filter(e => { const cs = getComputedStyle(e); return +cs.opacity > 0 && cs.display !== 'none'; });
  for (let i = 0; i < blocks.length; i++) for (let j = i + 1; j < blocks.length; j++) {
    const A = blocks[i].getBoundingClientRect(), B = blocks[j].getBoundingClientRect();
    if (blocks[i].contains(blocks[j]) || blocks[j].contains(blocks[i])) continue;
    const ox = Math.min(A.right, B.right) - Math.max(A.left, B.left), oy = Math.min(A.bottom, B.bottom) - Math.max(A.top, B.top);
    if (ox > 6 && oy > 6) res.push('overlap: ' + (blocks[i].className || blocks[i].tagName) + ' x ' + (blocks[j].className || blocks[j].tagName) + ' (' + Math.round(ox) + 'x' + Math.round(oy) + ')');
  }
  return { issues: res, minFont, minEl };
}
"""

report = {"viewport": [a.w, a.h], "slides": []}
with sync_playwright() as p:
    browsers = sorted((Path.home() / "Library/Caches/ms-playwright").glob("chromium-*/chrome-mac-arm64/*.app/Contents/MacOS/Google Chrome for Testing"))
    executable = os.environ.get("CHROMIUM_PATH") or (str(browsers[-1]) if browsers else None)
    b = p.chromium.launch(**({"executable_path": executable} if executable else {}))
    context = b.new_context(viewport={"width": a.w, "height": a.h}, offline=True)
    pg = context.new_page()
    report["network_requests"] = []
    pg.on("request", lambda r: report["network_requests"].append(r.url) if r.url.startswith(("http:", "https:")) else None)
    pg.goto((a.deck.resolve() / "index.html").as_uri() + "#1")
    pg.evaluate("document.fonts.ready")
    pg.wait_for_timeout(800)
    n = pg.evaluate("window.__deck.state().total")
    for i in range(1, n + 1):
        pg.evaluate(f"window.__deck.go({i - 1})")
        mx = pg.evaluate("window.__deck.state().max")
        entry = {"slide": i, "steps": mx, "states": []}
        for st in range(0, mx + 1):
            pg.evaluate(f"window.__deck.setStep({st})")
            if st == 0:
                pg.evaluate("document.querySelectorAll('video').forEach(v=>{v.pause();v.currentTime=0})")
            pg.wait_for_timeout(450)
            shot = OUT / f"s{i:02d}_step{st}.png"
            pg.screenshot(path=str(shot))
            r = pg.evaluate(CHECK)
            entry.setdefault("issues", []).extend(f"step {st}: {x}" for x in r["issues"])
            entry["min_font_design_px"] = r["minFont"]; entry["min_font_el"] = r["minEl"]
            entry["states"].append(shot.name)
        report["slides"].append(entry)
    # images / fonts / video load
    report["broken_images"] = pg.evaluate("Array.from(document.images).filter(i=>!i.complete||i.naturalWidth===0).map(i=>i.src)")
    report["fonts"] = pg.evaluate("Array.from(document.fonts).filter(f=>f.status==='loaded').map(f=>f.family+' '+f.weight+' '+f.style)")
    report["video"] = pg.evaluate("(()=>{const v=document.querySelector('video');return {ready:v.readyState,dur:v.duration,w:v.videoWidth,h:v.videoHeight,tracks:v.textTracks.length}})()")
    if not a.no_pdf:
        pdfp = a.deck.resolve() / "The_Last_Light_zashtita.pdf"
        pg.evaluate("document.title = 'The Last Light · R7 · ' + document.querySelector('meta[name=deck-version]').content")
        pg.emulate_media(media="print")
        pg.pdf(path=str(pdfp), width="1920px", height="1080px", print_background=True, margin={"top": "0", "bottom": "0", "left": "0", "right": "0"})
        report["pdf"] = pdfp.name
    b.close()
(ROOT / "qa").mkdir(exist_ok=True)
(ROOT / "qa" / f"render_report_{a.tag}.json").write_text(json.dumps(report, ensure_ascii=False, indent=1))
bad = [s for s in report["slides"] if s["issues"]]
print("slides:", len(report["slides"]), "| with issues:", len(bad), "| broken images:", report["broken_images"], "| video:", report["video"])
for s in report["slides"]:
    print(f'  {s["slide"]:2d} steps={s["steps"]} minfont={s["min_font_design_px"]}px  {s["issues"]}')
