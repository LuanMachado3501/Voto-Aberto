"""Lista oficial de temas da Câmara (codTema) e quantas proposições de 2023-2026
caíram em cada um. Base do "Fiel à pauta": o deputado escolhe prioridades desta
mesma lista, e depois comparamos com a atuação dele nesses temas."""
import json, re, urllib.request, urllib.parse
API = 'https://dadosabertos.camara.leg.br/api/v2'

def get(url):
    req = urllib.request.Request(url, headers={'Accept': 'application/json', 'User-Agent': 'centropolitico.com.br'})
    with urllib.request.urlopen(req, timeout=90) as r:
        return json.load(r)

def total(params):
    q = urllib.parse.urlencode(dict(params, itens=100, pagina=1))
    d = get(f'{API}/proposicoes?{q}')
    last = next((l['href'] for l in d.get('links', []) if l['rel'] == 'last'), None)
    if not last:
        return len(d['dados'])
    n = int(re.search(r'pagina=(\d+)', last).group(1))
    if n == 1:
        return len(d['dados'])
    q = urllib.parse.urlencode(dict(params, itens=100, pagina=n))
    return (n - 1) * 100 + len(get(f'{API}/proposicoes?{q}')['dados'])

temas = get(f'{API}/referencias/proposicoes/codTema')['dados']
out = []
for t in temas:
    base = {'codTema': t['cod'], 'dataApresentacaoInicio': '2023-02-01', 'dataApresentacaoFim': '2026-10-27'}
    try:
        n_all = total(dict(base, siglaTipo='PL'))
        n_pec = total(dict(base, siglaTipo='PEC'))
    except Exception as e:
        n_all = n_pec = None
    out.append({'cod': t['cod'], 'nome': t['nome'], 'pl_2023_2026': n_all, 'pec_2023_2026': n_pec})
    print(t['cod'], t['nome'], n_all, n_pec, flush=True)
json.dump({'fonte': 'Câmara dos Deputados, dados abertos', 'temas': out},
          open('data/temas_camara.json', 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
