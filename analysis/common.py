import pandas as pd, numpy as np, glob, os
# Root folder holding ext/ (downloaded raw data) and work/ (derived panels). Override with KOSPI_ROOT.
S=os.environ.get('KOSPI_ROOT', os.path.join(os.path.dirname(os.path.abspath(__file__)),'..','_data'))
def kospi():
    fs=sorted(glob.glob(S+'/ext/fdrcache/data/index/year_ks11/*.csv'))
    d=pd.concat([pd.read_csv(f,encoding='utf-8-sig') for f in fs])
    d['Date']=pd.to_datetime(d['Date']); d=d.drop_duplicates('Date').set_index('Date').sort_index()
    return d
def usdkrw():
    d=pd.read_csv(S+'/ext/macro/datasets_exchange-rates_main_data_daily.csv')
    d=d[d.Country=='South Korea'].copy(); d['Date']=pd.to_datetime(d['Date'])
    s=d.set_index('Date')['Exchange rate'] if 'Exchange rate' in d else d.set_index('Date').iloc[:,-1]
    return pd.to_numeric(s,errors='coerce').dropna()
def breadth(): return pd.read_parquet(S+'/work/breadth.parquet')
def find_cycles(px, thr=0.20):
    """Drawdown/rally zig-zag: alternate peaks/troughs where reversal >= thr."""
    p=px.values; idx=px.index
    piv=[]; mode=None; ext_i=0
    for i in range(1,len(p)):
        if mode is None:
            if p[i]>=p[ext_i]*(1+thr): piv.append(('T',ext_i)); mode='up'; ext_i=i
            elif p[i]<=p[ext_i]*(1-thr): piv.append(('P',ext_i)); mode='dn'; ext_i=i
            elif (p[i]>p[ext_i] and False): pass
            continue
        if mode=='up':
            if p[i]>p[ext_i]: ext_i=i
            elif p[i]<=p[ext_i]*(1-thr): piv.append(('P',ext_i)); mode='dn'; ext_i=i
        else:
            if p[i]<p[ext_i]: ext_i=i
            elif p[i]>=p[ext_i]*(1+thr): piv.append(('T',ext_i)); mode='up'; ext_i=i
    piv.append(('P' if mode=='up' else 'T', ext_i))
    return [(t,idx[i],p[i]) for t,i in piv]
