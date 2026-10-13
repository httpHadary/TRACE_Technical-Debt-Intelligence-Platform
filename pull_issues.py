#!/usr/bin/env python3
"""Complete, unique issue pagination with explicit taxonomy and effort validation."""
from td_utils import parse_minutes

STATUSES = 'OPEN,CONFIRMED,REOPENED,RESOLVED,CLOSED'
SEVERITIES = ['BLOCKER', 'CRITICAL', 'MAJOR', 'MINOR', 'INFO']
TYPES = ['BUG', 'VULNERABILITY', 'CODE_SMELL']
MAX_RESULTS_PER_QUERY = 10000


def fetch_all(extra_params, remaining_dims, fetch):
    page, collected, total, seen = 1, [], None, set()
    while True:
        data = fetch(extra_params, page)
        current_total = data.get('total', data.get('paging', {}).get('total'))
        if type(current_total) is not int or current_total < 0 or total is not None and total != current_total:
            raise ValueError('Missing/inconsistent issue total')
        total = current_total
        if total > MAX_RESULTS_PER_QUERY:
            if not remaining_dims:
                raise ValueError('Issue query exceeds supported partition size; no truncated export published')
            dim, values = remaining_dims[0]
            out = []
            for value in values:
                out.extend(fetch_all({**extra_params, dim:value}, remaining_dims[1:], fetch))
            if len(out) != total or len({i['key'] for i in out}) != total:
                raise ValueError('Split issue population incomplete/duplicated')
            return out
        items = data.get('issues')
        if not isinstance(items, list) or len(items) != min(500, total - len(collected)):
            raise ValueError('Incomplete/extra issue page')
        paging = data.get('paging', {})
        if paging and (paging.get('pageIndex') != page or paging.get('pageSize') != 500):
            raise ValueError('Invalid issue page index/size')
        for item in items:
            if not item.get('key') or item['key'] in seen:
                raise ValueError('Duplicate/missing issue key')
            seen.add(item['key'])
        collected.extend(items)
        if len(collected) == total:
            return collected
        page += 1


def normalize_issues(raw):
    seen, result = set(), []
    for item in raw:
        if not item.get('key') or item['key'] in seen:
            raise ValueError('Duplicate/missing issue key')
        seen.add(item['key'])
        if item.get('type') not in TYPES or item.get('severity') not in SEVERITIES or item.get('status') not in STATUSES.split(','):
            raise ValueError('Unsupported issue taxonomy')
        if not item.get('component') or not item.get('rule'):
            raise ValueError('Incomplete issue record')
        effort = item.get('debt') if item.get('debt') is not None else item.get('effort')
        result.append({**item, 'effort_minutes': parse_minutes(effort)})
    return result


if __name__ == '__main__':
    from sonar_evidence import export_main
    export_main()
