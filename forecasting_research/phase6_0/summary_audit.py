"""Permitted arithmetic on two small published aggregate/per-repository tables ONLY."""
from pathlib import Path
import csv,math,statistics
from .artifacts import sha,write


def audit(output):
    project=Path(__file__).resolve().parents[2]
    names=('chronos_comparison_metrics.csv','chronos_interval_metrics.csv')
    paths=[project/'examples/phase4_2'/n for n in names]
    if any(p.stat().st_size>1024*1024 for p in paths):raise ValueError('Small published summaries only')
    points,intervals=[list(csv.DictReader(p.open())) for p in paths]
    if any('actual' in r or 'target_minutes' in r for r in points+intervals):raise ValueError('No raw labels admitted')
    checks=0;tables=[]
    for row in points:
        if row['repository_id']!='ALL':continue
        peers=[r for r in points if r['repository_id']!='ALL' and int(r['n'])>0 and all(r[k]==row[k] for k in ('evaluation_phase','horizon_days','subset','model'))]
        assert sum(int(p['n']) for p in peers)==int(row['n'])
        if not peers:
            assert row['macro_mae']==row['pooled_mae']==''
            continue
        macro=statistics.mean(float(p['macro_mae']) for p in peers)
        pooled=sum(int(p['n'])*float(p['pooled_mae']) for p in peers)/int(row['n'])
        assert math.isclose(macro,float(row['macro_mae']),rel_tol=1e-12,abs_tol=1e-10)
        assert math.isclose(pooled,float(row['pooled_mae']),rel_tol=1e-12,abs_tol=1e-10)
        checks+=2
        if row['model'] in ('persistence','chronos_small'):
            base=float(row['persistence_macro_mae']);gain=None if base==0 else 1-macro/base
            if gain is not None:assert math.isclose(gain,float(row['macro_mae_gain_fraction']),abs_tol=1e-12)
            tables.append({k:row[k] for k in ('evaluation_phase','horizon_days','subset','model','n')}|
                          dict(repository_macro_mae=macro,pooled_mae=pooled,persistence_skill=gain))
    population=[]
    for phase in ('validation','test_temporal','test_repository'):
        for h in ('30','60','90'):
            chosen=[r for r in points if r['repository_id']=='ALL' and r['evaluation_phase']==phase and r['horizon_days']==h and r['model']=='persistence']
            by={r['subset']:r for r in chosen};n=int(by['all']['n']);unchanged=int(by['unchanged_debt']['n'])
            assert int(by['changing_debt']['n'])+unchanged==n
            population.append(dict(phase=phase,horizon_days=int(h),n=n,unchanged=unchanged,unchanged_fraction=unchanged/n,
                 persistence_unchanged_pooled_mae=float(by['unchanged_debt']['pooled_mae'])))
    output_value=dict(status='SUMMARY_ARITHMETIC_REPRODUCED_NOT_BENCHMARK_RERUN',checks=checks,
         sources={p.name:sha(p) for p in paths},point_summaries=tables,population=population,
         interval_summaries=[r for r in intervals if r['repository_id']=='ALL'],
         raw_label_files_opened=0,original_benchmark_calls=0)
    write(output,output_value);return output_value
