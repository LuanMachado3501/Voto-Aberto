"""Últimas votações de 2026 (com título) e presença nas votações nominais de 2026."""
import pandas as pd, json, re
import os
RAW=os.environ.get('RAW','/home/claude/voto_aberto/raw')+'/'
w=pd.read_csv(RAW+'votacoesVotos-2026.csv',sep=';',encoding='utf-8-sig',dtype=str,usecols=['idVotacao','voto','deputado_id','dataHoraVoto'])
w['t']=pd.to_datetime(w.dataHoraVoto); n=w.groupby('idVotacao').size(); w=w[w.idVotacao.isin(n[n>=300].index)]
w['wk']=w.t.dt.strftime('%G-%V')
vt=w.groupby('idVotacao').agg(t=('t','min'),wk=('wk','first'))
# presença: votação conta para o deputado se ele votou em alguma votação da mesma semana
act=w.groupby('wk').deputado_id.agg(set); votou=w.groupby('idVotacao').deputado_id.agg(set)
v=pd.read_csv(RAW+'votacoes-2026.csv',sep=';',encoding='utf-8-sig',dtype=str).set_index('id')
vp=pd.read_csv(RAW+'votacoesProposicoes-2026.csv',sep=';',encoding='utf-8-sig',dtype=str)
vp['pref']=vp.idVotacao.str.split('-').str[0]; vp['main']=vp.proposicao_id==vp.pref
vp=vp.sort_values('main',ascending=False).drop_duplicates('idVotacao').set_index('idVotacao')
def short(t):
    t=str(t or ''); t=re.split(r'\s*\(Art|, adotad|\. Sim|;|\. *$',t)[0]
    return t.replace('Projeto de Lei Complementar','PLP').replace('Projeto de Lei','PL').replace('Proposta de Emenda à Constituição','PEC').strip().rstrip('.')
cand=vt.join(v[['descricao']]).join(vp[['proposicao_titulo','proposicao_ementa','proposicao_id']])
cand=cand[cand.proposicao_titulo.notna()&~cand.descricao.str.contains('Requerimento',na=False)].sort_values('t',ascending=False)
rec=cand.head(10)
H=json.load(open('historico_data.json'))
H['rec']=[{'id':i,'d':r.t.strftime('%Y-%m-%d'),'tit':r.proposicao_titulo,'res':short(r.descricao),'em':(r.proposicao_ementa[:200]+('…' if len(r.proposicao_ementa)>200 else '')),'prop':r.proposicao_id} for i,r in rec.iterrows()]
vv=w.set_index(['idVotacao','deputado_id']).voto
tot=len(vt)
for i,d in H['deps'].items():
    code=''
    for vid,r in rec.iterrows():
        if (vid,i) in vv.index:
            x=vv.loc[(vid,i)]; x=x.iloc[0] if hasattr(x,'iloc') else x
            code+={'Sim':'S','Não':'N','Abstenção':'B','Obstrução':'B','Artigo 17':'P'}.get(x,'X')
        else: code+='A' if i in act[r.wk] else '-'
    d['rk']=code
    elig=[vid for vid,r in vt.iterrows() if i in act[r.wk]]
    pres=sum(1 for vid in elig if i in votou[vid])
    d['pres']=[pres,len(elig)]
H['rec_tot']=tot
json.dump(H,open('historico_data.json','w'),ensure_ascii=False,separators=(',',':'))
print(tot,'votações 2026'); print([ (x['d'],x['tit'],x['res']) for x in H['rec']])
print(H['deps']['209787']['rk'],H['deps']['209787']['pres'])
import statistics as st; r=[d['pres'][0]/d['pres'][1] for d in H['deps'].values() if d['pres'][1]>=20]; print('mediana presença',round(st.median(r),3),'min',round(min(r),3))
