"""Immutable past-only requests and identity-bound native daily responses."""
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
import hashlib
import json
import math
from . import VERSION, STATUS, UNIT


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()


def digest(value):
    return hashlib.sha256(canonical(value)).hexdigest()


def utc(text):
    if not isinstance(text, str):
        raise ValueError('Explicit UTC timestamp required')
    try:
        stamp = datetime.strptime(text, '%Y-%m-%dT%H:%M:%SZ').replace(tzinfo=timezone.utc)
    except ValueError as exc:
        raise ValueError('Exact UTC seconds required') from exc
    if stamp.strftime('%Y-%m-%dT%H:%M:%SZ') != text:
        raise ValueError('Canonical UTC required')
    return stamp


def iso(stamp):
    return stamp.strftime('%Y-%m-%dT%H:%M:%SZ')


def finite(value):
    if type(value) not in (float, int) or not math.isfinite(value):
        raise ValueError('Finite numeric value required; bool is not a measurement')
    return float(value)


def exact(obj, fields):
    if not isinstance(obj, dict) or set(obj) != set(fields):
        raise ValueError('Only versioned allowlisted fields admitted; labels/splits forbidden')


@dataclass(frozen=True)
class Request:
    case_id: str
    origin_utc: str
    timestamps: tuple
    values: tuple
    reasons: tuple
    horizons: tuple = (30, 60, 90)
    version: str = VERSION
    status: str = STATUS
    unit: str = UNIT

    def __post_init__(self):
        if (self.version, self.status, self.unit) != (VERSION, STATUS, UNIT):
            raise ValueError('Synthetic research contract and original estimand units required')
        if not isinstance(self.case_id, str) or not self.case_id.startswith('synthetic-'):
            raise ValueError('Synthetic identity required')
        if any(type(x) is not tuple for x in (self.timestamps, self.values, self.reasons, self.horizons)):
            raise ValueError('Immutable tuple inputs required')
        if self.horizons != (30, 60, 90) or any(type(h) is not int for h in self.horizons):
            raise ValueError('Exact 30/60/90-day horizons required')
        if not 2 <= len(self.values) <= 8192 or len(self.values) != len(self.timestamps) or len(self.values) != len(self.reasons):
            raise ValueError('Bounded aligned history required')
        origin, previous = utc(self.origin_utc), None
        for stamp, value, reason in zip(self.timestamps, self.values, self.reasons):
            date = utc(stamp)
            if date > origin or (previous is not None and date <= previous):
                raise ValueError('Only unique ordered past observations admitted')
            if value is None:
                if reason != 'SYNTHETIC_UNOBSERVED':
                    raise ValueError('Missing must retain null plus explicit reason')
            elif finite(value) < 0 or reason is not None:
                raise ValueError('Nonnegative stock and valid observation required')
            previous = date
        if previous != origin:
            raise ValueError('Explicit origin observation or missing record required; no carry')

    @classmethod
    def from_dict(cls, value):
        exact(value, ('case_id','origin_utc','timestamps','values','reasons','horizons','version','status','unit'))
        arrays = ('timestamps','values','reasons','horizons')
        if any(not isinstance(value[k], list) for k in arrays):
            raise ValueError('JSON arrays required')
        return cls(**{k:tuple(v) if k in arrays else v for k,v in value.items()})

    def as_dict(self):
        return {k:list(v) if isinstance(v,tuple) else v for k,v in vars(self).items()}

    @property
    def identity(self):
        return digest(self.as_dict())

    def complete_daily(self, length=90):
        start = utc(self.origin_utc) - timedelta(days=length-1)
        return (len(self.values)==length and all(v is not None for v in self.values)
                and all(utc(t)==start+timedelta(days=i) for i,t in enumerate(self.timestamps)))

    def endpoint(self, horizon):
        if type(horizon) is not int or horizon not in self.horizons:
            raise ValueError('Invalid horizon')
        return iso(utc(self.origin_utc)+timedelta(days=horizon))


def response(request, model, raw_path, *, quantiles=False):
    if not isinstance(request,Request) or not isinstance(model,str) or not model:
        raise ValueError('Typed request and model identity required')
    if not isinstance(raw_path,list) or len(raw_path)!=90:
        raise ValueError('Exactly 90 native daily steps required')
    path=[]
    for step,row in enumerate(raw_path,1):
        exact(row, ('timestamp_utc','raw_point','raw_q10','raw_q50','raw_q90'))
        if row['timestamp_utc']!=iso(utc(request.origin_utc)+timedelta(days=step)):
            raise ValueError('Future daily timestamp mismatch; never relabel weekly steps')
        point=finite(row['raw_point']);qs=[row[k] for k in ('raw_q10','raw_q50','raw_q90')]
        if quantiles:
            qs=list(map(finite,qs))
            if not qs[0]<=qs[1]<=qs[2]:
                raise ValueError('NATIVE_QUANTILE_CROSSING: never sort')
            if point!=qs[1]:
                raise ValueError('Point policy is native q50')
        elif any(q is not None for q in qs):
            raise ValueError('Baseline intervals unavailable; never invent quantiles')
        path.append(dict(row,point=max(0.0,point),q10=max(0.0,qs[0]) if quantiles else None,
                         q50=max(0.0,qs[1]) if quantiles else None,q90=max(0.0,qs[2]) if quantiles else None))
    return dict(version=VERSION,status=STATUS,unit=UNIT,request_id=request.identity,case_id=request.case_id,
                model=model,stock_policy='max(0, raw); raw retained',path=path)


def validate_response(request, value, model):
    exact(value, ('version','status','unit','request_id','case_id','model','stock_policy','path'))
    if not isinstance(value['path'],list) or len(value['path'])!=90:
        raise ValueError('Bounded native path required')
    for row in value['path']:
        exact(row, ('timestamp_utc','raw_point','raw_q10','raw_q50','raw_q90','point','q10','q50','q90'))
        finite(row['point'])
        for key in ('q10','q50','q90'):
            if row[key] is not None:finite(row[key])
    raw=[{k:r[k] for k in ('timestamp_utc','raw_point','raw_q10','raw_q50','raw_q90')} for r in value['path']]
    expected=response(request,model,raw,quantiles=any(r['raw_q10'] is not None for r in raw))
    if value!=expected:
        raise ValueError('Response identity, policy or content mismatch')
    return value
