"""Strict local evidence IO. Missing observations are never silently synthesized."""
import csv
import hashlib
import io
import json
import math
import os
import re
import tempfile
from pathlib import Path, PurePosixPath


def number(value):
    if value is None or isinstance(value, str) and not value.strip():
        return None
    if isinstance(value, bool):
        raise ValueError('Boolean measurement')
    try:
        result = float(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f'Malformed measurement: {value!r}') from exc
    if not math.isfinite(result) or result < 0:
        raise ValueError(f'Invalid measurement: {value!r}')
    return result


def ratio(numerator, denominator, scale=1):
    if numerator is None or denominator is None or denominator <= 0:
        return None
    return round(scale * numerator / denominator, 8)


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':'),
                                     allow_nan=False).encode()).hexdigest()


def sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def safe_id(value):
    if not isinstance(value, str) or not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_.-]*', value):
        raise ValueError(f'Unsafe identifier: {value!r}')
    return value


def source_path(value):
    if not isinstance(value, str) or not value or '\\' in value or any(ord(c) < 32 for c in value):
        raise ValueError(f'Invalid source path: {value!r}')
    p = PurePosixPath(value)
    if p.is_absolute() or value == '.' or '..' in p.parts or str(p) != value:
        raise ValueError(f'Noncanonical source path: {value!r}')
    return value


def read_csv(path, required=(), key=None):
    with open(path, newline='', encoding='utf-8') as f:
        reader = csv.reader(f, strict=True)
        header = next(reader, None)
        if not header or len(header) != len(set(header)) or any(not c for c in header):
            raise ValueError(f'{path}: invalid/duplicate CSV header')
        if not set(required) <= set(header):
            raise ValueError(f'{path}: missing columns {set(required) - set(header)}')
        rows, seen = [], set()
        for values in reader:
            if len(values) != len(header):
                raise ValueError(f'{path}: invalid CSV row width')
            row = dict(zip(header, values))
            if key:
                unit = tuple(row[k] for k in key) if not isinstance(key, str) else row[key]
                if not unit or isinstance(unit, tuple) and not all(unit) or unit in seen:
                    raise ValueError(f'{path}: missing/duplicate identity {unit!r}')
                seen.add(unit)
            rows.append(row)
    return header, rows


def _unique_object(pairs):
    obj = {}
    for key, value in pairs:
        if key in obj:
            raise ValueError(f'Duplicate JSON key: {key}')
        obj[key] = value
    return obj


def read_json(path):
    return json.loads(Path(path).read_text(encoding='utf-8'), object_pairs_hook=_unique_object,
                      parse_constant=lambda v: (_ for _ in ()).throw(ValueError(v)))


def atomic_bytes(path, content):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, name = tempfile.mkstemp(prefix='.' + path.name + '.', dir=path.parent)
    try:
        with os.fdopen(fd, 'wb') as f:
            f.write(content)
            f.flush()
            os.fsync(f.fileno())
        os.replace(name, path)
    finally:
        if os.path.exists(name):
            os.unlink(name)


def write_json(path, obj):
    atomic_bytes(path, (json.dumps(obj, indent=2, sort_keys=True, allow_nan=False) + '\n').encode())


def write_csv(path, rows, fields):
    f = io.StringIO(newline='')
    writer = csv.DictWriter(f, fieldnames=fields)
    writer.writeheader()
    writer.writerows(rows)
    atomic_bytes(path, f.getvalue().encode('utf-8'))


def insert_csv(path, row):
    path = Path(path)
    fields, rows = read_csv(path, required=row, key='label') if path.exists() else (list(row), [])
    if set(fields) != set(row) or any(r['label'] == row['label'] for r in rows):
        raise ValueError(f'{path}: conflicting label/schema')
    write_csv(path, rows + [row], fields)
