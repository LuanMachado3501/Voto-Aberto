"""Página Cota: média mensal de cada deputado em exercício vs. mediana da bancada do estado."""
import pandas as pd, json, statistics as st
w=pd.concat([pd.read_csv(f'/mnt/user-data/uploads/Ano-{a}.csv',sep=';',encoding='utf-8-sig',dtype=str,
   usecols=['ideCadastro','txtDescricao','vlrLiquido','numAno','numMes','txtFornecedor','txtCNPJCPF']) for a in (2023,2024,2025,2026)])
w=w[w.ideCadastro.notna()&(w.ideCadastro!='')&~w.txtDescricao.str.contains('AUXÍLIO-MORADIA',na=False)]
w['v']=pd.to_numeric(w.vlrLiquido.str.replace(',','.'),errors='coerce').fillna(0)
w['ym']=w.numAno+'-'+w.numMes.str.zfill(2)
w=w[w.ym>='2023-02']  # legislatura 57 começou em 1º/fev/2023
hem=json.load(open('hemiciclo_data.json')); pres=json.load(open('presidente_data.json'))
uf={d['id']:d['uf'] for d in hem['deps']}; uf[str(pres['id'])]=pres.get('uf','PB')
CAT={'DIVULGAÇÃO':'Divulgação do mandato','VEÍCULOS AUTOMOTORES':'Aluguel de carros','ESCRITÓRIO':'Escritório no estado','COMBUSTÍVEIS':'Combustível',
     'PASSAGEM AÉREA':'Passagens aéreas','HOSPEDAGEM':'Hospedagem','TELEFONIA':'Telefone','AERONAVES':'Fretamento de aviões','SEGURANÇA':'Segurança privada',
     'ALIMENTAÇÃO':'Alimentação','TÁXI':'Táxi, pedágio e estacionamento','EMBARCAÇÕES':'Aluguel de barcos','TERRESTRES':'Passagens de ônibus e barco',
     'CONSULTORIAS':'Consultorias e pesquisas','CURSO':'Cursos e eventos','POSTAIS':'Correios','ASSINATURA':'Assinaturas'}
def cat(s):
    for k,v in CAT.items():
        if k in s: return v
    return 'Outros'
w['cat']=w.txtDescricao.map(cat)
w=w[w.ideCadastro.isin(uf)]
# fornecedor pelo CNPJ/CPF (nomes variam); nome mais frequente
w['fk']=w.txtCNPJCPF.fillna('').str.replace(r'\D','',regex=True); w.loc[w.fk=='','fk']=w.txtFornecedor
nome=w.groupby('fk').txtFornecedor.agg(lambda s:s.mode().iat[0])
SMALL={'DE','DA','DO','DAS','DOS','E'}
def tc(s): return ' '.join(x.lower() if x.upper() in SMALL and i else (x if x in ('LTDA','S/A','SA','ME','EIRELI','EPP') else x.capitalize()) for i,x in enumerate(str(s).split()))
rows=[]
for i,g in w.groupby('ideCadastro'):
    tot=g.v.sum(); m=g.ym.nunique()
    if tot<=0: continue
    c=g.groupby('cat').v.sum().sort_values(ascending=False)
    f=g.groupby('fk').v.sum().sort_values(ascending=False)
    rows.append(dict(id=i,uf=uf[i],tot=tot,m=m,men=tot/m,cat=c.index[0],catp=c.iat[0]/tot,cats=[[k,round(v/m)] for k,v in c.items()][:4],
                     forn=tc(nome[f.index[0]]),fornp=f.iat[0]/tot))
df=pd.DataFrame(rows)
ok=df[df.m>=3]
med=ok.groupby('uf').men.median()
# mediana por categoria/estado (R$/mês), para comparar na página
cm={}
for (u,k),s in w[w.ideCadastro.isin(ok.id)].groupby(['ideCadastro','cat']).v.sum().rename('v').reset_index().assign(uf=lambda x:x.ideCadastro.map(uf)).groupby(['uf','cat']):
    pass
pc=w[w.ideCadastro.isin(ok.id)].groupby(['ideCadastro','cat']).v.sum().unstack(fill_value=0)
pc=pc.div(ok.set_index('id').m,axis=0); pc['uf']=pc.index.map(uf)
catmed={u:{k:round(v) for k,v in g.drop(columns='uf').median().items()} for u,g in pc.groupby('uf')}
df['r']=df.apply(lambda x:x.men/med[x.uf] if x.m>=3 and x.uf in med else None,axis=1)
df['pos']=df.groupby('uf').men.rank(ascending=False,method='min').astype(int); df['n']=df.groupby('uf').men.transform('size')
yms=sorted(w.ym.unique())
out={'de':yms[0],'ate':yms[-1],'med':{k:round(v) for k,v in med.items()},
  'deps':[[x.id,round(x.men),None if pd.isna(x.r) else round(x.r,3),int(x.m),round(x.tot),x.forn,round(x.fornp,3),int(x.pos),int(x.n)] for x in df.itertuples()]}
json.dump(out,open('cota_data.json','w'),ensure_ascii=False,separators=(',',':'))
print(len(out['deps']),'deps',yms[0],yms[-1],'sem razão:',df.r.isna().sum())
print(df.sort_values('r',ascending=False)[['id','uf','men','r','fornp','forn']].head(8).to_string())
print(med.sort_values().to_string())
print('fornp>=.4:',(df.fornp>=.4).sum(), ' r>=1.5:',(df.r>=1.5).sum(), ' r<=.5:',(df.r<=.5).sum())
