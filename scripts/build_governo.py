"""% de votos alinhados à orientação do líder do governo (2025-26), por deputado."""
import pandas as pd, json
import os
RAW=os.environ.get('RAW','/home/claude/voto_aberto/raw')+'/'
o=pd.concat([pd.read_csv(RAW+f,sep=';',encoding='utf-8-sig',dtype=str) for f in ['votacoesOrientacoes-2025.csv','votacoesOrientacoes-2026.csv']])
g=o[(o.siglaBancada=='Governo')&o.orientacao.isin(['Sim','Não'])][['idVotacao','orientacao']].drop_duplicates('idVotacao')
w=pd.concat([pd.read_csv(f,sep=';',encoding='utf-8-sig',dtype=str,usecols=['idVotacao','voto','deputado_id']) for f in [RAW+'votacoesVotos-2025.csv',RAW+'votacoesVotos-2026.csv']])
n=w.groupby('idVotacao').size(); w=w[w.idVotacao.isin(n[n>=300].index)&w.voto.isin(['Sim','Não'])]
m=w.merge(g,on='idVotacao'); m['ok']=m.voto==m.orientacao
r=m.groupby('deputado_id').ok.agg(['mean','size'])
H=json.load(open('historico_data.json'))
for i,v in H['deps'].items():
    v['gov']=round(float(r.loc[i,'mean'])*100) if i in r.index and r.loc[i,'size']>=20 else None
H['gov_n']=int(g.idVotacao.isin(w.idVotacao).sum())
json.dump(H,open('historico_data.json','w'),ensure_ascii=False,separators=(',',':'))
hem=json.load(open('hemiciclo_data.json'))
import statistics as st
by={}
for d in hem['deps']:
    x=H['deps'][d['id']]['gov']
    if x is not None: by.setdefault(d['p'],[]).append(x)
print('votações com orientação do governo:',H['gov_n'])
print(sorted(((p,round(st.mean(v)),len(v)) for p,v in by.items()),key=lambda z:-z[1]))
