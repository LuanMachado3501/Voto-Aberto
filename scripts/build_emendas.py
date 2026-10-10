import pandas as pd, json, unicodedata, re
def N(s):
    s=unicodedata.normalize('NFD',str(s)).encode('ascii','ignore').decode().upper()
    s=re.sub(r'\(.*','',s); s=s.replace('.',' ')
    s=re.sub(r'\bPROF\b','PROFESSOR',s); s=re.sub(r'\bPROFA\b','PROFESSORA',s); s=re.sub(r'\bDEL\b','DELEGADO',s)
    s=re.sub(r'\bCEL\b','CORONEL',s); s=re.sub(r'\bSGT\b','SARGENTO',s); s=re.sub(r'\bCAP\b','CAPITAO',s); s=re.sub(r'\bPR\b','PASTOR',s)
    return re.sub(r'[^A-Z ]','',re.sub(r'\s+',' ',s)).strip()
num=lambda c:pd.to_numeric(c.str.replace('.','',regex=False).str.replace(',','.',regex=False),errors='coerce').fillna(0)
e=pd.read_csv('/mnt/user-data/uploads/EmendasParlamentares.csv',sep=';',encoding='latin1',dtype=str)
e=e[e['Ano da Emenda'].astype(int).between(2023,2026)&e['Tipo de Emenda'].str.contains('Individual')].copy()
e['pago']=num(e['Valor Pago'])+num(e['Valor Restos A Pagar Pagos']); e['emp']=num(e['Valor Empenhado'])
e['k']=e['Nome do Autor da Emenda'].map(N)
hem=json.load(open('hemiciclo_data.json'))
ALIAS={'220660':'YURY DO PAREDAO'}
H=json.load(open('historico_data.json'))
keys=set(e.k)
miss=[]
for d in hem['deps']:
    k=ALIAS.get(d['id']) or N(d['n'])
    if k not in keys:
        # tenta sem título (Dr, Pastor...)
        k2=re.sub(r'^(DR|DRA|PASTOR|DELEGADO|DELEGADA|CORONEL|GENERAL|SARGENTO|CAPITAO|PROFESSOR|PROFESSORA|SUBTENENTE|CABO|MAJOR) ','',k)
        cand=[x for x in keys if x==k2 or x.endswith(' '+k2)]
        k=cand[0] if len(cand)==1 else None
    if not k: miss.append(d['n']); H['deps'][d['id']]['em']=None; continue
    s=e[e.k==k]
    fn=s.groupby('Nome Função').pago.sum().sort_values(ascending=False)
    loc=s.groupby('Localidade de aplicação do recurso').pago.sum().sort_values(ascending=False)
    H['deps'][d['id']]['em']={'pago':round(s.pago.sum()),'emp':round(s.emp.sum()),
      'ano':{a:round(v) for a,v in s.groupby('Ano da Emenda').pago.sum().items()},
      'area':[[a,round(v)] for a,v in fn.head(3).items() if v>0],
      'loc':[[a,round(v)] for a,v in loc.head(3).items() if v>0]}
json.dump(H,open('historico_data.json','w'),ensure_ascii=False,separators=(',',':'))
print(len(miss),miss)
v=[x['em']['pago'] for x in H['deps'].values() if x.get('em')]; import statistics as st
print('mediana',st.median(v),'max',max(v),'min',min(v))
n={d['n']:d['id'] for d in hem['deps']}
for nm in ['Nikolas Ferreira','Erika Hilton','Tabata Amaral']: print(nm,H['deps'][n[nm]]['em'])
