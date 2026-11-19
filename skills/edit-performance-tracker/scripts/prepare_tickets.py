#!/usr/bin/env python3
"""Step 1 of edit-performance-tracker.

Reads the full Notion Editor Tickets export, validates it, keeps approved HP / AI HP
net new editor tickets, optionally narrows to one editor, and writes:
  <workdir>/tickets.json   tickets in scope (with concept # recovered from titles)
  <workdir>/pull_plan.json clients + Foreplay lenses to pull, and clients skipped (with reason)

Usage:
  python prepare_tickets.py <csv_path> <workdir> [--editor "Name"] [--export-date YYYY-MM-DD]
Exit code 2 = validation problem (message printed); 3 = editor name ambiguous/not found.
"""
import argparse, json, os, re, sys
from datetime import date, datetime
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
CLIENTS = json.load(open(os.path.join(HERE, '..', 'references', 'clients.json')))['clients']
REQUIRED = ['Concept', 'Clients', 'Campaign', 'Concept #', 'Ad Type', 'Type', 'Status', 'Assigned to', 'Due date']
NAME_RE = re.compile(r'EditorTickets_HP-NetNew_Approved_(\d{4}-\d{2}-\d{2})\.csv$')


def concept_number(row):
    if pd.notna(row['Concept #']):
        return int(row['Concept #'])
    m = re.search(r'\[C(?:ONCEPT)?\s*#?\s*(\d+)\]|(?<![A-Za-z])C(\d+)_|CONCEPT\s*#?\s*(\d+)', row['title'], re.I)
    return int(next(g for g in m.groups() if g)) if m else None


def client_entry(client_name):
    low = client_name.lower()
    for c in CLIENTS:
        if c['key'].lower() in low:
            return c
    return None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('csv'); ap.add_argument('workdir')
    ap.add_argument('--editor'); ap.add_argument('--export-date')
    ap.add_argument('--to', help='Window end YYYY-MM-DD; only clients with tickets due in the 180 days before it are pulled')
    a = ap.parse_args()
    os.makedirs(a.workdir, exist_ok=True)
    warnings = []

    m = NAME_RE.search(os.path.basename(a.csv))
    export_date = a.export_date or (m.group(1) if m else None)
    if not m:
        warnings.append('File name does not follow EditorTickets_HP-NetNew_Approved_YYYY-MM-DD.csv.')
    if export_date:
        age = (date.today() - datetime.strptime(export_date, '%Y-%m-%d').date()).days
        if age > 7:
            warnings.append(f'Export is {age} days old ({export_date}). Recent approvals may be missing.')

    df = pd.read_csv(a.csv, encoding='utf-8-sig', low_memory=False)
    missing = [c for c in REQUIRED if c not in df.columns]
    if missing:
        print('VALIDATION FAILED: missing columns ' + ', '.join(missing) +
              '. This looks like a view export. Export the full Editor Tickets database (the _all.csv).')
        sys.exit(2)
    if len(df) < 1000:
        warnings.append(f'Only {len(df)} rows. A full export usually has 10,000+; check it is the _all.csv, not a filtered view.')

    types = df['Ad Type'].fillna('').str.split(', ')
    keep = (types.apply(lambda l: 'HP' in l or 'AI HP' in l)
            & (df['Type'] == 'Net new - Editor')
            & df['Status'].isin(['Approved', 'Live']))
    f = df[keep].copy()
    no_client = int(f['Clients'].isna().sum())
    f = f[f['Clients'].notna()]
    f['client'] = f['Clients'].str.split(r' \(https').str[0].str.strip()
    f['title'] = f['Concept'].fillna('').str.split(r' \(https').str[0].str.strip()
    f['c'] = f.apply(concept_number, axis=1)
    f['cm'] = f['Campaign'].fillna('').str.split(',').str[0].str.strip()
    f['ad_type'] = types[f.index].apply(lambda l: 'AI HP' if 'AI HP' in l and 'HP' not in l else 'HP')
    f['editors'] = f['Assigned to'].fillna('').apply(lambda s: [e.strip() for e in s.split(',') if e.strip()])
    no_concept = int(f['c'].isna().sum())

    editor_full = None
    if a.editor:
        names = sorted({e for lst in f['editors'] for e in lst})
        hits = [n for n in names if a.editor.lower() in n.lower()]
        if len(hits) != 1:
            print(('EDITOR AMBIGUOUS: ' + '; '.join(hits)) if hits else f'EDITOR NOT FOUND: no approved HP ticket assigned to "{a.editor}".')
            sys.exit(3)
        editor_full = hits[0]

    tickets, unknown_clients = [], set()
    for idx, r in f.iterrows():
        entry = client_entry(r['client'])
        if entry is None:
            unknown_clients.add(r['client'])
        tickets.append(dict(id=int(idx), client=r['client'], label=entry['label'] if entry else r['client'],
                            pod=r.get('POD') if pd.notna(r.get('POD')) else '', cm=r['cm'],
                            c=None if pd.isna(r['c']) else int(r['c']), ad_type=r['ad_type'], title=r['title'],
                            editors=r['editors'], status=r['Status'], due=r['Due date'] if pd.notna(r['Due date']) else ''))

    end = datetime.strptime(a.to, '%Y-%m-%d') if a.to else datetime.today()

    def recent(t):
        try:
            d = datetime.strptime(t['due'], '%d %B %Y')
        except ValueError:
            return False
        return 0 <= (end - d).days <= 180

    plan_clients = {t['label'] for t in tickets if (not editor_full or editor_full in t['editors']) and recent(t)}
    pull, skipped = [], []
    for c in CLIENTS:
        if c['label'] not in plan_clients:
            continue
        if c['status'] in ('ok', 'client_naming') and c['lenses']:
            pull.append(dict(label=c['label'], lenses=c['lenses'], status=c['status'], note=c.get('note', '')))
        else:
            skipped.append(dict(label=c['label'], status=c['status'], note=c.get('note', '')))
    for u in sorted(unknown_clients):
        if any((not editor_full or editor_full in t['editors']) and recent(t) for t in tickets if t['client'] == u):
            skipped.append(dict(label=u, status='not_in_clients_json', note='Add this client and its Foreplay lens to references/clients.json.'))

    json.dump(dict(export_date=export_date, editor=editor_full, tickets=tickets), open(os.path.join(a.workdir, 'tickets.json'), 'w'), indent=1)
    json.dump(dict(pull=pull, skipped=skipped), open(os.path.join(a.workdir, 'pull_plan.json'), 'w'), indent=1)

    scope = [t for t in tickets if not editor_full or editor_full in t['editors']]
    print(f'Rows in export: {len(df)} | approved HP net new with client: {len(tickets)} | excluded (no client linked): {no_client}')
    if editor_full:
        print(f'Editor: {editor_full} | their approved HP tickets: {len(scope)} across {len(plan_clients)} clients')
    print(f'Tickets with no concept # in field or title: {no_concept}')
    print(f'Clients to pull: {len(pull)} | skipped: {len(skipped)}')
    for s in skipped:
        print(f'  skipped {s["label"]}: {s["status"]} {s["note"]}')
    for w in warnings:
        print('WARNING: ' + w)


if __name__ == '__main__':
    main()
