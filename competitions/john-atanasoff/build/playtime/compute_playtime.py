#!/usr/bin/env python3
"""Ориентировъчно време за игра на THE LAST LIGHT — повторяемо изчисление.

Вход:  out/realtime.txt (ред на изпълнение: run_realtime.sh; ботът играе кампанията с пълни скриптови
       чакания и с времето на всеки ред диалог по формулата на dialogue_ui.gd).
       godot/data/story/chapters.json (брой задължителни стъпки на дежурствата).
Изход: out/playtime.json, out/PLAYTIME.md, out/deck_tokens.json (за слайд 11 и документите).

Стартиране:  tools/py competitions/john-atanasoff/build/playtime/compute_playtime.py
Допускания — вижте METHOD.md. Накратко: времето на реда диалог НЕ зависи от скоростта на четене на играча
(ред се сменя сам; прескачане няма — audit D1); скоростта се проявява само чрез настройката Reading time (×0,75…×3)
и чрез времето за избор на отговор.
"""
from __future__ import annotations

import json
import re
import statistics
from collections import defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
OUT = HERE / "out"
CHAPTERS = HERE.parents[3] / "projects/games/last_light/godot/data/story/chapters.json"

# ---- допускания за човешката част (секунди), низко / средно / високо -----------------------------------------
STEP_S = {"low": 8, "mid": 20, "high": 35}          # допълнително време за една задължителна стъпка на дежурство
STEP_HIDDEN = 0.6                                   # част от него не е скрита зад чакане/плаване на корабите
DOCS = 9                                            # дневници, писмо, бележки, снимки (read_* и after_read)
DOC_S = {"low": 15, "mid": 40, "high": 60}          # четене на един документ
OPTIONAL_S = {"low": 0, "mid": 100, "high": 200}    # незадължителни радиообаждания (по SCRIPT_REVISION_2026-11 §11: +3,3 мин)
STUCK_S = {"low": 0, "mid": 300, "high": 600}       # първо запознаване: губене, повторни опити, Esc/настройки
CARDS_S = 6 * 5.0 + 5 * 3.8                         # 6 заглавни карти + 5 часовникови прехода (story_presenter.gd)
PANELS_S = {"low": 33.0, "mid": 36.0, "high": 36.0}  # 4 крайни панела: 9+9+(9..12)+6 с (ending_sequence/panels.json), × Reading time
CARD_HOLD_S = {"low": 15, "mid": 30, "high": 60}    # крайната карта се държи колкото играчът реши
CREDITS_S = (60, 80, 100)                           # кредити: 63 реда със 46 px/s (credits_roll.gd) — приблизително, Esc ги пропуска
CHOICE_S = {"low": 5, "mid": 8, "high": 12}         # избор на отговор на радиото
MUL = {"low": 1.0, "mid": 1.0, "high": 1.25}         # настройка Reading time


def parse_runs():
    runs = []
    for line in (OUT / "realtime.txt").read_text().splitlines():
        if not line.startswith("REALTIME ") or "ended=true" not in line:
            continue
        kv = dict(re.findall(r"(\w+)=([^\s]+)", line))
        runs.append({
            "route": kv["route"], "choice": float(kv["choice"]), "mul": float(kv["mul"]), "ending": kv["ending"],
            "sim_s": int(kv["sim_seconds"]), "lines": int(kv["lines"]), "line_s": int(kv["modelled_line_s"]),
            "picks": int(kv["picks"]), "per_chapter": json.loads(kv["per_chapter"]),
        })
    return runs


def mandatory_steps():
    d = json.loads(CHAPTERS.read_text())
    n = 0
    for c in d["chapters"]:
        for duty in c.get("duties", []):
            subs = duty.get("sub", [])
            n += sum(1 for s in subs if not s.get("optional")) if subs else 1
    return n


def main():
    runs = parse_runs()
    steps = mandatory_steps()
    by = defaultdict(list)
    for r in runs:
        by[(r["route"], r["choice"], r["mul"])].append(r)

    def sim(route, choice, mul):
        rs = by.get((route, choice, mul))
        return statistics.mean(r["sim_s"] for r in rs) if rs else None

    routes = sorted({r["route"] for r in runs})
    result = {"mandatory_steps": steps, "routes": {}}
    for route in routes:
        base = sim(route, 8.0, 1.0)
        if base is None:
            continue
        ref = sim("truth_saved", 8.0, 1.0)
        c5, c15, m2 = sim("truth_saved", 5.0, 1.0), sim("truth_saved", 15.0, 1.0), sim("truth_saved", 8.0, 2.0)
        # реакция на времето за избор (линейно между измерените 5/8/15 с) и на Reading time (линейно до измереното ×2,0;
        # ×1,5 не се използва директно: ботът остава без гориво в глава 6 при това темпо)
        def d_choice(c):
            return (c5 - ref) * (c - 8.0) / (5.0 - 8.0) if c < 8 else (c15 - ref) * (c - 8.0) / (15.0 - 8.0)
        def d_mul(m):
            return (m2 - ref) * (m - 1.0)
        picks = by[(route, 8.0, 1.0)][0]["picks"]
        lines_s = by[(route, 8.0, 1.0)][0]["line_s"]
        sc = {}
        for k in ("low", "mid", "high"):
            t = base + d_choice(CHOICE_S[k]) + d_mul(MUL[k])
            human = steps * STEP_S[k] * STEP_HIDDEN + DOCS * DOC_S[k] + OPTIONAL_S[k] + STUCK_S[k]
            extras = CARDS_S + PANELS_S[k] * MUL[k] + CARD_HOLD_S[k]
            sc[k] = {"bot_timeline_s": round(t), "human_s": round(human), "extras_s": round(extras),
                     "total_s": round(t + human + extras), "total_min": round((t + human + extras) / 60, 1)}
        result["routes"][route] = {"ending": by[(route, 8.0, 1.0)][0]["ending"], "bot_mid_s": round(base), "lines_s": lines_s,
                                   "picks": picks, "scenarios": sc, "per_chapter_s": by[(route, 8.0, 1.0)][0]["per_chapter"]}

    lows = [r["scenarios"]["low"]["total_min"] for r in result["routes"].values()]
    highs = [r["scenarios"]["high"]["total_min"] for r in result["routes"].values()]
    mids = [r["scenarios"]["mid"]["total_min"] for r in result["routes"].values()]
    floor_bot = [r["bot_mid_s"] / 60 for r in result["routes"].values()]
    lo_r = int(round(min(lows) / 5) * 5)
    hi_r = int(round(max(highs) / 5) * 5)
    mid_r = int(round(statistics.mean(mids) / 5) * 5)
    result["headline"] = {"low_min": min(lows), "mid_min": round(statistics.mean(mids), 1), "high_min": max(highs),
                          "rounded_range_min": [lo_r, hi_r], "typical_min": mid_r, "modelled_bot_min_min": round(min(floor_bot), 1),
                          "credits_s": list(CREDITS_S)}

    def hm(m):
        h, mm = divmod(int(m), 60)
        return (f"{h} ч {mm:02d} мин" if h else f"{mm} мин")
    sentence = (f"Ориентировъчно време за едно изиграване: около {lo_r}–{hi_r} минути (типично около {mid_r}), "
                f"без кредитите (още около 1–2 минути; пропускат се с Esc).")
    result["sentence_bg"] = sentence

    # представителен маршрут (truth_saved), среден сценарий — разбивка
    rep = result["routes"].get("truth_saved")
    if rep:
        mid = rep["scenarios"]["mid"]
        lines = rep["lines_s"]
        choices = rep["picks"] * CHOICE_S["mid"]
        sim_rest = mid["bot_timeline_s"] - lines - choices
        parts = [("Диалог", lines, "#8fc3e0"), ("Избор на отговор", choices, "#f3b95f"),
                 ("Чакане и механика (ботът)", max(sim_rest, 0), "#8fe0b0"),
                 ("Задачи, документи, обаждания", mid["human_s"], "#d9a0c8"), ("Карти и край", mid["extras_s"], "#c4bdac")]
        result["breakdown_mid_truth_saved"] = [{"part": p, "min": round(s / 60, 1)} for p, s, _ in parts]
        tot = sum(s for _, s, _ in parts)
        bar = "".join(f'<div style="width:{s / tot * 100:.2f}%;background:{c}">{round(s / 60)}</div>' for _, s, c in parts)
        legend = "".join(f'<span><i style="background:{c}"></i>{p}</span>' for p, _, c in parts)
        tokens = {
            "PT_RANGE": f"≈ {lo_r}–{hi_r} минути",
            "PT_BAR": f'<div class="bar1">{bar}</div><div class="legend">{legend}</div>',
            "PT_UNC": ("Най-голяма неопределеност: колко време ще отнемат задачите при първо запознаване "
                       f"(за {steps} задължителни стъпки допускам {STEP_S["low"]}–{STEP_S["high"]} с на стъпка) и колко ще се бави играчът с избора на отговор. "
                       "Редовете се сменят сами; времето им е моделирано с приближение за страниците."),
            "PT_NOTES": ("Последно — колко трае една нощ. Не съм я изиграл с хронометър, затова числото е изчислено. "
                         f"Пуснах автоматичен играч, който минава кампанията с пълните чакания и с времето на всеки ред по формулата на играта — "
                         f"това дава около {round(min(floor_bot))} минути за двата завършени маршрута със спасен кораб, преди човешкото забавяне. "
                         f"[КЛИК] Добавям времето за задачи, документи и първо запознаване и получавам диапазон от около {lo_r} до {hi_r} минути, "
                         "без кредитите. Двата маршрута със загубен кораб не са завършени с пълните чакания. [КЛИК] Най-голямата неопределеност е колко време ще отнемат задачите на нов играч."),
        }
        (OUT / "deck_tokens.json").write_text(json.dumps(tokens, ensure_ascii=False, indent=1))

    (OUT / "playtime.json").write_text(json.dumps(result, ensure_ascii=False, indent=1))
    md = ["# Изчислено време за игра (генерирано от compute_playtime.py)", "", sentence, ""]
    md.append("| Маршрут | Край | Ботът (средно) | Ниско | Средно | Високо |")
    md.append("|---|---|---|---|---|---|")
    for name, r in result["routes"].items():
        s = r["scenarios"]
        md.append(f"| {name} | {r['ending']} | {r['bot_mid_s'] / 60:.1f} мин | {s['low']['total_min']} | {s['mid']['total_min']} | {s['high']['total_min']} |")
    md += ["", f"Най-кратък моделиран бот маршрут от двата завършени със спасен кораб: ≈ {result['headline']['modelled_bot_min_min']} мин. Не е глобален минимум за всички маршрути.", ""]
    if "breakdown_mid_truth_saved" in result:
        md.append("Разбивка, представителен маршрут (истина + спасен кораб), средно:")
        md += [f"- {b['part']}: {b['min']} мин" for b in result["breakdown_mid_truth_saved"]]
    (OUT / "PLAYTIME.md").write_text("\n".join(md) + "\n")
    print(sentence)
    print(json.dumps(result["headline"], ensure_ascii=False))


if __name__ == "__main__":
    main()
