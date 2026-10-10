"""% de votos alinhados à orientação do líder do governo (2025-26), por deputado."""
import pandas as pd, json
U='/root/.claude/uploads/4ca0478c-f08e-50ae-9016-3a44578f0aff/'
o=pd.concat([pd.read_csv(U+f,sep=';',encoding='utf-8-sig',dtype=str) for f in ['2caec7cf-votacoesOrientacoes-2025.csv','22adbd58-votacoesOrientacoes-2026.csv']])
g=o[(o.siglaBancada=='Governo')&o.orientacao.isin(['Sim','Não'])][['idVotacao','orientacao']].drop_duplicates('idVotacao')
w=pd.concat([pd.read_csv(f,sep=';',encoding='utf-8-sig',dtype=str,usecols=['idVotacao','voto','deputado_id']) for f in ['/mnt/user-data/uploads/votacoesVotos-2025__1_.csv',U+'d5d70b6b-votacoesVotos-2026.csv']])
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
