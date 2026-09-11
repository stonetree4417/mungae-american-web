#!/usr/bin/env python3
"""
data/patterns.json → index.html 주입 빌드

패턴 데이터의 단일 소스는 data/patterns.json 하나뿐입니다.
HTML을 직접 고치지 마시고, JSON을 고친 뒤 이 스크립트를 돌리십시오.

    python3 build.py

template.html 안의 아래 두 자리에 데이터가 들어갑니다.
    const P = [/*__PATTERNS__*/];
    const LV = [/*__LEVELS__*/];
"""
import json, re, sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).parent
SRC = ROOT / "data" / "patterns.json"
IDX = ROOT / "data" / "patterns-index.json"
LOG = ROOT / "CHANGELOG.md"
TPL = ROOT / "template.html"
OUT = ROOT / "index.html"

def j(o):
    return json.dumps(o, ensure_ascii=False)

def main():
    d = json.loads(SRC.read_text(encoding="utf-8"))
    pats, lvs = d["patterns"], d["levels"]

    # 무결성 검사 — 빌드 단계에서 막는 것이 앱에서 터지는 것보다 낫습니다
    errs = []
    for i, p in enumerate(pats):
        if p["level"] not in (1, 2, 3):
            errs.append(f"[{i}] 레벨 값 오류: {p['level']}")
        if "___" not in p["pattern"] and not re.search(r"\b(to|on|of|with|that)\b", p["pattern"]):
            errs.append(f"[{i}] 빈칸 표시가 없습니다: {p['pattern']}")
        if len(p["ex"]) < 3:
            errs.append(f"[{i}] 예문이 {len(p['ex'])}개뿐입니다: {p['pattern']}")
        for e in p["ex"]:
            if len(e) != 2 or not e[0].strip() or not e[1].strip():
                errs.append(f"[{i}] 예문 형식 오류: {e}")
    if errs:
        print("빌드 중단 — 데이터 오류\n" + "\n".join(errs))
        sys.exit(1)

    # [level, pattern, ko, tip, [[en,ko],...]] 배열로 압축
    rows = [j([p["level"], p["pattern"], p["ko"], p["tip"], p["ex"]]) for p in pats]
    levels = [j({"n": l["n"], "name": l["name"], "cefr": l["cefr"],
                 "goal": l["goal"], "can": l["can"], "bark": l["bark"]}) for l in lvs]

    # 마스터 인덱스와 대조 — 중복과 누락을 여기서 잡습니다
    plan = todo = 0
    if IDX.exists():
        key = lambda t: re.sub(r"[\s?,.:]|___", "", t.lower())
        index = json.loads(IDX.read_text(encoding="utf-8"))["index"]
        plan = len(index)
        have = {key(p["pattern"]) for p in pats}
        want = {key(r[1]) for r in index}
        todo = len(want - have)
        stray = sorted(have - want)
        if stray:
            print("경고 — 마스터 인덱스에 없는 패턴: " + ", ".join(stray))

    # 앱 버전은 릴리즈 키트의 version.properties가 단일 소스입니다
    vp = ROOT / "version.properties"
    if not vp.exists():
        vp = ROOT / "release-kit" / "version.properties"
    app_ver = "0.0.0"
    if vp.exists():
        t = vp.read_text(encoding="utf-8")
        g = lambda k: re.search(rf"^{k}=(\d+)$", t, re.M).group(1)
        app_ver = f"{g('versionMajor')}.{g('versionMinor')}.{g('versionPatch')}"
    ver = {"app": app_ver, "data": d["meta"]["dataVersion"],
           "build": datetime.now().strftime("%Y-%m-%d")}

    # 목표·트랙·전체 계획 수량도 데이터에서 주입합니다
    plan_per = {}
    if plan:
        for lv in (1, 2, 3):
            plan_per[lv] = sum(1 for r in index if r[0] == lv)
    html = TPL.read_text(encoding="utf-8")
    html = html.replace("__GOALS__", j(d.get("goals", [])))
    html = html.replace("__TRACKS__", j(d.get("tracks", [])))
    html = html.replace("__PLAN__", j({"total": plan or len(pats),
                                           "per": plan_per or {}, "loaded": len(pats)}))
    html = html.replace("/*__VER__*/", ", ".join(f"{k}:{j(v)}" for k, v in ver.items()))
    html = html.replace("/*__PATTERNS__*/", "\n" + ",\n".join(rows) + "\n")
    html = html.replace("/*__LEVELS__*/", "\n " + ",\n ".join(levels) + "\n")
    # 데이터 버전을 올려놓고 이력을 안 적으면 여기서 걸립니다 (경고만, 중단하지 않음)
    dv = d["meta"]["dataVersion"]
    if LOG.exists() and f"데이터 {dv}" not in LOG.read_text(encoding="utf-8"):
        print(f"경고 — CHANGELOG.md에 '데이터 {dv}' 항목이 없습니다. 변경 이력을 적어주십시오.")

    left = [t for t in ("__GOALS__", "__TRACKS__", "__PLAN__", "__VER__",
                        "__PATTERNS__", "__LEVELS__") if t in html]
    if left:
        print("빌드 중단 — 치환되지 않은 자리: " + ", ".join(left))
        sys.exit(1)
    OUT.write_text(html, encoding="utf-8")

    per = [sum(1 for p in pats if p["level"] == n) for n in (1, 2, 3)]
    total_ex = sum(len(p["ex"]) for p in pats)
    print(f"빌드 완료 → {OUT.name}")
    print(f"  패턴 {len(pats)}개 (레벨별 {per[0]}/{per[1]}/{per[2]}) · 예문 {total_ex}개")
    if plan:
        print(f"  마스터 인덱스 {plan}개 · 예문 미작성 {todo}개 → 진척 {len(pats)}/{plan}")
    print(f"  앱 {app_ver} · 데이터 {d['meta']['dataVersion']} · {OUT.stat().st_size//1024}KB")

if __name__ == "__main__":
    main()
