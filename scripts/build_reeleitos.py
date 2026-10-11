"""Lista os deputados reeleitos em 2026 (TSE) para a Tribuna aceitar perguntas só para eles."""
import json, sys, os
H = json.load(open(os.path.join(os.path.dirname(__file__), '..', 'data', 'historico_data.json')))
hem = {d['id']: d for d in json.load(open(os.path.join(os.path.dirname(__file__), '..', 'data', 'hemiciclo_data.json')))['deps']}
ids = sorted(i for i, d in H['deps'].items()
             if d.get('tse') and d['tse'].get('cargo') == 'Deputado Federal' and str(d['tse'].get('sit', '')).startswith('ELEITO'))
# id -> "Nome (PARTIDO-UF)", para a moderação mostrar o nome em vez do número
out = {i: (f"{hem[i]['n']} ({hem[i]['p']}-{hem[i]['uf']})" if i in hem else i) for i in ids}
json.dump(out, sys.stdout, ensure_ascii=False)
print(len(out), 'reeleitos', file=sys.stderr)
