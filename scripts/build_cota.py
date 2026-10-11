"""Cota parlamentar (CEAP) 2025-26 por deputado."""
import pandas as pd, json
import os
RAW=os.environ.get('RAW','/home/claude/voto_aberto/raw')+'/'
w=pd.concat([pd.read_csv(RAW+f'Ano-{a}.csv',sep=';',encoding='utf-8-sig',dtype=str,usecols=['ideCadastro','txtDescricao','vlrLiquido','numAno','numMes','txtFornecedor']) for a in (2023,2024,2025,2026)],ignore_index=True)
w=w[w.ideCadastro.notna()&(w.ideCadastro!='')&~w.txtDescricao.str.contains('AUXÍLIO-MORADIA',na=False)]
w=w[(w.numAno+'-'+w.numMes.str.zfill(2))>='2023-02']
w['v']=pd.to_numeric(w.vlrLiquido.str.replace(',','.'),errors='coerce').fillna(0)
CAT={'DIVULGAÇÃO':'Divulgação do mandato','VEÍCULOS AUTOMOTORES':'Aluguel de carros','ESCRITÓRIO':'Escritório no estado','COMBUSTÍVEIS':'Combustível',
     'PASSAGEM AÉREA':'Passagens aéreas','HOSPEDAGEM':'Hospedagem','TELEFONIA':'Telefone','AERONAVES':'Fretamento de aviões','SEGURANÇA':'Segurança privada',
     'ALIMENTAÇÃO':'Alimentação','TÁXI':'Táxi, pedágio e estacionamento','EMBARCAÇÕES':'Aluguel de barcos','TERRESTRES':'Passagens de ônibus e barco'}
def cat(s):
    for k,v in CAT.items():
        if k in s: return v
    return 'Outros'
w['cat']=w.txtDescricao.map(cat)
hem=json.load(open('hemiciclo_data.json')); H=json.load(open('historico_data.json'))
uf={d['id']:d['uf'] for d in hem['deps']}
y25=w[w.numAno=='2025'].groupby('ideCadastro').v.sum()
mx26=int(w[w.numAno=='2026'].numMes.astype(int).max())
y26=w[w.numAno=='2026'].groupby('ideCadastro').v.sum()
# ranking dentro do estado (2025), só deputados atuais
r=pd.DataFrame({'v':y25}).reset_index(); r=r[r.ideCadastro.isin(uf)]; r['uf']=r.ideCadastro.map(uf)
r['pos']=r.groupby('uf').v.rank(ascending=False,method='min').astype(int); r['n']=r.groupby('uf').v.transform('size')
pos=r.set_index('ideCadastro')
cats=w.groupby(['ideCadastro','cat']).v.sum(); forn=w.groupby(['ideCadastro','txtFornecedor']).v.sum()
SMALL={'DE','DA','DO','DAS','DOS','E'}
def tc(s): return ' '.join(x.lower() if x.upper() in SMALL and i else (x if x in ('LTDA','S/A','SA','ME','EIRELI','EPP') else x.capitalize()) for i,x in enumerate(str(s).split()))
n=0
for i,d in H['deps'].items():
    if i not in y25.index and i not in y26.index: d['cota']=None; continue
    c=cats.loc[i].sort_values(ascending=False); f=forn.loc[i].sort_values(ascending=False)
    yr={a:round(float(v)) for a,v in w[w.ideCadastro==i].groupby('numAno').v.sum().items()}
    d['cota']={'anos':yr,'y25':round(float(y25.get(i,0))),'y26':round(float(y26.get(i,0))),'m26':mx26,
      'pos':int(pos.loc[i,'pos']) if i in pos.index else None,'n':int(pos.loc[i,'n']) if i in pos.index else None,
      'cats':[[k,round(v)] for k,v in c.items() if v>0][:6],'forn':[[tc(k),round(v)] for k,v in f.items() if v>0][:5]}
    n+=1
json.dump(H,open('historico_data.json','w'),ensure_ascii=False,separators=(',',':'))
print('com cota',n,'meses 2026:',mx26); import statistics as st
print('mediana 2025',st.median([v['cota']['y25'] for v in H['deps'].values() if v.get('cota') and v['cota']['y25']]))
print(H['deps']['209787']['cota'])
