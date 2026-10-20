"""New mechanisms/streams; no previous experiment labels are imported."""
from datetime import datetime, timedelta, timezone
import hashlib
import numpy as np
from forecasting_research.phase6_0.contracts import Request, digest, iso, utc

FAMILIES = ('constant', 'growth', 'decay', 'stairs_up', 'stairs_down', 'cycle',
            'mean_reverting', 'stationary_noise', 'quiet_jump', 'trend_stop',
            'sparse', 'irregular')
OOD = ('reversal', 'chirp', 'damped', 'renewal', 'volatility_shift', 'hidden_switch')
COUNTS = dict(train=48, validation=24, calibration=24, test=32, ood=48, identifiability=24)
REPLICAS = (64120261020, 64120261021)
ORIGIN = datetime(2026, 1, 1, tzinfo=timezone.utc)


def seed(*parts):
    return int(hashlib.sha256('/'.join(map(str, parts)).encode()).hexdigest()[:16], 16)


def generate(replica, partition, family, index):
    if replica not in REPLICAS or partition not in COUNTS or family not in (OOD if partition in ('ood','identifiability') else FAMILIES):
        raise ValueError('Registered generator identity required')
    # Stress triples share only history and parameters: stable/up/down hidden futures.
    # This is deliberate within-group dependence, never cross-partition reuse.
    group = index // 3 if partition == 'identifiability' else index
    rng = np.random.default_rng(seed(replica, partition, family, group))
    future = np.random.default_rng(seed(replica, partition, family, group, 'future'))
    scale = float((1., 30., 300., 30000.)[group % 4] * rng.uniform(.8, 1.2))
    rate = float(rng.uniform(.008, .018))
    period = float(rng.uniform(35, 85))
    phase = float(rng.uniform(0, 2*np.pi))
    t = np.arange(-255, 91, dtype=float)
    base = family
    if family in ('sparse', 'irregular'):
        base = ('growth', 'decay', 'constant', 'cycle')[group % 4]
    if base == 'constant': y = np.full(len(t), scale)
    elif base in ('growth', 'decay'):
        y = scale * np.exp((1 if base == 'growth' else -1)*rate*np.clip(t, -90, 90))
    elif base in ('stairs_up', 'stairs_down'):
        sign = 1 if base == 'stairs_up' else -1
        y = scale * np.maximum(.02, 1 + sign*.28*np.floor((t+float(rng.uniform(0, 12)))/18))
    elif base == 'cycle': y = scale*(1+.35*np.sin(2*np.pi*t/period+phase))
    elif base == 'mean_reverting':
        z = [float(rng.normal())]
        for _ in t[1:]: z.append(.85*z[-1]+float(rng.normal(0,.08)))
        y = scale*np.maximum(0, 1+np.array(z)*.2)
    elif base == 'stationary_noise': y = scale*np.maximum(0, 1+rng.normal(0,.03,len(t)))
    elif base == 'quiet_jump':
        y = np.full(len(t), scale)
        event = int(rng.integers(-150, 70)); sign = -1 if group % 2 else 1
        y[t>=event] += sign*.45*scale
    elif base == 'trend_stop':
        stop = float(rng.uniform(-20, 60)); sign = -1 if group % 2 else 1
        y = scale*np.maximum(.05, 1+sign*.006*np.clip(t,-90,stop))
    elif base == 'reversal': y = scale*np.maximum(.05,1+.012*t*np.where(t<0,1,-1))
    elif base == 'chirp': y = scale*(1+.3*np.sin(phase+.0007*t*t))
    elif base == 'damped': y = scale*(1+.4*np.exp(-np.maximum(t+255,0)/180)*np.sin(t/9+phase))
    elif base == 'renewal':
        y = np.full(len(t),scale)
        for event in rng.choice(np.arange(-230, 90), 7, replace=False):
            y[t>=event] += float(rng.choice([-1,1]))*.12*scale
        y = np.maximum(0,y)
    elif base == 'volatility_shift': y = scale*np.maximum(0,1+rng.normal(0,1,len(t))*np.where(t<0,.01,.3))
    elif base == 'hidden_switch': y = np.full(len(t),scale)
    else: raise ValueError('Unknown mechanism')
    # Main future cessation is independent of history, at fixed 1/4 probability.
    # It deliberately prevents training from assuming every visible trend continues.
    if partition != 'identifiability' and future.random() < .25:
        y[t>0] = y[t==0][0]
    if partition == 'identifiability':
        current = float(y[t==0][0]); branch=index%3
        if branch == 0:
            # Unchanged exact endpoints with real intermediate excursions.
            y[t>0] = current + .15*scale*np.sin(np.pi*t[t>0]/30)**2
            y[np.isin(t, [30,60,90])] = current
        else:
            event=int(future.integers(1,20)); magnitude=float(future.uniform(.3,.65))*current
            y[t>0]=current
            y[t>=event] = max(0.,current+(1 if branch==1 else -1)*magnitude)
    if base == 'constant' and group % 12 == 0:
        # Unique near-zero histories, genuinely generated; origin/future zero.
        # All-zero identical histories are covered by analytical unit fixtures.
        y[:] = 0.; y[0] = scale*1e-4
    history=y[t<=0].tolist(); dates=[iso(ORIGIN+timedelta(days=int(d))) for d in t[t<=0]]
    if family == 'sparse':
        history=[v if i%7==3 or i==255 else None for i,v in enumerate(history)]
    if family == 'irregular':
        keep=[i for i in range(256) if i==255 or rng.random()<.2]
        dates=[dates[i] for i in keep];history=[history[i] for i in keep]
    cid='synthetic-'+hashlib.sha256(f'{replica}/{partition}/{family}/{index}'.encode()).hexdigest()[:24]
    req=Request(cid,iso(ORIGIN),tuple(dates),tuple(history),tuple('SYNTHETIC_UNOBSERVED' if v is None else None for v in history))
    targets={str(h):dict(timestamp_utc=req.endpoint(h),value=float(y[t==h][0])) for h in (30,60,90)}
    return dict(request=req.as_dict(),targets=targets,metadata=dict(partition=partition,family=family,
        group=f'{replica}/{partition}/{family}/{group}',replica=replica,scale_band=group%4,
        history_sha256=digest(dict(timestamps=list(range(len(history))),values=history,
                                  offsets=[(utc(d)-ORIGIN).days for d in dates])),
        parameters_sha256=digest(dict(scale=scale,rate=rate,period=period,phase=phase))))


def population(replica, partition):
    return [generate(replica,partition,f,i) for f in (OOD if partition in ('ood','identifiability') else FAMILIES)
            for i in range(COUNTS[partition])]
