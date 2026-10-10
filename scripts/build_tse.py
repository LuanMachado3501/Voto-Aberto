"""Candidatura 2026 + patrimônio declarado 2026 (TSE) por deputado em exercício. Não guarda CPF nem dados sensíveis."""
import pandas as pd, json, unicodedata, re
U='/root/.claude/uploads/4ca0478c-f08e-50ae-9016-3a44578f0aff/'
def N(s): s=unicodedata.normalize('NFD',str(s)).encode('ascii','ignore').decode().upper(); return re.sub(r'[^A-Z ]','',re.sub(r'\s+',' ',s)).strip()
cols=['NR_TURNO','SG_UF','DS_CARGO','SQ_CANDIDATO','NM_CANDIDATO','NM_URNA_CANDIDATO','DS_SITUACAO_CANDIDATURA','SG_PARTIDO','DS_GRAU_INSTRUCAO','DS_OCUPACAO','DS_SIT_TOT_TURNO','SG_UF_NASCIMENTO','DT_NASCIMENTO']
c=pd.read_csv(U+'96a6899e-consulta_cand_2026_BRASIL.csv',sep=';',encoding='latin1',dtype=str,usecols=cols)
c['NR_TURNO']=c.NR_TURNO.astype(int); c=c.sort_values('NR_TURNO').drop_duplicates('SQ_CANDIDATO',keep='last')
c['kc']=c.NM_CANDIDATO.map(N); c['ku']=c.NM_URNA_CANDIDATO.map(N)
b=pd.read_csv(U+'42c2a73a-bem_candidato_2026_BRASIL.csv',sep=';',encoding='latin1',dtype=str,usecols=['SQ_CANDIDATO','DS_TIPO_BEM_CANDIDATO','VR_BEM_CANDIDATO'])
b['v']=pd.to_numeric(b.VR_BEM_CANDIDATO.str.replace('.','',regex=False).str.replace(',','.',regex=False),errors='coerce').fillna(0)
tot=b.groupby('SQ_CANDIDATO').v.sum(); nb=b.groupby('SQ_CANDIDATO').size()
dep=pd.read_csv(U+'96b309c8-deputados.csv',sep=';',encoding='utf-8-sig',dtype=str); dep['id']=dep.uri.str.rsplit('/',n=1).str[-1]; dep=dep.set_index('id')
hem=json.load(open('hemiciclo_data.json')); H=json.load(open('historico_data.json'))
TIPO={'Apartamento':'Imóveis','Casa':'Imóveis','Terreno':'Imóveis','Sala ou conjunto':'Imóveis','Prédio comercial':'Imóveis','Prédio residencial':'Imóveis','Loja':'Imóveis','Galpão':'Imóveis','Construção':'Imóveis','Benfeitorias':'Imóveis','Imóvel rural':'Imóveis rurais','Terra nua':'Imóveis rurais'}
def cat(t):
    t=str(t)
    if t in TIPO: return TIPO[t]
    tl=t.lower()
    if 'terra nua' in tl or 'rural' in tl: return 'Imóveis rurais'
    if 'imóve' in tl or 'imove' in tl: return 'Imóveis'
    if 'veículo' in tl or 'embarca' in tl or 'aeronave' in tl: return 'Veículos'
    if 'quota' in tl or 'ações' in tl or 'participaç' in tl: return 'Empresas e participações'
    if any(w in tl for w in ['aplica','poupança','depósito','fundo','dinheiro','vgbl','pgbl','ouro','crédito','consórcio','cripto','numerário','renda fixa','previd']): return 'Dinheiro e aplicações'
    return 'Outros'
b['cat']=b.DS_TIPO_BEM_CANDIDATO.map(cat)
bycat=b.groupby(['SQ_CANDIDATO','cat']).v.sum()
miss=[]; ok=0
for d in hem['deps']:
    i=d['id']; nc=N(dep.loc[i,'nomeCivil']) if i in dep.index else ''
    m=c[c.kc==nc]
    if len(m)!=1: m=c[(c.ku==N(d['n']))&(c.SG_UF==d['uf'])] if len(m)==0 else m[m.SG_UF==d['uf']]
    if len(m)!=1: H['deps'][i]['tse']=None; miss.append(d['n']); continue
    r=m.iloc[0]; sq=r.SQ_CANDIDATO; ok+=1
    cats=[[k,round(v)] for k,v in bycat.loc[sq].sort_values(ascending=False).items() if v>0] if sq in tot.index else []
    H['deps'][i]['tse']={'sq':str(sq),'cargo':r.DS_CARGO.title(),'uf':r.SG_UF,'partido':r.SG_PARTIDO,'sit':r.DS_SIT_TOT_TURNO,'cand':r.DS_SITUACAO_CANDIDATURA,
       'ocup':r.DS_OCUPACAO.capitalize(),'esc':r.DS_GRAU_INSTRUCAO.capitalize(),'nasc':r.DT_NASCIMENTO,
       'bens':round(float(tot.get(sq,0))),'nbens':int(nb.get(sq,0)),'cats':cats}
json.dump(H,open('historico_data.json','w'),ensure_ascii=False,separators=(',',':'))
print('casados',ok,'sem candidatura/achado',len(miss)); print(miss[:40])
from collections import Counter
print(Counter((v['tse']['cargo'],v['tse']['sit']) for v in H['deps'].values() if v.get('tse')).most_common(20))
n={d['n']:d['id'] for d in hem['deps']}
for nm in ['Nikolas Ferreira','Erika Hilton','Tabata Amaral','Marcel van Hattem']: print(nm,H['deps'][n[nm]]['tse'])
