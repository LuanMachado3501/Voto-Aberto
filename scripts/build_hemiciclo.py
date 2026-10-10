import pandas as pd, json
U='/root/.claude/uploads/4ca0478c-f08e-50ae-9016-3a44578f0aff/'
cur=json.load(open(U+'bc863235-deputados3.json'))['dados']
ip=pd.read_csv('/tmp/claude-0/-home-claude/4ca0478c-f08e-50ae-9016-3a44578f0aff/scratchpad/ideal_points.csv',dtype={'deputado_id':str}).set_index('deputado_id').pc1
w=pd.concat([pd.read_csv(f,sep=';',encoding='utf-8-sig',dtype=str,usecols=['idVotacao','voto','deputado_id']) for f in ['/mnt/user-data/uploads/votacoesVotos-2025__1_.csv',U+'d5d70b6b-votacoesVotos-2026.csv']])
n=w.groupby('idVotacao').size(); w=w[w.idVotacao.isin(n[n>=300].index)]
TOT=w.idVotacao.nunique(); vc=w[w.voto.isin(['Sim','Não'])].groupby('deputado_id').size()
LBL={"NOVO":"Novo","REDE":"Rede","MISSÃO":"Missão","REPUBLICANOS":"Republicanos","UNIÃO":"União","PODE":"Podemos","SOLIDARIEDADE":"Solidariedade","CIDADANIA":"Cidadania","AVANTE":"Avante"}
PRES='160674'
deps=[]
for d in cur:
    i=str(d['id'])
    if i==PRES: continue
    deps.append({'id':i,'n':d['nome'],'p':LBL.get(d['siglaPartido'],d['siglaPartido']),'uf':d['siglaUf'],
                 's':round(float(ip[i]),3) if i in ip.index else None,'v':int(vc.get(i,0))})
df=pd.DataFrame(deps); pm=df.dropna(subset=['s']).groupby('p').s.mean()
for d in deps:
    if d['s'] is None: d['s']=round(float(pm.get(d['p'],0)),3); d['e']=1
deps.sort(key=lambda d:d['s'])
json.dump({'total_votacoes':TOT,'deps':deps},open('hemiciclo_data.json','w'),ensure_ascii=False,separators=(',',':'))
print(TOT,len(deps),sum(1 for d in deps if d.get('e')),[ (d['n'],d['p'],d['v']) for d in deps if d.get('e')])
print([d for d in deps if d['n']=='Luiz Couto'])
