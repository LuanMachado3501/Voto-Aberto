import pandas as pd, json
d=pd.read_csv('/root/.claude/uploads/4ca0478c-f08e-50ae-9016-3a44578f0aff/96b309c8-deputados.csv',sep=';',encoding='utf-8-sig',dtype=str)
d['id']=d.uri.str.rsplit('/',n=1).str[-1]; d=d.set_index('id')
H=json.load(open('historico_data.json')); hem=json.load(open('hemiciclo_data.json')); miss=[]
for x in hem['deps']:
    i=x['id']
    if i not in d.index: miss.append(x['n']); continue
    r=d.loc[i]; L=int(r.idLegislaturaInicial); H['deps'][i]['l0']=L; H['deps'][i]['y0']=2023-4*(57-L)
    mun,uf=r.municipioNascimento,r.ufNascimento
    H['deps'][i]['nasc']=f"{mun}-{uf}" if isinstance(mun,str) and isinstance(uf,str) else None
json.dump(H,open('historico_data.json','w'),ensure_ascii=False,separators=(',',':')); print('sem tenure',miss)
