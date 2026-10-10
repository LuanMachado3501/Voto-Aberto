"""Gera historico_data.json: para cada deputado do hemiciclo, voto nas votações-chave,
primeiro voto na legislatura e fidelidade ao partido (2025-26)."""
import pandas as pd, json, glob
from datetime import timedelta
SCR='/tmp/claude-0/-home-claude/4ca0478c-f08e-50ae-9016-3a44578f0aff/scratchpad'
UP='/root/.claude/uploads/4ca0478c-f08e-50ae-9016-3a44578f0aff'
files=['/mnt/user-data/uploads/votacoesVotos-2023.csv','/mnt/user-data/uploads/votacoesVotos-2024.csv',
       '/mnt/user-data/uploads/votacoesVotos-2025__1_.csv',f'{UP}/d5d70b6b-votacoesVotos-2026.csv']
cols=['idVotacao','dataHoraVoto','voto','deputado_id','deputado_siglaPartido']
w=pd.concat([pd.read_csv(f,sep=';',encoding='utf-8-sig',dtype=str,usecols=cols) for f in files])
w['t']=pd.to_datetime(w.dataHoraVoto)
hem=json.load(open('/home/claude/voto_aberto/site/hemiciclo_data.json'))
ids=[d['id'] for d in hem['deps']]

# votações-chave (as dos posts)
KEY=[]
for f in sorted(glob.glob(f'{SCR}/capas/*.json')):
    k=f.split('/')[-1][:-5]; c=json.load(open(f)); d=json.load(open(f'{SCR}/data_{k}.json'))
    lb=c.get('labels',{})
    KEY.append(dict(id=d['id'],t=c['h1'],m=c['meta'],r=c['resultado'],
        sim=lb.get('sim_word','a favor'),nao=lb.get('nao_word','contra'),desc=c.get('desc',''),dep=c.get('depois','')))
KEY+= [dict(id='2233802-438',t='FIM DA ESCALA 6X1',m='PEC · Câmara dos Deputados · 2º turno · 27 mai 2026',r='APROVADA: 461 A 19',sim='a favor',nao='contra',desc='Reduz a jornada máxima de 44 para 40 horas semanais, em cinco dias de trabalho, sem redução de salário.',dep=''),
       dict(id='2383019-54',t='DE 513 PARA 531 DEPUTADOS',m='PLP 177/2023 · Câmara dos Deputados · 6 mai 2025',r='APROVADO: 270 A 207',sim='a favor',nao='contra',desc='Cria 18 vagas de deputado federal a partir de 2027. Com isso, nenhum estado perderia cadeiras na atualização pelo Censo de 2022.',dep='Depois, o Senado aprovou e Lula vetou. O veto ainda não foi votado, e a Câmara segue com 513.'),
       dict(id='2270800-160',t='PEC DA BLINDAGEM',m='PEC 3/2021 · Câmara dos Deputados · 16 set 2025',r='APROVADA: 344 A 133',sim='a favor',nao='contra',desc='Dificulta abrir processo criminal e prender deputados e senadores: o STF passaria a depender de autorização da própria Casa, em voto secreto.',dep='No 1º turno, foram 353 a 134. Depois, a CCJ do Senado rejeitou por unanimidade e a PEC foi arquivada.'),
       dict(id='2196833-373',t='REFORMA TRIBUTÁRIA',m='PEC 45/2019 · Câmara dos Deputados · 2º turno · 6 jul 2023',r='APROVADA: 375 A 113',sim='a favor',nao='contra',desc='Troca cinco impostos sobre consumo (PIS, Cofins, IPI, ICMS e ISS) por um imposto sobre valor agregado dividido entre União (CBS) e estados e municípios (IBS), com transição longa.',dep='Depois, o Senado mudou o texto, a Câmara concluiu a votação e a Emenda Constitucional 132 foi promulgada em dezembro de 2023.'),
       dict(id='2357053-47',t='ARCABOUÇO FISCAL',m='PLP 93/2023 · Câmara dos Deputados · 23 mai 2023',r='APROVADO: 372 A 108',sim='a favor',nao='contra',desc='Substitui o teto de gastos por uma regra em que a despesa pode crescer até 70% do aumento da receita, dentro de um limite, com metas de resultado das contas públicas.',dep='Depois, o Senado aprovou com mudanças, a Câmara concluiu em agosto e o texto virou a Lei Complementar 200/2023.'),
       dict(id='2355135-49',t='DECRETOS DO SANEAMENTO',m='PDL 98/2023 · Câmara dos Deputados · 3 mai 2023',r='APROVADO: 295 A 136',sim='derrubar',nao='manter',desc='Derruba trechos de decretos do governo Lula que mudavam regras do Marco do Saneamento de 2020 e davam mais espaço para empresas estatais prestarem o serviço.',dep='O projeto seguiu para o Senado.'),
       dict(id='2515648-44',t='AUMENTO DO IOF',m='PDL 214/2025 · Câmara dos Deputados · 25 jun 2025',r='APROVADO: 383 A 98',sim='derrubar',nao='manter',desc='Derruba o decreto do governo que aumentava o IOF, imposto cobrado em operações de crédito, câmbio e alguns investimentos.',dep='O Senado também aprovou no mesmo dia. Depois, o STF restabeleceu a maior parte do aumento numa decisão de conciliação.'),
       dict(id='257161-454',t='LICENCIAMENTO AMBIENTAL',m='PL 2159/2021 · Câmara dos Deputados · 17 jul 2025',r='APROVADO: 267 A 116',sim='a favor',nao='contra',desc='Cria uma nova lei geral de licenciamento ambiental, com licença por autodeclaração para empreendimentos de médio porte e dispensa para algumas atividades.',dep='Críticos chamaram o texto de “PL da devastação”. Lula sancionou a lei com vetos em agosto de 2025.')]
for k in KEY:
    s=w[w.idVotacao==k['id']]; assert len(s)>300, k
    k['d']=s.t.min().strftime('%Y-%m-%d'); k['prop']=k['id'].split('-')[0]
    t0=s.t.min(); win=w[(w.t>=t0-timedelta(days=7))&(w.t<=t0+timedelta(days=7))]
    k['_votou']=dict(zip(s.deputado_id,s.voto.fillna('?'))); k['_ativos']=set(win.deputado_id)
KEY.sort(key=lambda k:k['d'],reverse=True)
CODE={'Sim':'S','Não':'N','Abstenção':'B','Obstrução':'B','Artigo 17':'P','?':'X'}
def code(k,i):
    if i in k['_votou']: return CODE.get(k['_votou'][i],'X')
    return 'A' if i in k['_ativos'] else '-'

# fidelidade ao partido, 2025-26, votações com >=300 votantes
r=w[w.t>='2025-01-01']; n=r.groupby('idVotacao').size(); r=r[r.idVotacao.isin(n[n>=300].index)&r.voto.isin(['Sim','Não'])]
maj=r.groupby(['idVotacao','deputado_siglaPartido']).voto.agg(lambda s:s.value_counts().idxmax() if s.value_counts().iloc[0]>len(s)/2 else None).rename('maj')
r=r.join(maj,on=['idVotacao','deputado_siglaPartido']); r=r[r.maj.notna()]
# partidos de 1 deputado não contam
sz=r.groupby(['idVotacao','deputado_siglaPartido']).size().rename('sz'); r=r.join(sz,on=['idVotacao','deputado_siglaPartido']); r=r[r.sz>=3]
fid=(r.voto==r.maj).groupby(r.deputado_id).agg(['mean','size'])
first=w.groupby('deputado_id').t.min()

out={'key':[{k2:v for k2,v in k.items() if not k2.startswith('_')} for k in KEY],'deps':{}}
for i in ids:
    out['deps'][i]={'k':''.join(code(k,i) for k in KEY),
        'f':round(float(fid.loc[i,'mean'])*100) if i in fid.index and fid.loc[i,'size']>=30 else None,
        'p0':first[i].strftime('%Y-%m-%d') if i in first.index else None}
json.dump(out,open('/home/claude/voto_aberto/site/historico_data.json','w'),ensure_ascii=False,separators=(',',':'))
from collections import Counter
print(len(KEY), Counter(''.join(v['k'] for v in out['deps'].values())))
print(out['deps'][[d['id'] for d in hem['deps'] if d['n']=='Nikolas Ferreira'][0]])
print([ (k['t'],k['d']) for k in out['key']])
