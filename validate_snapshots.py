#!/usr/bin/env python3
"""Read-only validation of every published snapshot; never deletes or re-scans."""
import sys
import config
from contracts import read_csv
from sonar_evidence import DATA, verify_snapshot


def main():
    if len(sys.argv) != 1:
        print('Validation is read-only. --fix is no longer supported; preserve failed evidence.')
        return 2
    try:
        _, rows = read_csv(DATA / 'snapshots.csv', required=['label', 'commit_hash'], key='label')
        if not rows:
            raise ValueError('No snapshots to validate')
        analyses = {}
        for row in rows:
            proof = verify_snapshot(row['label'], config.REPO_PATH, row['commit_hash'])
            identity = (proof['project_key'], proof['analysis_id'])
            previous = analyses.setdefault(identity, row['commit_hash'])
            if previous != row['commit_hash']:
                raise ValueError('One analysis assigned to different commits')
        print(f'PASS: {len(rows)} complete snapshots bound to exact Git/task/export evidence.')
        return 0
    except (ValueError, OSError, KeyError, TypeError) as exc:
        print(f'FAIL: {type(exc).__name__}: {exc}')
        return 2


if __name__ == '__main__':
    sys.exit(main())
