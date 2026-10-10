import pandas as pd, json, re
from build_emendas_norm import N
num=lambda c:pd.to_numeric(c.str.replace('.','',regex=False).str.replace(',','.',regex=False),errors='coerce').fillna(0)
it=pd.read_csv('/mnt/user-data/uploads/EmendasParlamentares_PorFavorecido.csv',sep=';',encoding='latin1',dtype=str,chunksize=500000,
   usecols=['Código da Emenda','Nome do Autor da Emenda','Tipo de Emenda','Ano/Mês','Favorecido','Município Favorecido','UF Favorecido','Valor Recebido'])
parts=[]
for c in it:
    c=c[c['Tipo de Emenda'].str.contains('Individual',na=False)&(c['Ano/Mês'].str[:4].astype(int)>=2023)]
    parts.append(c)
f=pd.concat(parts)
em_area=pd.read_csv('/mnt/user-data/uploads/EmendasParlamentares.csv',sep=';',encoding='latin1',dtype=str,usecols=['Código da Emenda','Nome Função']).drop_duplicates('Código da Emenda')
f=f.merge(em_area,on='Código da Emenda',how='left'); f['Nome Função']=f['Nome Função'].fillna('Sem informação'); f['v']=num(f['Valor Recebido']); f['k']=f['Nome do Autor da Emenda'].map(N)
hem=json.load(open('hemiciclo_data.json'))
ALIAS={'220660':'YURY DO PAREDAO'}
H=json.load(open('historico_data.json'))
keys=set(f.k)
SMALL={'DE','DA','DO','DAS','DOS','E'}
def tc(s):
    s=str(s); return ' '.join(w.lower() if w in SMALL and i else (w if len(w)<=3 and w.isupper() and w not in SMALL and i else w.capitalize()) for i,w in enumerate(s.split()))
ok=0
for d in hem['deps']:
    em=H['deps'][d['id']].get('em')
    if not em: continue
    k=ALIAS.get(d['id']) or N(d['n'])
    if k not in keys:
        k2=re.sub(r'^(DR|DRA|PASTOR|DELEGADO|DELEGADA|CORONEL|GENERAL|SARGENTO|CAPITAO|PROFESSOR|PROFESSORA|SUBTENENTE|CABO|MAJOR) ','',k)
        c=[x for x in keys if x==k2 or x.endswith(' '+k2)]; k=c[0] if len(c)==1 else None
    if not k: continue
    s=f[f.k==k]; g=s.groupby(['Favorecido','Município Favorecido','UF Favorecido']).v.sum().sort_values(ascending=False)
    ar=s.groupby(['Favorecido','Município Favorecido','UF Favorecido','Nome Função']).v.sum()
    em['fav']=[[tc(a),tc(m)+'-'+u,round(v),[[fn,round(x)] for fn,x in ar.loc[(a,m,u)].sort_values(ascending=False).items() if x>0][:3]] for (a,m,u),v in g.head(5).items() if v>0]
    em['nfav']=int(s.Favorecido.nunique()); em['nmun']=int(s['Município Favorecido'].nunique()); ok+=1
json.dump(H,open('historico_data.json','w'),ensure_ascii=False,separators=(',',':'))
print('ok',ok); n={d['n']:d['id'] for d in hem['deps']}; print(H['deps'][n['Nikolas Ferreira']]['em']['fav'], H['deps'][n['Nikolas Ferreira']]['em']['nmun'])
