#!/usr/bin/env python3
"""Allocation helper for the ppm-overview skill (app-backed version).

Reads the allocation app's data exported with the Artifact tool
(action "read_db" with out_dir) and prints an overview, an EXT shift
proposal, or an EXT-calendar sync batch. It never writes anything;
Claude applies the printed write_db batch after the user approves.

Data directory layout (from read_db out_dir):
  <dir>/tickets/<id>.json   {title, editor, date, month, status, notes, ...}
  <dir>/ext/<id>.json       {title, label, date, url, prevDate?, moveHandled?}
  <dir>/meta/roster.json    {editors:[{name,type,hidden}]}   (optional)

Commands:
  overview --dir D --today YYYY-MM-DD [--weeks 3] [--cal cal.json]
  shift    --dir D --today YYYY-MM-DD --ext <ext id> [--from YYYY-MM-DD --to YYYY-MM-DD]
  sync     --dir D --cal cal.json --today YYYY-MM-DD
           (cal.json = Notion PM rows: url, "Key Deadline", "date:Dates:start")
"""
import argparse, glob, json, os, re, sys, time, datetime as dt
from collections import defaultdict

DAYS = ["Mon", "Tue", "Wed", "Thu", "Fri"]
HOLIDAYS = {dt.date(2026,12,25), dt.date(2026,12,28), dt.date(2027,1,1), dt.date(2027,3,26), dt.date(2027,3,29),
            dt.date(2027,5,3), dt.date(2027,5,31), dt.date(2027,8,30), dt.date(2027,12,27), dt.date(2027,12,28)}
MAX_PER_DAY = 2
WEEKLY_MAX = 5
MIN_BUFFER = 1
ALIASES = {"fs - cg": ["free soul"], "sbo": ["sweet bee"], "rheal - collagen": ["rheal"],
           "the diamond store": ["diamond store"], "bella+duke": ["bella + duke", "bella & duke", "bella and duke"],
           "tom’s studio": ["tom's studio", "toms studio"], "voy hl": ["voy"]}
SKIP_EXT = re.compile(r"script|statics?", re.I)
NON_WORK = re.compile(r"^(unavailable|(ugcs? & )?iterations?)$", re.I)
SKILL_LABEL = "Claude (ppm-overview)"

D = lambda s: dt.date.fromisoformat(str(s)[:10])
def is_work(d): return d.weekday() < 5 and d not in HOLIDAYS
def add_wd(d, n):
    step = 1 if n >= 0 else -1
    while n:
        d += dt.timedelta(days=step)
        if is_work(d): n -= step
    return d
def wd_between(a, b):
    if a == b: return 0
    s = 1 if b > a else -1; lo, hi = (a, b) if s > 0 else (b, a); n, d = 0, lo
    while d < hi:
        d += dt.timedelta(days=1)
        if is_work(d): n += 1
    return n * s
def monday(d): return d - dt.timedelta(days=d.weekday())
def month_key(d): m = monday(d); return f"{m.year}-{m.month:02d}"
def fmt(d): return d.strftime("%a %d %b") if d else "—"
def norm(s): return re.sub(r"[^a-z0-9]", "", str(s).lower())
def pid(x):
    m = re.findall(r"[0-9a-f]{32}", str(x).replace("-", ""))
    return m[-1] if m else None

def ext_label(title):
    b = re.search(r"\[([^\]]+)\]", title); p = re.search(r"\(([^)]+)\)\s*$", title)
    if not b: return re.sub(r"\s*EXT.*$", "", title, flags=re.I).strip() or title
    return f"{b.group(1)} ({p.group(1)})" if p else b.group(1)
def concepts_in(s): return [x.upper() for x in re.findall(r"\bC\d+\b", str(s), re.I)]
def manual_parts(title):
    brand = re.sub(r"\s+", " ", re.sub(r"[,&+]|\band\b", " ", re.sub(r"\bC\d+\b", " ", title, flags=re.I), flags=re.I)).strip()
    return brand, concepts_in(title)
def ext_keys(e):
    if e.get("manual"):
        b = manual_parts(e["title"])[0].lower()
        return [k for k in (norm(x) for x in [b] + ALIASES.get(b, [])) if len(k) >= 3]
    m = re.search(r"\[([^\]]+)\]", e["title"])
    b = (m.group(1) if m else e["title"].split(" EXT")[0]).strip().lower()
    return [k for k in (norm(x) for x in [b] + ALIASES.get(b, [])) if len(k) >= 3]

def load(dirpath):
    def coll(name):
        out = []
        for f in sorted(glob.glob(os.path.join(dirpath, name, "*.json"))):
            try: body = json.load(open(f))
            except Exception: continue
            if isinstance(body, dict) and isinstance(body.get("data"), dict): body = body["data"]
            body = dict(body); body["id"] = os.path.splitext(os.path.basename(f))[0]
            out.append(body)
        return out
    tickets = [t for t in coll("tickets") if t.get("date") and t.get("editor")]
    for t in tickets: t["d"] = D(t["date"]); t.setdefault("title", "Untitled"); t.setdefault("status", "Pending")
    ext = [e for e in coll("ext") if e.get("date")]
    for e in ext: e["d"] = D(e["date"]); e.setdefault("title", e.get("label", "")); e.setdefault("label", ext_label(e["title"]))
    roster = []
    rf = os.path.join(dirpath, "meta", "roster.json")
    if os.path.exists(rf):
        r = json.load(open(rf)); r = r.get("data", r) if isinstance(r, dict) else r
        roster = r.get("editors", []) if isinstance(r, dict) else []
    return tickets, ext, roster

def match_ext(t, ext):
    n = norm(t["title"]); tc = (concepts_in(t["title"]) or [None])[0]; best, score_best = None, 1e9
    for e in ext:
        if not any(k in n for k in ext_keys(e)): continue
        dist = (e["d"] - t["d"]).days
        cs = manual_parts(e["title"])[1] if e.get("manual") else []
        if cs:  # a manual EXT naming this concept always wins
            if tc not in cs or dist < -30 or dist > 60: continue
            score = -1000 + abs(dist)
        else:
            if dist < -10 or dist > 28: continue
            score = dist if dist >= 0 else 100 - dist
        if score < score_best: best, score_best = e, score
    return best

def busy_map(tickets):
    m = defaultdict(list)
    for t in tickets: m[(t["editor"], t["d"])].append(t)
    return m

# ---------------- overview ----------------
def overview(a):
    tickets, ext, roster = load(a.dir)
    today = D(a.today); start = monday(today) + (dt.timedelta(days=7) if today.weekday() > 4 else dt.timedelta(0))
    end = start + dt.timedelta(days=7 * a.weeks - 3)
    live = [t for t in tickets if today <= t["d"] <= end]
    out = [f"# Allocation overview — {fmt(today)} (window {fmt(start)} → {fmt(end)})", ""]

    # 0. calendar drift the app hasn't picked up yet
    if a.cal:
        drift = sync_changes(ext, json.load(open(a.cal)), today)
        if drift["set"] or drift["delete"]:
            out.append("## 0. EXT calendar changes not yet in the app")
            for s in drift["set"]:
                cur = next((e for e in ext if e["id"] == s["doc_id"]), None)
                what = "new" if not cur else (f"moved {fmt(cur['d'])} → {fmt(D(s['data']['date']))}" if cur["date"] != s["data"]["date"] else "renamed")
                out.append(f"- {s['data']['label']}: {what}")
            for d_ in drift["delete"]: out.append(f"- removed from calendar: {d_['doc_id']}")
            out.append("Run `sync` and apply its batch, then re-read the data before shifting.")
            out.append("")

    # 1. EXT moves waiting on INT shifts
    out.append("## 1. EXT dates that moved (INT dates not adjusted yet)")
    moves = [e for e in ext if e.get("prevDate") and e.get("moveHandled") is False]
    if not moves: out.append("None.")
    for e in sorted(moves, key=lambda e: e["d"]):
        aff = [t for t in tickets if t["d"] >= today and (m := match_ext(t, ext)) and m["id"] == e["id"]]
        dl = wd_between(D(e["prevDate"]), e["d"])
        out.append(f"- **{e['label']}**: {fmt(D(e['prevDate']))} → {fmt(e['d'])} ({'+' if dl > 0 else ''}{dl} working days). "
                   f"{len(aff)} upcoming ticket(s): {', '.join(sorted({t['editor'] for t in aff})) or 'none matched'}. ext={e['id']}")

    # 2. INT too close to / after EXT
    out.append(f"\n## 2. INT within {MIN_BUFFER} working day of its EXT (or after it)")
    risky = []
    for t in live:
        if NON_WORK.match(t["title"].strip()): continue
        e = match_ext(t, ext)
        if e and wd_between(t["d"], e["d"]) <= MIN_BUFFER: risky.append((t, e))
    if not risky: out.append("None.")
    for t, e in sorted(risky, key=lambda x: x[0]["d"]):
        b = wd_between(t["d"], e["d"])
        tag = "🔴 after EXT (or its real EXT is missing from the calendar)" if b < 0 else "🟠 same day" if b == 0 else "🟡 1 day"
        out.append(f"- {tag}: {t['editor']} — {t['title']} INT {fmt(t['d'])}, EXT {fmt(e['d'])} ({e['label']})")

    # 3. EXT deliveries with nothing matched
    out.append("\n## 3. EXT deliveries in the window with no tickets matched by name")
    matched = {m["id"] for t in tickets if (m := match_ext(t, ext))}
    gaps = [e for e in ext if today <= e["d"] <= end + dt.timedelta(days=7) and e["id"] not in matched and not SKIP_EXT.search(e["title"])]
    out += [f"- {fmt(e['d'])} — {e['label']} ({e['title']})" for e in sorted(gaps, key=lambda e: e["d"])] or ["None."]

    # 4. tickets whose brand isn't recognised
    out.append("\n## 4. Upcoming tickets not matched to any EXT (check the brand name in the ticket)")
    nomatch = [t for t in live if not NON_WORK.match(t["title"].strip()) and not match_ext(t, ext)]
    out += [f"- {t['editor']} — {t['title']} ({fmt(t['d'])})" for t in sorted(nomatch, key=lambda t: t["d"])] or ["None."]

    # 5. capacity
    out.append("\n## 5. Capacity (tickets per week)")
    weeks = []; w = start
    while w <= end: weeks.append(w); w += dt.timedelta(days=7)
    order = [r["name"] for r in roster if not r.get("hidden")] or sorted({t["editor"] for t in tickets})
    extra = sorted({t["editor"] for t in tickets} - set(order))
    load_ = defaultdict(lambda: defaultdict(int)); flags = defaultdict(set); per = busy_map(tickets)
    for t in tickets:
        if NON_WORK.match(t["title"].strip()): continue
        load_[t["editor"]][monday(t["d"])] += 1
    for (ed, d), ts in per.items():
        if not (start <= d <= end): continue
        if any(re.match(r"^unavailable$", x["title"].strip(), re.I) for x in ts) and len(ts) > 1:
            flags[ed].add(f"ticket on an Unavailable day ({fmt(d)})")
    ftype = {r["name"]: r.get("type", "editor") for r in roster}
    out += ["| Editor | " + " | ".join("W/C " + w.strftime("%d %b") for w in weeks) + " | Flags |", "|" + "---|" * (len(weeks) + 2)]
    for ed in order + extra:
        for w in weeks:
            if load_[ed][w] > WEEKLY_MAX and ftype.get(ed) != "aiv": flags[ed].add(f"{load_[ed][w]} in W/C {w.strftime('%d %b')}")
            if load_[ed][w] == 0 and w >= monday(today) and ftype.get(ed, "editor") == "editor": flags[ed].add(f"nothing allocated W/C {w.strftime('%d %b')}")
        if ed in extra: flags[ed].add("not in the app’s editor list")
        out.append(f"| {ed} | " + " | ".join(str(load_[ed][w]) for w in weeks) + f" | {'; '.join(sorted(flags[ed]))} |")
    print("\n".join(out))

# ---------------- shift ----------------
def shift(a):
    tickets, ext, _ = load(a.dir)
    today = D(a.today)
    e = next((x for x in ext if x["id"] == a.ext), None)
    if not e: sys.exit(f"No EXT {a.ext} in the data.")
    old = D(a.from_) if a.from_ else (D(e["prevDate"]) if e.get("prevDate") else None)
    new = D(a.to) if a.to else e["d"]
    if not old: sys.exit("No previous EXT date recorded; pass --from and --to.")
    delta = wd_between(old, new)
    latest = add_wd(new, -MIN_BUFFER)
    per = busy_map(tickets)
    rows, writes = [], []
    now_ms = int(time.time() * 1000)
    for t in sorted([t for t in tickets if t["d"] >= today and (m := match_ext(t, ext)) and m["id"] == e["id"]], key=lambda t: t["d"]):
        target = add_wd(t["d"], delta)
        if target > latest: target = latest
        if target < today: target = today if is_work(today) else add_wd(today, 1)
        def full(d): return len([x for x in per[(t["editor"], d)] if x["id"] != t["id"]]) >= MAX_PER_DAY
        note = ""
        if target != t["d"] and full(target):
            alt = None
            for k in range(1, 6):
                for c in (add_wd(target, -k), add_wd(target, k)):
                    if today <= c <= latest and not full(c): alt = c; break
                if alt: break
            note = "day full → nearest free day" if alt else "⚠️ day full, no free day before EXT"
            target = alt or target
        per[(t["editor"], t["d"])] = [x for x in per[(t["editor"], t["d"])] if x["id"] != t["id"]]
        per[(t["editor"], target)].append(t)
        rows.append((t, target, note))
        if target != t["d"]:
            writes.append({"op": "update", "collection": "tickets", "doc_id": t["id"],
                           "data": {"date": target.isoformat(), "month": month_key(target), "editedBy": None,
                                    "editedLabel": SKILL_LABEL, "editedAt": now_ms}})
    writes.append({"op": "update", "collection": "ext", "doc_id": e["id"], "data": {"moveHandled": True}})
    print(f"# Shift proposal — {e['label']}\nEXT {fmt(old)} → {fmt(new)} ({'+' if delta > 0 else ''}{delta} working days)\n")
    print("| Editor | Ticket | INT now | INT proposed | Note |\n|---|---|---|---|---|")
    for t, tg, n in rows:
        print(f"| {t['editor']} | {t['title']} | {fmt(t['d'])} | {fmt(tg)} | {n or ('unchanged' if tg == t['d'] else '')} |")
    if not rows: print("| — | No upcoming tickets matched this EXT by name | | | |")
    print("\n```json\n" + json.dumps({"writes": writes}, indent=1) + "\n```")

# ---------------- sync (mirror of the app's EXT sync) ----------------
def sync_changes(ext, cal_rows, today):
    cal_rows = cal_rows.get("results", cal_rows) if isinstance(cal_rows, dict) else cal_rows
    lo, hi = today - dt.timedelta(days=35), today + dt.timedelta(days=120)
    fresh = []
    for r in cal_rows:
        t, d = r.get("Key Deadline") or "", r.get("date:Dates:start")
        if not d or SKIP_EXT.search(t) or "design" in t.lower(): continue
        if not (lo <= D(d) <= hi): continue
        fresh.append({"id": pid(r["url"]), "title": t, "date": d[:10]})
    cur = {e["id"]: e for e in ext}; sets, dels, seen = [], [], set()
    for f in fresh:
        seen.add(f["id"]); c = cur.get(f["id"])
        if c and c["date"] == f["date"] and c["title"] == f["title"]: continue
        body = {"title": f["title"], "label": ext_label(f["title"]), "date": f["date"], "url": f"https://app.notion.com/p/{f['id']}"}
        if c and c["date"] != f["date"]:
            prev = c["prevDate"] if (c.get("moveHandled") is False and c.get("prevDate")) else c["date"]
            body.update(prevDate=prev, movedAt=int(time.time() * 1000), moveHandled=(prev == f["date"]))
        elif c and c.get("prevDate"):
            body.update(prevDate=c["prevDate"], movedAt=c.get("movedAt"), moveHandled=c.get("moveHandled") is not False)
        sets.append({"op": "set", "collection": "ext", "doc_id": f["id"], "data": body})
    for e in ext:
        if e["id"] not in seen and not e.get("manual") and lo <= e["d"] <= hi: dels.append({"op": "delete", "collection": "ext", "doc_id": e["id"]})
    return {"set": sets, "delete": dels}

def sync(a):
    _, ext, _ = load(a.dir)
    ch = sync_changes(ext, json.load(open(a.cal)), D(a.today))
    writes = ch["set"] + ch["delete"]
    if writes:
        writes.append({"op": "set", "collection": "meta", "doc_id": "extSync",
                       "data": {"at": int(time.time() * 1000), "by": None, "count": len(ext) + len(ch["set"]) - len(ch["delete"])}})
    print(f"{len(ch['set'])} EXT entr(ies) to add/update, {len(ch['delete'])} to remove.")
    print("```json\n" + json.dumps({"writes": writes}, indent=1) + "\n```")

if __name__ == "__main__":
    p = argparse.ArgumentParser(); s = p.add_subparsers(dest="cmd", required=True)
    o = s.add_parser("overview"); o.add_argument("--dir", required=True); o.add_argument("--today", required=True); o.add_argument("--weeks", type=int, default=3); o.add_argument("--cal")
    h = s.add_parser("shift"); h.add_argument("--dir", required=True); h.add_argument("--today", required=True); h.add_argument("--ext", required=True); h.add_argument("--from", dest="from_"); h.add_argument("--to")
    y = s.add_parser("sync"); y.add_argument("--dir", required=True); y.add_argument("--today", required=True); y.add_argument("--cal", required=True)
    a = p.parse_args()
    {"overview": overview, "shift": shift, "sync": sync}[a.cmd](a)
