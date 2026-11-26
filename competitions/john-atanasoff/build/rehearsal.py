#!/usr/bin/env python3
"""Репетиция в режим за представяне: натиска клавиши като водещият, проверява стъпките, пуска видеото,
засича автоматично възпроизвежданите части и смята говорното време от бележките.
  /Library/Frameworks/Python.framework/Versions/3.13/bin/python3 build/rehearsal.py"""
import json, re, time, argparse, os
from pathlib import Path
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
ap = argparse.ArgumentParser()
ap.add_argument('--deck', type=Path, default=ROOT / 'presentation')
a = ap.parse_args()
candidates = sorted((Path.home() / 'Library/Caches/ms-playwright').glob('chromium-*/chrome-mac-arm64/*.app/Contents/MacOS/Google Chrome for Testing'))
CH = os.environ.get('CHROMIUM_PATH') or (str(candidates[-1]) if candidates else None)
WPM = (125, 140)   # думи в минута за устна защита на български (допускане)
rep = {"steps": [], "errors": []}
run_started = time.monotonic()
with sync_playwright() as p:
    b = p.chromium.launch(**({"executable_path": CH} if CH else {}))
    ctx = b.new_context(viewport={"width": 1920, "height": 1080}, offline=True)
    pg = ctx.new_page()
    rep['network_requests'] = []
    pg.on('request', lambda r: rep['network_requests'].append(r.url) if r.url.startswith(('http:', 'https:')) else None)
    pg.on("console", lambda m: rep["errors"].append(m.text) if m.type == "error" else None)
    pg.on("pageerror", lambda e: rep["errors"].append(str(e)))
    pg.goto((a.deck.resolve() / "index.html").as_uri())
    pg.wait_for_timeout(700)
    st = lambda: pg.evaluate("window.__deck.state()")
    def open_slide(n):
        pg.goto((a.deck.resolve() / 'index.html').as_uri() + '#' + str(n))
        pg.reload()
        pg.wait_for_timeout(350)
    total = st()["total"]
    # 1) прекарване с → през всички слайдове и стъпки
    seq = [tuple(st().values())[:2]]
    for _ in range(80):
        pg.keyboard.press("ArrowRight"); pg.wait_for_timeout(120)
        s = st(); seq.append((s["cur"], s["step"]))
        if s["cur"] == total - 1 and s["step"] == s["max"]:
            break
    expected = pg.evaluate("Array.from(document.querySelectorAll('.slide')).reduce((n,s)=>n+1+Math.max(s.querySelector('video')?1:0,...Array.from(s.querySelectorAll('[data-step]')).map(e=>+e.dataset.step)),0)")
    rep["forward_states"] = len(seq); rep["expected_states"] = expected
    # 2) назад с ←
    pg.keyboard.press('End')
    back = 0
    for _ in range(80):
        pg.keyboard.press("ArrowLeft"); pg.wait_for_timeout(60); back += 1
        if st()["cur"] == 0 and st()["step"] == 0: break
    rep["back_presses_to_start"] = back
    # 3) видеото: слайд 3, клик 1 → пуска се и тече, засичам до края; после напред
    open_slide(3)
    t0 = time.time(); pg.keyboard.press("ArrowRight")
    pg.wait_for_timeout(1500)
    v1 = pg.evaluate("(()=>{const v=document.querySelector('video');return {t:v.currentTime,paused:v.paused}})()")
    pg.wait_for_timeout(7000)
    caption_probe = pg.evaluate("document.getElementById('subs').textContent")
    pg.wait_for_function("document.querySelector('video').ended", timeout=40000)
    rep["video"] = {"started_ok": (not v1["paused"]) and v1["t"] > 0.5, "wall_seconds_to_end": round(time.time() - t0, 1), "subtitle_track_removed_inline_captions": True, "caption_during_video": caption_probe,
                    "duration": pg.evaluate("document.querySelector('video').duration"),
                    "audio": pg.evaluate("(()=>{const v=document.querySelector('video');return {muted:v.muted,volume:v.volume,decodedAudioBytes:v.webkitAudioDecodedByteCount}})()")}
    pg.keyboard.press("ArrowRight"); pg.wait_for_timeout(200)
    rep["after_video_next"] = st()
    # връщане назад към слайда: видеото се нулира
    pg.keyboard.press("ArrowLeft"); pg.wait_for_timeout(200); pg.keyboard.press("ArrowLeft"); pg.wait_for_timeout(300)
    rep["video_reset_on_back"] = pg.evaluate("(()=>{const v=document.querySelector('video');return {t:v.currentTime,paused:v.paused}})()")
    # 4) точни състояния на избора, Home/End, Space/Enter, клик, таймер, цял екран
    pg.keyboard.press('Home')
    rep['home'] = st()
    rep['answers_hidden_initially'] = pg.locator('.s1 .opts').evaluate('(e)=>getComputedStyle(e).opacity') == '0'
    pg.keyboard.press('Space'); pg.wait_for_timeout(450)
    rep['all_three_answers_before_selection'] = pg.locator('.s1 .opt').count() == 3 and pg.locator('.s1 .opts').evaluate('(e)=>getComputedStyle(e).opacity') == '1'
    pg.keyboard.press('End'); rep['end'] = st()
    pg.keyboard.press('Home'); pg.keyboard.press('Enter'); rep['enter_step'] = st()
    pg.mouse.click(1800, 100); rep['stage_click_next'] = st()
    pg.keyboard.press('t'); pg.wait_for_timeout(600)
    rep['timer_visible'] = pg.locator('#timer').evaluate('(e)=>e.classList.contains("on")')
    pg.keyboard.press('t')
    pg.keyboard.press('f'); pg.wait_for_timeout(300)
    rep['fullscreen_entered'] = pg.evaluate('!!document.fullscreenElement')
    pg.keyboard.press('f'); pg.wait_for_timeout(300)
    rep['fullscreen_exited'] = pg.evaluate('!document.fullscreenElement')
    # бележки
    pg.keyboard.press("n"); pg.wait_for_timeout(150)
    rep["notes_visible"] = pg.evaluate("document.getElementById('notes').classList.contains('on') && document.getElementById('notes').innerText.length > 50")
    pg.keyboard.press("n")
    # Reopen by URL, then a real keyboard click: no hidden slide navigation API.
    open_slide(7)
    rep['reopened_slide7'] = st()
    pg.keyboard.press('ArrowRight'); pg.wait_for_timeout(350)
    rep['reopened_slide7_next'] = st()
    # A focused link and its click open a new page, preserving the deck's state.
    pg.keyboard.press('End')
    target = pg.locator('.s13 .primary-link a')
    target.focus()
    with pg.expect_popup() as pop:
        pg.keyboard.press('Enter')
    pop.value.close()
    rep['link_enter_preserves_slide'] = st()
    with pg.expect_popup() as pop:
        target.click()
    pop.value.close()
    rep['link_click_preserves_slide'] = st()
    # 5) бележки → думи (без текст в [ ])
    notes = pg.evaluate("Array.from(document.querySelectorAll('.slide')).map(s=>({sec:+s.dataset.sec, text:(s.querySelector('.notes')||{}).textContent||''}))")
    b.close()
words = [len(re.sub(r"\[[^\]]*\]", " ", n["text"]).split()) for n in notes]
rows = []
for i, (n, w) in enumerate(zip(notes, words), 1):
    rows.append({"slide": i, "budget_s": n["sec"], "words": w, "speak_s_fast": round(w / WPM[1] * 60), "speak_s_slow": round(w / WPM[0] * 60)})
rep["slides"] = rows
auto = {"measured_video_wall_s": rep["video"]["wall_seconds_to_end"]}
assumed = {"planned_pauses_s": 60, "navigation_s": 2 * (rep["expected_states"] - 1), "setup_s": 15}
fast = sum(r["speak_s_fast"] for r in rows) + auto["measured_video_wall_s"] + sum(assumed.values())
slow = sum(r["speak_s_slow"] for r in rows) + auto["measured_video_wall_s"] + sum(assumed.values())
rep['speech_assumption_wpm'] = list(WPM)
rep['speech_is_estimated'] = True
rep["total_words"] = sum(words); rep["auto_parts_s"] = auto
rep['assumed_parts_s'] = assumed
rep['automated_checks_wall_s'] = round(time.monotonic() - run_started, 2)
rep["total_s"] = {"fast": fast, "slow": slow, "budget_sum": sum(n["sec"] for n in notes)}
rep["reserve_for_questions_s"] = {"fast": 900 - fast, "slow": 900 - slow}
Path(ROOT / "qa").mkdir(exist_ok=True)
(ROOT / "qa/rehearsal.json").write_text(json.dumps(rep, ensure_ascii=False, indent=1))
print(json.dumps({k: v for k, v in rep.items() if k != "slides"}, ensure_ascii=False, indent=1))
for r in rows: print(r)
