#!/usr/bin/env python3
"""Turn a fresh concept pull into write_db batches for the allocation app.

Inputs
  --existing DIR   read_db out_dir for the app's `concepts` collection (DIR/*.json), may be empty
  --new FILE       JSON list of concept records built from the Notion pull (see SKILL.md, Step 5)
  --clients A,B    clients covered by this pull (only their missing concepts get deleted);
                   use ALL for a full refresh
  --tickets DIR    optional read_db out_dir for the app's `tickets` collection, for the summary
  --by NAME        who ran it (shown in the app), e.g. "Tim (ppm-overview)"

Output: a summary, then ```json {"batches": [[...<=50 writes], ...]}``` to apply with
Artifact write_db (db_op "batch"), one call per batch. Nothing is written by this script.
"""
import argparse, glob, json, os, re, time

KEYS = ["client", "campaign", "concept", "conceptNum", "title", "url", "approved", "ticketCreated",
        "pipelineStatus", "editorTicketUrl", "editorTicketStatus", "editorTicketAssignee"]

def load_dir(d):
    out = {}
    if not d or not os.path.isdir(d): return out
    for f in glob.glob(os.path.join(d, "*.json")):
        try: body = json.load(open(f))
        except Exception: continue
        if isinstance(body, dict) and isinstance(body.get("data"), dict): body = body["data"]
        out[os.path.splitext(os.path.basename(f))[0]] = body
    return out

def bucket(c):
    if c.get("ticketCreated") or c.get("editorTicketUrl"): return "confirmed"
    return "expected" if c.get("approved") else "early"

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--existing"); p.add_argument("--new", required=True); p.add_argument("--clients", required=True)
    p.add_argument("--tickets"); p.add_argument("--by", default="Claude (ppm-overview)")
    a = p.parse_args()
    old = load_dir(a.existing)
    new = {}
    for r in json.load(open(a.new)):
        rid = re.sub(r"[^0-9a-f]", "", str(r.get("id", "")).lower())[-32:]
        if len(rid) != 32: continue
        rec = {k: r.get(k) for k in KEYS}
        rec["title"] = str(rec.get("title") or "")[:140]
        new[rid] = rec
    scope = None if a.clients.strip().upper() == "ALL" else {c.strip().lower() for c in a.clients.split(",") if c.strip()}
    now = int(time.time() * 1000)
    writes, changed, added, newly_ticketed = [], 0, 0, []
    for rid, rec in new.items():
        prev = old.get(rid)
        if prev and all(prev.get(k) == rec.get(k) for k in KEYS): continue
        if prev is None: added += 1
        else:
            changed += 1
            if bucket(prev) != "confirmed" and bucket(rec) == "confirmed": newly_ticketed.append(rec)
        writes.append({"op": "set", "collection": "concepts", "doc_id": rid, "data": {**rec, "refreshedAt": now}})
    removed = 0
    for rid, prev in old.items():
        if rid in new: continue
        if scope is None or str(prev.get("client", "")).lower() in scope:
            writes.append({"op": "delete", "collection": "concepts", "doc_id": rid}); removed += 1
    clients = sorted({r["client"] for r in new.values() if r.get("client")})
    writes.append({"op": "set", "collection": "meta", "doc_id": "conceptSync",
                   "data": {"at": now, "by": None, "byLabel": a.by, "count": len(new) if scope is None else None,
                            "clients": clients if scope is None else sorted(scope)}})
    batches = [writes[i:i + 50] for i in range(0, len(writes), 50)]

    # summary
    allc = {**{k: v for k, v in old.items() if not (scope is None or str(v.get("client", "")).lower() in scope)}, **new}
    counts = {"confirmed": 0, "expected": 0, "early": 0}
    for c in allc.values(): counts[bucket(c)] += 1
    linked = {t.get("conceptId") for t in load_dir(a.tickets).values() if t.get("conceptId")} if a.tickets else set()
    waiting = [c for rid, c in new.items() if bucket(c) == "expected" and rid not in linked]
    print(f"Concepts in scope: {len(new)} ({', '.join(clients) or 'none'})")
    print(f"Changes: {added} new, {changed} updated, {removed} removed. Writes: {len(writes)} in {len(batches)} batch(es).")
    print(f"Buckets now: {counts['confirmed']} ticketed, {counts['expected']} approved without a ticket, {counts['early']} in concepting.")
    if newly_ticketed:
        print("Newly ticketed (linked slots flip to Ready): " + "; ".join(f"{c['client']} {c['campaign']} {c['concept']}" for c in newly_ticketed))
    if a.tickets:
        print(f"Approved, no ticket, and not in the plan yet: {len(waiting)}" +
              ("" if not waiting else " — " + "; ".join(f"{c['client']} {c['campaign']} {c['concept']}" for c in sorted(waiting, key=lambda c: (c['client'], c.get('conceptNum') or 0)))))
    print("```json\n" + json.dumps({"batches": batches}, ensure_ascii=False) + "\n```")

if __name__ == "__main__":
    main()
