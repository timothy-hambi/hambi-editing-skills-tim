#!/usr/bin/env python3
"""Lock check for iteration edits.

An iteration changes a few named things in a finished ad and leaves the rest
alone. This script proves the "rest" really is unchanged: for every locked
range it compares the new render against the original export, picture and
sound, and prints PASS or FAIL per range.

Usage:
  python lock_check.py --original orig.mp4 --new CS_..._V1_v1.mp4 --spec spec.json --variation V1
  python lock_check.py --original orig.mp4 --new new.mp4 --ranges ranges.json

A range is {"label": "body", "orig_in": 4.0, "orig_out": 31.2, "new_in": 5.1}
(seconds). In spec.json they live at variations.<ID>.locked.

Exit code 0 = every range passed, 1 = at least one failed.
"""
import argparse
import json
import re
import subprocess
import sys

import numpy as np

SSIM_MIN = 0.975     # compared at 360x640; one high-quality re-encode sits around 0.99
CORR_MIN = 0.95      # audio waveform correlation
LEVEL_MAX_DB = 1.0   # locked audio must not be re-levelled
SR = 16000


def video_ssim(orig, new, o_in, n_in, dur):
    fc = (
        f"[0:v]trim=start={o_in}:duration={dur},setpts=PTS-STARTPTS,fps=15,scale=360:640[a];"
        f"[1:v]trim=start={n_in}:duration={dur},setpts=PTS-STARTPTS,fps=15,scale=360:640[b];"
        f"[a][b]ssim"
    )
    p = subprocess.run(
        ["ffmpeg", "-hide_banner", "-nostdin", "-i", orig, "-i", new,
         "-filter_complex", fc, "-an", "-f", "null", "-"],
        capture_output=True, text=True)
    m = re.findall(r"All:([0-9.]+)", p.stderr)
    return float(m[-1]) if m else None


def audio(path, start, dur):
    p = subprocess.run(
        ["ffmpeg", "-hide_banner", "-nostdin", "-ss", str(start), "-t", str(dur), "-i", path,
         "-vn", "-ac", "1", "-ar", str(SR), "-f", "f32le", "-"],
        capture_output=True)
    return np.frombuffer(p.stdout, dtype=np.float32)


def audio_compare(orig, new, o_in, n_in, dur):
    a, b = audio(orig, o_in, dur), audio(new, n_in, dur)
    n = min(len(a), len(b))
    if n < SR // 4:
        return None, None, None
    a, b = a[:n], b[:n]
    best, best_lag = -1.0, 0
    for lag in range(-800, 801, 40):          # +/- 50 ms in 2.5 ms steps
        x, y = (a[lag:], b[:n - lag]) if lag >= 0 else (a[:n + lag], b[-lag:])
        if x.std() < 1e-6 or y.std() < 1e-6:
            continue
        c = float(np.corrcoef(x, y)[0, 1])
        if c > best:
            best, best_lag = c, lag
    rms = lambda s: 20 * np.log10(max(float(np.sqrt(np.mean(s ** 2))), 1e-9))
    return best, best_lag / SR * 1000, rms(b) - rms(a)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--original", required=True)
    ap.add_argument("--new", required=True)
    ap.add_argument("--spec")
    ap.add_argument("--variation")
    ap.add_argument("--ranges")
    args = ap.parse_args()

    if args.ranges:
        ranges = json.load(open(args.ranges))
    elif args.spec and args.variation:
        ranges = json.load(open(args.spec))["variations"][args.variation]["locked"]
    else:
        sys.exit("Give --ranges, or --spec with --variation")

    failed = False
    print(f"{'range':<16}{'orig in-out':<18}{'new in':<9}{'SSIM':<8}{'audio':<8}{'lag ms':<8}{'level dB':<10}result")
    for r in ranges:
        dur = round(r["orig_out"] - r["orig_in"], 3)
        ssim = video_ssim(args.original, args.new, r["orig_in"], r["new_in"], dur)
        corr, lag, lvl = audio_compare(args.original, args.new, r["orig_in"], r["new_in"], dur)
        problems = []
        if ssim is None or ssim < SSIM_MIN:
            problems.append("picture differs")
        if corr is None:
            problems.append("no audio to compare")
        else:
            if corr < CORR_MIN:
                problems.append("audio differs")
            if abs(lag) > 20:
                problems.append("audio out of sync")
            if abs(lvl) > LEVEL_MAX_DB:
                problems.append("audio level moved")
        failed |= bool(problems)
        f = lambda v, p: "n/a" if v is None else f"{v:.{p}f}"
        print(f"{r.get('label', '-'):<16}{str(r['orig_in']) + '-' + str(r['orig_out']):<18}{r['new_in']:<9}"
              f"{f(ssim, 3):<8}{f(corr, 3):<8}{f(lag, 0):<8}{f(lvl, 2):<10}"
              f"{'FAIL: ' + ', '.join(problems) if problems else 'PASS'}")
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()
