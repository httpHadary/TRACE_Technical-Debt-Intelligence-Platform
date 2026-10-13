#!/usr/bin/env python3
"""Resume complete exports first; submit only genuinely new weekly snapshots."""
import sys
from pathlib import Path

import config
from contracts import atomic_bytes, read_csv, read_json, write_json
from scan_snapshot import scan_snapshot
from sonar_evidence import DATA, collect_snapshot, upsert_equal, verify_snapshot, workspace_lock
from weekly_commits import resolve_weekly_commits


def fill_week_from(src_label, dst_label):
    proof = read_json(DATA / f'complete_{src_label}.json')
    verify_snapshot(src_label, config.REPO_PATH, proof['commit'])
    if (DATA / f'complete_{dst_label}.json').exists() or (DATA / f'pending_{dst_label}.json').exists():
        raise ValueError('Destination already has scan evidence')
    for kind, ext in [('measures','csv'),('issues','json')]:
        atomic_bytes(DATA / f'{kind}_{dst_label}.{ext}', (DATA / f'{kind}_{src_label}.{ext}').read_bytes())
    proof.update(label=dst_label, reused_from=src_label)
    proof['snapshot']['label'] = dst_label
    proof['metadata']['label'] = dst_label
    upsert_equal(DATA / 'snapshots.csv', proof['snapshot'])
    upsert_equal(DATA / 'analysis_metadata.csv', proof['metadata'])
    write_json(DATA / f'complete_{dst_label}.json', proof)


def main():
    if '--force' in sys.argv:
        raise SystemExit('Force overwrite is disabled; preserve this workspace and choose a fresh one')
    if len(sys.argv) not in (2,3,4):
        raise SystemExit('Usage: scan_weekly_snapshots.py START [BRANCH] [WEEKS]')
    start = sys.argv[1]
    branch = sys.argv[2] if len(sys.argv)>2 else config.BRANCH
    count = int(sys.argv[3]) if len(sys.argv)>3 else config.DEFAULT_WEEKS
    weeks = resolve_weekly_commits(config.REPO_PATH, start, branch, count)
    if not weeks:
        raise ValueError('No complete weeks')
    with workspace_lock():
        previous = None
        for w, bounds in weeks.items():
            label, commit = f'week_{w:02d}', bounds['commit']
            if not commit:
                raise ValueError(f'{label}: missing historical commit')
            complete = DATA / f'complete_{label}.json'
            pending = DATA / f'pending_{label}.json'
            if complete.exists():
                verify_snapshot(label, config.REPO_PATH, commit)
            elif pending.exists():
                if read_json(pending)['commit'] != commit:
                    raise ValueError('Pending attempt commit mismatch')
                collect_snapshot(label)  # export recovery only; never silently resubmit
            elif (DATA / f'measures_{label}.csv').exists() or (DATA / f'issues_{label}.json').exists():
                raise ValueError('Legacy/incomplete evidence needs independent verification; use a fresh workspace')
            elif previous and previous[1] == commit:
                fill_week_from(previous[0], label)
            else:
                if (DATA / 'snapshots.csv').exists():
                    _, rows = read_csv(DATA / 'snapshots.csv', key='label')
                    if any(r['label']==label for r in rows):
                        raise ValueError('Snapshot registration without complete task evidence')
                scan_snapshot(commit, label)
                collect_snapshot(label)
            previous = (label, commit)


if __name__ == '__main__':
    main()
