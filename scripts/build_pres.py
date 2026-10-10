import re
import pandas as pd, json
U='/root/.claude/uploads/4ca0478c-f08e-50ae-9016-3a44578f0aff/'
w=pd.concat([pd.read_csv(f,sep=';',encoding='utf-8-sig',dtype=str,usecols=['idVotacao','dataHoraVoto','voto','deputado_id']) for f in ['/mnt/user-data/uploads/votacoesVotos-2025__1_.csv',U+'d5d70b6b-votacoesVotos-2026.csv']])
w['t']=pd.to_datetime(w.dataHoraVoto)
pres=w[(w.deputado_id=='160674')&(w.voto=='Artigo 17')].groupby('idVotacao').t.min().reset_index()
vp=pd.read_csv(U+'7e8aeb3a-votacoesProposicoes-2026.csv',sep=';',encoding='utf-8-sig',dtype=str)
v=pd.read_csv(U+'62571816-votacoes-2026.csv',sep=';',encoding='utf-8-sig',dtype=str)
vp['pref']=vp.idVotacao.str.split('-').str[0]; vp['main']=(vp.proposicao_id==vp.pref)
vp=vp.sort_values('main',ascending=False).drop_duplicates('idVotacao')
x=pres.merge(vp[['idVotacao','proposicao_id','proposicao_titulo','proposicao_ementa']],on='idVotacao',how='left').merge(v[['id','descricao']],left_on='idVotacao',right_on='id',how='left')
x=x[x.proposicao_titulo.notna()].sort_values('t',ascending=False)
g=x.groupby('proposicao_titulo',sort=False).agg(prop=('proposicao_id','first'),d=('t','max'),n=('idVotacao','size'),em=('proposicao_ementa','first'),res=('descricao','first')).head(8).reset_index()
def short(t):
    t=str(t or ''); t=re.split(r'\s*\(Art|, adotad|\. Sim|;',t)[0]
    t=t.replace('Projeto de Lei Complementar','PLP').replace('Projeto de Lei','PL')
    return t.strip().rstrip('.')
P=json.load(open('presidente_data.json'))
P['pautas']=[{'tit':r.proposicao_titulo,'prop':r.prop,'d':r.d.strftime('%Y-%m-%d'),'n':int(r.n),'em':r.em[:180]+('…' if len(r.em)>180 else ''),'res':short(r.res)} for r in g.itertuples()]
json.dump(P,open('presidente_data.json','w'),ensure_ascii=False)
for p in P['pautas']: print(p)
