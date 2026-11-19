#!/usr/bin/env python3
"""Step 3 of edit-performance-tracker.

Parses Foreplay ad names, matches each ad to an approved editor ticket and writes the workbook.

Inputs (in <workdir>): tickets.json, pull_plan.json (from prepare_tickets.py) and ads.json:
  [{"client": "<label from pull_plan>", "region": "US" | "", "currency": "GBP",
    "ad_name": "<group_by from get_lens_insights>", "spend": 123.4, "roas": 1.23}, ...]

Usage:
  python match_and_report.py <workdir> --from YYYY-MM-DD --to YYYY-MM-DD --out <file.xlsx>
"""
import argparse, json, os, re
from collections import defaultdict
from datetime import datetime, timedelta
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment
from openpyxl.utils import get_column_letter

EXCLUDE = re.compile(r'iteration|static|^\W*image\b|\bimage\s*[-|:]|IMAGE::|UGC NET NEW|\|\s*UGC\s*\||_UGC_|ct:UGC|DO NOT TURN ON', re.I)
CM_RE = re.compile(r'(?<![A-Za-z])CM\s?(\d+)', re.I)
BATCH_RE = re.compile(r'(?<![A-Za-z])B(\d{1,3})(?=_)', re.I)
C_RES = [re.compile(r'\[C(\d+)\]', re.I), re.compile(r'concept\s*#?\s*(\d+)', re.I),
         re.compile(r'(?<![A-Za-z0-9])C(\d{1,2})(?=[\s_\-:|\].H]|$)', re.I)]
STOP = {'the', 'and', 'for', 'you', 'your', 'hook', 'video', 'net', 'new', 'shoot', 'non', 'hambi', 'copy', 'rev',
        'problem', 'solution', 'product', 'aware', 'framework', 'big', 'swing', 'easy', 'impact', 'collagen'}
CUR = {'GBP': '£', 'EUR': '€', 'USD': '$', 'AUD': 'A$'}


def toks(s):
    s = re.sub(r'([a-z])([A-Z])', r'\1 \2', str(s))
    return {w for w in re.findall(r'[a-z0-9]+', s.lower()) if len(w) > 2 and w not in STOP and not w.isdigit()}


def parse(name):
    cm = CM_RE.search(name); b = BATCH_RE.search(name)
    c = None
    for rx in C_RES:
        m = rx.search(name)
        if m:
            c = int(m.group(1)); break
    return dict(cm=f'CM{cm.group(1)}' if cm else '', batch=f'B{b.group(1)}' if b else '', c=c,
                ad_type='AI HP' if 'AI HP' in name.upper() else 'HP')


def match(ad, cands):
    """Return (ticket | None, editors | None, note)."""
    p = ad['p']
    if p['c'] is not None:
        cc = [t for t in cands if t['c'] == p['c']]
        if p['cm']:
            exact = [t for t in cc if t['cm'] == p['cm']]
            cc = exact or [t for t in cc if not t['cm']]
        if not cc:
            return None, None, f"No approved ticket for {p['cm'] or 'any CM'} C{p['c']}."
    else:
        cc = cands
        if not p['cm'] and not cc:
            return None, None, 'No concept # in ad name.'
    if len(cc) > 1:
        sc = [len(toks(ad['ad_name']) & toks(t['title'])) for t in cc]
        best = max(sc)
        need = 1 if p['c'] is not None else 2
        if best >= need:
            cc = [t for t, s in zip(cc, sc) if s == best]
        elif p['c'] is None:
            return None, None, 'No concept # in ad name and no concept-name match.'
    if len(cc) == 1:
        overlap = len(toks(ad['ad_name']) & toks(cc[0]['title']))
        if p['c'] is None and overlap < 2:
            return None, None, 'No concept # in ad name and no concept-name match.'
        if p['c'] is not None and not p['cm'] and overlap < 1:
            t0 = cc[0]
            return None, None, "Ad has no CM and its name doesn't match the only C%s ticket (%s, %s)." % (p['c'], t0['cm'] or 'no CM', ', '.join(t0['editors']))
        return cc[0], cc[0]['editors'], ''
    eds = {tuple(sorted(t['editors'])) for t in cc}
    if len(eds) == 1:
        return None, list(eds.pop()), f'{len(cc)} tickets fit; all assigned to the same editor(s).'
    why = 'ad has no CM' if not p['cm'] else 'same CM and concept #'
    return None, None, f"{len(cc)} tickets fit ({why}): " + '; '.join(f"{t['cm'] or 'no CM'} {', '.join(t['editors'])}" for t in cc[:3])


def concept_name(title):
    s = re.sub(r'^[^\[A-Za-z0-9]*', '', title)
    b = [x.strip() for x in re.findall(r'\[([^\]]+)\]', s)
         if not re.match(r'^(C|CONCEPT)\s*#?\s*\d+$', x.strip(), re.I) and not re.match(r'^(talent|P\d|Cross-Persona)', x.strip(), re.I)]
    if len(b) >= 2:
        n = b[1]
    elif len(b) == 1:
        n = b[0].split(':', 1)[1] if ':' in b[0] else b[0]
    else:
        tail = re.sub(r'^.*?C\d+_', '', s)
        n = tail.split('_', 1)[1] if '_' in tail else tail
    n = re.sub(r'\s*\((Shoot|Non Shoot|NO SHOOT|AI|Broll Shoot)\)\s*$', '', n, flags=re.I)
    n = re.sub(r'^(NO SHOOT|Shoot \d|FOUNDER|Founder|AI)\s*:\s*', '', n)
    return re.sub(r'\]-?\s*\w*$', '', n).strip(' []}_-')


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('workdir'); ap.add_argument('--from', dest='frm', required=True)
    ap.add_argument('--to', required=True); ap.add_argument('--out', required=True)
    a = ap.parse_args()
    T = json.load(open(os.path.join(a.workdir, 'tickets.json')))
    plan = json.load(open(os.path.join(a.workdir, 'pull_plan.json')))
    ads = json.load(open(os.path.join(a.workdir, 'ads.json')))
    tickets, editor = T['tickets'], T['editor']
    by_client = defaultdict(list)
    for t in tickets:
        by_client[t['label']].append(t)

    kept, excluded = [], 0
    for ad in ads:
        if EXCLUDE.search(ad['ad_name']):
            excluded += 1; continue
        ad['p'] = parse(ad['ad_name']); ad['sym'] = CUR.get(ad.get('currency', 'GBP'), ad.get('currency', ''))
        kept.append(ad)

    agg, unmatched = {}, []
    for ad in kept:
        t, eds, note = match(ad, by_client.get(ad['client'], []))
        key_region = ad.get('region', '')
        if t:
            k = (t['id'], key_region)
            r = agg.setdefault(k, dict(t=t, region=key_region, sym=ad['sym'], spend=0.0, value=0.0, ads=0))
            r['spend'] += ad['spend']; r['value'] += ad['spend'] * (ad.get('roas') or 0); r['ads'] += 1
        else:
            unmatched.append(dict(ad=ad, eds=eds, note=note))

    rows = list(agg.values())
    if editor:
        rows = [r for r in rows if editor in r['t']['editors']]
        unmatched = [u for u in unmatched if u['eds'] and editor in u['eds']] + \
                    [u for u in unmatched if not u['eds'] and u['ad']['client'] in {t['label'] for t in tickets if editor in t['editors']}]
    podnum = lambda p: int(re.sub(r'\D', '', str(p)) or 99)
    rows.sort(key=lambda r: (podnum(r['t']['pod']), r['t']['label'], r['region'], r['t']['cm'], r['t']['c'] or 0))

    # Approved but no spend found (editor runs, or all runs): tickets due within ~60 days before window end
    end = datetime.strptime(a.to, '%Y-%m-%d'); start_recent = end - timedelta(days=60)
    matched_ids = {r['t']['id'] for r in agg.values()}
    pulled = {p['label'] for p in plan['pull']}
    quiet = []
    for t in tickets:
        if editor and editor not in t['editors']:
            continue
        try:
            due = datetime.strptime(t['due'], '%d %B %Y')
        except ValueError:
            continue
        if editor and start_recent <= due <= end and t['id'] not in matched_ids and t['label'] in pulled:
            quiet.append(t)

    wb = Workbook(); F = 'Arial'
    hf = Font(name=F, bold=True, color='FFFFFF'); fill = PatternFill('solid', fgColor='1F3A5F'); base = Font(name=F)

    def table(ws, heads, widths, start=1):
        for i, (h, w) in enumerate(zip(heads, widths), 1):
            c = ws.cell(start, i, h); c.font = hf; c.fill = fill
            ws.column_dimensions[get_column_letter(i)].width = w
        ws.freeze_panes = ws.cell(start + 1, 1)

    rd = wb.active; rd.title = 'Read me'
    title = f"Edit performance — HP net new — {a.frm} to {a.to}" + (f" — {editor}" if editor else ' — all pods')
    rd['A1'] = title; rd['A1'].font = Font(name=F, bold=True, size=14)
    notes = [
        ('Purpose', 'A coaching and learning view of how edits perform once live. ROAS depends on the script, offer and media buying as much as the edit, so this is not a ranking of editors.' if editor else
         'A learning view of how HP net new edits perform once live, per concept. ROAS depends on the script, offer and media buying as much as the edit, so compare concepts within a client, not editors across clients.'),
        ('Reading ROAS', 'Compare against "Client typical ROAS" on the same row. Spend is in each ad account\'s own currency; never add rows in different currencies together.'),
        ('Ad data', f'Foreplay, {a.frm} to {a.to}, 7-day click / 1-day view, ads with spend over 100 in account currency.'),
        ('Ticket data', f"Editor Tickets export {T.get('export_date') or ''}: Ad Type HP or AI HP, Type = Net new - Editor, Status = Approved or Live, client linked. No due-date cutoff."),
        ('Match rule', 'Client + CM + concept #. Concept # read from the ticket title when the field is empty. Concept-name words break ties. If tickets still tie but share the same editor, the editor is shown on the Unmatched sheet.'),
        ('Excluded', f'Iterations, statics and UGC ({excluded} ad names dropped). Tickets with no client linked.'),
    ]
    if editor:
        notes.insert(1, ('Shared concepts', 'Concepts with more than one editor appear in each editor\'s report and are marked Shared.'))
    for s in plan['skipped']:
        notes.append(('Not covered', f"{s['label']}: {s['note'] or s['status']}"))
    for p in plan['pull']:
        if p['status'] == 'client_naming':
            notes.append(('Low coverage', f"{p['label']}: {p['note']}"))
    rd.column_dimensions['A'].width = 18; rd.column_dimensions['B'].width = 120
    for i, (k, v) in enumerate(notes, 3):
        rd.cell(i, 1, k).font = Font(name=F, bold=True)
        c = rd.cell(i, 2, v); c.font = base; c.alignment = Alignment(wrap_text=True, vertical='top')

    ws = wb.create_sheet('Matched concepts')
    heads = ['Pod', 'Client', 'Account', 'CM', 'Concept #', 'Concept', 'Ad type', 'Editor(s)', 'Shared', 'Currency',
             'Spend', 'Purchase value', 'ROAS', 'Client typical ROAS']
    table(ws, heads, [9, 18, 9, 7, 10, 42, 8, 38, 8, 9, 12, 15, 8, 18])
    for i, r in enumerate(rows, 2):
        t = r['t']
        vals = [t['pod'], t['label'], r['region'], t['cm'], t['c'], concept_name(t['title']), t['ad_type'],
                ', '.join(t['editors']), 'Yes' if len(t['editors']) > 1 else '', r['sym'], round(r['spend']), round(r['value'])]
        for j, v in enumerate(vals, 1):
            ws.cell(i, j, v).font = base
        ws.cell(i, 13, f'=IF(K{i}=0,0,L{i}/K{i})').font = base
        ws.cell(i, 14, f'=IFERROR(SUMIFS(L:L,B:B,B{i},C:C,C{i})/SUMIFS(K:K,B:B,B{i},C:C,C{i}),0)').font = base
        for col, fmt in ((11, '#,##0'), (12, '#,##0'), (13, '0.00'), (14, '0.00')):
            ws.cell(i, col).number_format = fmt
    ws.auto_filter.ref = f"A1:N{max(2, len(rows) + 1)}"

    w2 = wb.create_sheet('Unmatched ads')
    table(w2, ['Client', 'Account', 'Ad name', 'CM / batch', 'Concept #', 'Currency', 'Spend', 'Likely editor(s)', 'Why it did not match'],
          [18, 9, 70, 11, 10, 9, 12, 30, 70])
    for i, u in enumerate(sorted(unmatched, key=lambda u: -u['ad']['spend']), 2):
        ad = u['ad']; p = ad['p']
        vals = [ad['client'], ad.get('region', ''), ad['ad_name'], p['cm'] or p['batch'] or '(none)', p['c'] if p['c'] is not None else '',
                ad['sym'], round(ad['spend']), ', '.join(u['eds']) if u['eds'] else '', u['note']]
        for j, v in enumerate(vals, 1):
            c = w2.cell(i, j, v); c.font = base
        w2.cell(i, 7).number_format = '#,##0'

    if editor:
        w3 = wb.create_sheet('Approved, no spend found')
        table(w3, ['Client', 'CM', 'Concept #', 'Concept', 'Editor(s)', 'Due date'], [18, 7, 10, 50, 38, 16])
        w3.cell(1, 8, 'Approved tickets due in the 60 days to the window end with no matching ad over the spend threshold. Often not launched yet: a media-buying question, not an editing one.').font = Font(name=F, italic=True)
        for i, t in enumerate(sorted(quiet, key=lambda t: (t['label'], t['cm'], t['c'] or 0)), 2):
            for j, v in enumerate([t['label'], t['cm'], t['c'], concept_name(t['title']), ', '.join(t['editors']), t['due']], 1):
                w3.cell(i, j, v).font = base

    wb.save(a.out)
    spend_m = sum(r['spend'] for r in rows); spend_u = sum(u['ad']['spend'] for u in unmatched)
    print(f'Ads parsed: {len(kept)} kept, {excluded} excluded (iteration/static/UGC)')
    print(f'Matched concepts: {len(rows)} | unmatched ad groups: {len(unmatched)} | approved with no spend found: {len(quiet)}')
    print(f'Matched spend (mixed currencies, indicative): {spend_m:,.0f} | unmatched spend: {spend_u:,.0f}')
    print('Saved ' + a.out)


if __name__ == '__main__':
    main()
