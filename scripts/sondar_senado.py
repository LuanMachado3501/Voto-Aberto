"""Sonda os dados abertos do Senado e guarda as respostas cruas em raw_senado/ para inspeção."""
import os, urllib.request, json
os.makedirs('raw_senado', exist_ok=True)
URLS = {
 'lista_atual': 'https://legis.senado.leg.br/dadosabertos/senador/lista/atual.json',
 'votacao_v2_out': 'https://legis.senado.leg.br/dadosabertos/votacao?dataInicio=2026-10-01&dataFim=2026-10-31',
 'votacao_v2_ano': 'https://legis.senado.leg.br/dadosabertos/votacao?ano=2026',
 'nominal_2026': 'https://legis.senado.leg.br/dadosabertos/plenario/votacao/nominal/2026.json',
 'lista_votacao': 'https://legis.senado.leg.br/dadosabertos/plenario/lista/votacao/20261001/20261031.json',
}
for k, u in URLS.items():
    try:
        req = urllib.request.Request(u, headers={'Accept': 'application/json', 'User-Agent': 'centropolitico.com.br'})
        with urllib.request.urlopen(req, timeout=90) as r:
            b = r.read()
        open(f'raw_senado/{k}.json', 'wb').write(b)
        print('ok', k, len(b), b[:200])
    except Exception as e:
        print('ERRO', k, e)
