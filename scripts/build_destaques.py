"""Índice de destaque das votações recentes do plenário.

Índice (0 a 100) = 70% atenção pública + 30% disputa no plenário.
- Atenção pública: quantas notícias citam a proposta (Google Notícias, 7 dias
  antes até 21 dias depois da votação), em escala logarítmica.
- Disputa: placar apertado (50%), governo e oposição orientando em lados
  opostos (30%) e quantidade de votações nominais sobre a mesma proposta (20%).
Gera data/destaques.json e, no GitHub Actions, um resumo na página da rodada.
"""
import os, re, json, math, time, datetime as dt, urllib.parse, urllib.request
import xml.etree.ElementTree as ET
import pandas as pd

RAW = os.environ.get('RAW', '/home/claude/voto_aberto/raw') + '/'
PESO_ATENCAO, PESO_DISPUTA = 0.7, 0.3
JANELA_DIAS, MIN_ITENS, TOP = 45, 6, 10

# apelidos editáveis no GitHub (data/apelidos.txt)
APELIDOS = {}
if os.path.exists('apelidos.txt'):
    for ln in open('apelidos.txt', encoding='utf-8'):
        ln = ln.strip()
        if ln and not ln.startswith('#') and '=' in ln:
            k, v = ln.split('=', 1)
            APELIDOS[re.sub(r'\s+', ' ', k.strip().upper())] = [a.strip() for a in v.split(';') if a.strip()]

v = pd.read_csv(RAW + 'votacoes-2026.csv', sep=';', encoding='utf-8-sig', dtype=str)
v = v[v.siglaOrgao == 'PLEN'].copy()
for c in ('votosSim', 'votosNao'):
    v[c] = pd.to_numeric(v[c], errors='coerce').fillna(0).astype(int)
v = v[(v.votosSim + v.votosNao) >= 300]          # só votações nominais com quórum
v['t'] = pd.to_datetime(v.dataHoraRegistro)

vp = pd.read_csv(RAW + 'votacoesProposicoes-2026.csv', sep=';', encoding='utf-8-sig', dtype=str)
vp['pref'] = vp.idVotacao.str.split('-').str[0]
vp['main'] = vp.proposicao_id == vp.pref
vp = vp.sort_values('main', ascending=False).drop_duplicates('idVotacao')
x = v.merge(vp[['idVotacao', 'proposicao_id', 'proposicao_titulo', 'proposicao_ementa', 'proposicao_siglaTipo']],
            left_on='id', right_on='idVotacao', how='inner')
x = x[~x.proposicao_siglaTipo.isin(['REQ', 'RIC'])]   # requerimentos não entram

o = pd.read_csv(RAW + 'votacoesOrientacoes-2026.csv', sep=';', encoding='utf-8-sig', dtype=str)
o = o[o.orientacao.isin(['Sim', 'Não'])]
gov = o[o.siglaBancada == 'Governo'].set_index('idVotacao').orientacao
opo = o[o.siglaBancada == 'Oposição'].set_index('idVotacao').orientacao
gov = gov[~gov.index.duplicated()]; opo = opo[~opo.index.duplicated()]

fim = x.t.max()
props = []
for pid, g in x.groupby('proposicao_id'):
    principal = g.loc[(g.votosSim + g.votosNao).idxmax()]
    s, n = int(principal.votosSim), int(principal.votosNao)
    dividido = any(i in gov.index and i in opo.index and gov[i] != opo[i] for i in g.id)
    props.append(dict(id=pid, vid=principal.id, titulo=principal.proposicao_titulo, ementa=principal.proposicao_ementa,
                      data=g.t.max(), placar=[s, n], votacoes=len(g), dividido=dividido,
                      aprovada=principal.aprovacao == '1'))
props.sort(key=lambda p: p['data'], reverse=True)
recentes = [p for p in props if p['data'] >= fim - pd.Timedelta(days=JANELA_DIAS)]
if len(recentes) < MIN_ITENS:
    recentes = props[:max(MIN_ITENS, 12)]

UA = {'User-Agent': 'Mozilla/5.0 (compatible; CentroPoliticoBot/1.0; +https://centropolitico.com.br)'}
def noticias(titulo, data):
    """Conta matérias no Google Notícias que citam o número da proposta perto da votação."""
    m = re.match(r'(\w+)\s+(\d+)/(\d{4})', titulo or '')
    if not m:
        return None
    tipo, num, ano = m.groups()
    termos = [f'{tipo} {num}/{ano}', f'{tipo} {num}/{ano[2:]}'] + APELIDOS.get(f'{tipo} {num}/{ano}'.upper(), [])
    q = ' OR '.join(f'"{x}"' for x in termos)
    url = 'https://news.google.com/rss/search?' + urllib.parse.urlencode(
        {'q': q, 'hl': 'pt-BR', 'gl': 'BR', 'ceid': 'BR:pt-419'})
    try:
        with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=30) as r:
            root = ET.fromstring(r.read())
    except Exception as e:
        print('  notícias indisponíveis para', titulo, '-', e)
        return None
    ini, fimj = data - pd.Timedelta(days=7), data + pd.Timedelta(days=21)
    c = 0
    for it in root.iter('item'):
        try:
            pub = pd.Timestamp(dt.datetime.strptime(it.findtext('pubDate')[:25], '%a, %d %b %Y %H:%M:%S'))
        except Exception:
            continue
        if ini <= pub <= fimj:
            c += 1
    time.sleep(1.5)
    return c

for p in recentes:
    p['noticias'] = noticias(p['titulo'], p['data'])
    tot = sum(p['placar'])
    aperto = 1 - abs(p['placar'][0] - p['placar'][1]) / tot if tot else 0
    p['disputa'] = round(0.5 * aperto + 0.3 * p['dividido'] + 0.2 * min(p['votacoes'] / 5, 1), 3)

conta = [p['noticias'] for p in recentes if p['noticias'] is not None]
teto = max(conta + [10])
for p in recentes:
    p['atencao'] = None if p['noticias'] is None else round(math.log1p(p['noticias']) / math.log1p(teto), 3)
    a = p['atencao'] if p['atencao'] is not None else 0
    p['indice'] = round(100 * (PESO_ATENCAO * a + PESO_DISPUTA * p['disputa']))
recentes.sort(key=lambda p: p['indice'], reverse=True)

vall = pd.read_csv(RAW + 'votacoesVotos-2026.csv', sep=';', encoding='utf-8-sig', dtype=str,
                   usecols=['idVotacao', 'voto', 'deputado_siglaPartido', 'deputado_nome', 'deputado_siglaUf'])
vall = vall[vall.idVotacao.isin([p['vid'] for p in recentes[:TOP]])]
vv = vall[vall.voto.isin(['Sim', 'Não'])]
ED = json.load(open('editorial.json', encoding='utf-8')) if os.path.exists('editorial.json') else {'destaques': {}}
def nomes(vid):
    g = vall[vall.idVotacao == vid].set_index('deputado_nome')
    return {lado: [[n, (f"{g.loc[n, 'deputado_siglaPartido']}-{g.loc[n, 'deputado_siglaUf']}" if n in g.index else ''),
                    (g.loc[n, 'voto'] if n in g.index else 'não votou')] for n in L]
            for lado, L in ED.get('destaques', {}).items()}
por = vv.groupby(['idVotacao', 'deputado_siglaPartido']).voto.value_counts().unstack(fill_value=0)
def partidos(vid):
    if vid not in por.index.get_level_values(0):
        return []
    g = por.loc[vid]
    g = g.assign(t=g.sum(axis=1)).sort_values('t', ascending=False)
    return [[pt, int(r.get('Sim', 0)), int(r.get('Não', 0))] for pt, r in g.iterrows()]

out = {'gerado': dt.date.today().isoformat(), 'pesos': {'atencao': PESO_ATENCAO, 'disputa': PESO_DISPUTA},
       'noticias_ok': bool(conta), 'itens': []}
for p in recentes[:TOP]:
    out['itens'].append({**{k: p[k] for k in ('id', 'titulo', 'ementa', 'placar', 'votacoes', 'dividido',
                                            'aprovada', 'noticias', 'atencao', 'disputa', 'indice')},
                         'data': p['data'].strftime('%Y-%m-%d'),
                         'nome': (APELIDOS.get((p['titulo'] or '').upper()) or [None])[0],
                         'partidos': partidos(p['vid']),
                         'nomes': nomes(p['vid'])})
json.dump(out, open('destaques.json', 'w'), ensure_ascii=False, indent=1)

linhas = ['## Pauta da semana: votações com mais destaque', '',
          f'Índice = {int(PESO_ATENCAO*100)}% atenção pública + {int(PESO_DISPUTA*100)}% disputa no plenário.'
          + ('' if conta else ' **Atenção: o Google Notícias não respondeu; o índice usou só a disputa.**'), '',
          '| # | Proposta | Data | Placar | Notícias | Gov × Oposição | Índice |', '|---|---|---|---|---|---|---|']
for i, p in enumerate(out['itens'], 1):
    em = (p['ementa'] or '')[:90] + ('…' if len(p['ementa'] or '') > 90 else '')
    linhas.append(f"| {i} | **[{p['titulo']}](https://www.camara.leg.br/propostas-legislativas/{p['id']})** {em} | "
                  f"{p['data'][8:]}/{p['data'][5:7]} | {p['placar'][0]} × {p['placar'][1]} | "
                  f"{'—' if p['noticias'] is None else p['noticias']} | {'opostos' if p['dividido'] else '—'} | **{p['indice']}** |")
resumo = '\n'.join(linhas) + '\n'
print(resumo)
if os.environ.get('GITHUB_STEP_SUMMARY'):
    open(os.environ['GITHUB_STEP_SUMMARY'], 'a').write(resumo)
