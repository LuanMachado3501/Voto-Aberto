"""Gera dois arquivos que os agentes agendados leem pelo GitHub
(o ambiente deles não alcança a Câmara nem o Worker da Tribuna):

- data/deputados_contato.json: deputados em exercício com e-mail oficial,
  partido, UF e sexo (para "Deputado"/"Deputada" nos e-mails).
- data/tribuna_fila.json: perguntas da Tribuna aprovadas e ainda não
  enviadas, agrupadas por deputado, já com nome e e-mail.

Só usa dados públicos: o e-mail institucional do deputado e o texto das
perguntas que já aparecem no site. Nada de quem perguntou.
"""
import json, os, sys, urllib.request
from datetime import datetime, timezone, timedelta

CAMARA = 'https://dadosabertos.camara.leg.br/api/v2/deputados?itens=1000&ordem=ASC&ordenarPor=nome'
TRIBUNA = os.environ.get('TRIBUNA_API', 'https://tribuna.votoabertobr.workers.dev') + '/perguntas'


def get(url):
    req = urllib.request.Request(url, headers={'Accept': 'application/json', 'User-Agent': 'centropolitico.com.br'})
    with urllib.request.urlopen(req, timeout=60) as r:
        return json.load(r)


def deputados():
    out = {}
    for sexo in ('F', 'M'):
        for d in get(CAMARA + '&siglaSexo=' + sexo)['dados']:
            out[str(d['id'])] = {'nome': d['nome'], 'partido': d['siglaPartido'], 'uf': d['siglaUf'],
                                 'email': d.get('email') or '', 'sexo': sexo}
    if len(out) < 400:
        sys.exit(f'Lista de deputados incompleta ({len(out)}); não sobrescrevo.')
    return out


def salvar(caminho, obj):
    novo = json.dumps(obj, ensure_ascii=False, indent=1, sort_keys=True)
    try:
        velho = open(caminho, encoding='utf-8').read()
    except FileNotFoundError:
        velho = ''
    # ignora a hora do carimbo (mantém só o dia): no máximo um commit por dia,
    # e o campo "gerado" mostra aos agentes que a fila foi conferida hoje
    import re
    tira = lambda s: re.sub(r'("gerado": "\d{4}-\d{2}-\d{2})[^"]*"', r'\1"', s)
    if tira(novo) != tira(velho):
        open(caminho, 'w', encoding='utf-8').write(novo + '\n')
        print('atualizado:', caminho)


def main():
    agora = datetime.now(timezone(timedelta(hours=-3))).strftime('%Y-%m-%d %H:%M')
    deps = deputados()
    salvar('data/deputados_contato.json', {'gerado': agora, 'fonte': 'Câmara dos Deputados, dados abertos', 'deputados': deps})

    perg = get(TRIBUNA)['perguntas']
    fila = {}
    for p in perg:
        if p.get('status') != 'a_enviar':
            continue
        d = deps.get(str(p['dep']), {})
        f = fila.setdefault(str(p['dep']), {'nome': d.get('nome', ''), 'email': d.get('email', ''),
                                            'sexo': d.get('sexo', ''), 'partido': d.get('partido', ''),
                                            'uf': d.get('uf', ''), 'perguntas': []})
        f['perguntas'].append({'id': p['id'], 'tema': p.get('tema', ''), 'texto': p['texto'], 'uf_eleitor': p.get('uf', '')})
    salvar('data/tribuna_fila.json', {'gerado': agora, 'total': sum(len(v['perguntas']) for v in fila.values()), 'deputados': fila})


if __name__ == '__main__':
    main()
