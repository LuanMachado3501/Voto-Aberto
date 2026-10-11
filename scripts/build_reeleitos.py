"""Lista os deputados reeleitos em 2026 (TSE) para a Tribuna aceitar perguntas só para eles."""
import json, sys, os
H = json.load(open(os.path.join(os.path.dirname(__file__), '..', 'data', 'historico_data.json')))
ids = sorted(i for i, d in H['deps'].items()
             if d.get('tse') and d['tse'].get('cargo') == 'Deputado Federal' and str(d['tse'].get('sit', '')).startswith('ELEITO'))
json.dump(ids, sys.stdout)
print(len(ids), 'reeleitos', file=sys.stderr)
