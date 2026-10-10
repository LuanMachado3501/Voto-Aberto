"""Linha do tempo de candidaturas (TSE, histórico ligado à candidatura de 2026)."""
import pandas as pd, json
U='/root/.claude/uploads/4ca0478c-f08e-50ae-9016-3a44578f0aff/'
h=pd.read_csv(U+'6a122d89-historico_candidatura_2026_BRASIL.csv',sep=';',encoding='latin1',dtype=str)
h['NR_TURNO']=h.NR_TURNO.astype(int)
h=h.sort_values('NR_TURNO').drop_duplicates(['SQ_CANDIDATO_ATUAL','SQ_CANDIDATO'],keep='last')
print(h.ANO_ELEICAO.value_counts().sort_index().to_dict())
H=json.load(open('historico_data.json'))
g={k:v for k,v in h.groupby('SQ_CANDIDATO_ATUAL')}
n=0
for i,d in H['deps'].items():
    t=d.get('tse')
    if not t or t['sq'] not in g: d['hc']=[]; continue
    rows=g[t['sq']].sort_values('ANO_ELEICAO',ascending=False)
    d['hc']=[[int(r.ANO_ELEICAO),r.DS_CARGO.title() if r.DS_CARGO.isupper() else r.DS_CARGO,(r.NM_UE.title() if r.TP_ABRANGENCIA_ELEICAO=='M' else r.SG_UF),r.SG_PARTIDO,r.DS_SIT_TOT_TURNO] for r in rows.itertuples()]
    if not d['hc'] or d['hc'][0][0]!=2026:
        sit=t['sit'].capitalize().replace('qp','QP')
        d['hc'].insert(0,[2026,t['cargo'],t['uf'],t['partido'],sit])
    n+=1
json.dump(H,open('historico_data.json','w'),ensure_ascii=False,separators=(',',':'))
print('com histórico',n)
from collections import Counter
print(Counter(x[4] for d in H['deps'].values() for x in d.get('hc',[])).most_common(12))
for nm in ['209787','204411','107283','74041']: print(H['deps'][nm].get('hc'))
