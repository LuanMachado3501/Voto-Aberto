"""Gera data/senado_data.json: os 81 senadores, a posição de cada um no plenário
(calculada pelos votos nominais abertos de 2025 e 2026), presença, fidelidade ao
partido e as votações mais recentes com o voto de cada senador.

Entrada (pasta RAW): senado_nominal_2025.json, senado_nominal_2026.json,
senado_lista.json (dados abertos do Senado).
"""
import json, os, collections
import numpy as np

RAW = os.environ.get('RAW', 'raw')
ANOS = (2025, 2026)
LIMIAR = 0.05          # só entram na posição votações em que a minoria teve pelo menos 5%
MIN_VOTOS = 6          # com menos que isso, a posição é estimada pela média do partido
LBL = {"NOVO": "Novo", "REDE": "Rede", "MISSÃO": "Missão", "REPUBLICANOS": "Republicanos", "UNIÃO": "União",
       "PODE": "Podemos", "SOLIDARIEDADE": "Solidariedade", "CIDADANIA": "Cidadania", "AVANTE": "Avante",
       "S/Partido": "Sem partido"}
NOMES = {'PEC 221/2019': 'Fim da escala 6x1'}
VOTOU = {'Sim', 'Não', 'Abstenção'}
JUSTIF = {'AP', 'LS', 'MIS', 'LP', 'LAP', 'LC', 'LG', 'REP'}


def lista(x):
    return x if isinstance(x, list) else ([x] if x else [])


def carregar():
    vots = []
    for a in ANOS:
        d = json.load(open(os.path.join(RAW, f'senado_nominal_{a}.json'), encoding='utf-8'))
        for v in lista(d['ListaVotacoes'].get('Votacoes', {}).get('Votacao')):
            if v.get('Secreta') != 'N':
                continue
            votos = {str(p['CodigoParlamentar']): p['Voto'] for p in lista(v['Votos']['VotoParlamentar'])}
            vots.append({'id': v['CodigoSessaoVotacao'], 'd': v['DataSessao'], 'seq': int(v.get('SequencialSessao') or 0),
                         'ident': v.get('DescricaoIdentificacaoMateria') or '', 'mat': v.get('CodigoMateria') or '',
                         'desc': v.get('DescricaoVotacao') or '', 'res': v.get('Resultado') or '', 'votos': votos})
    vots.sort(key=lambda v: (v['d'], v['seq'], v['id']))
    return vots


def main():
    vots = carregar()
    L = json.load(open(os.path.join(RAW, 'senado_lista.json'), encoding='utf-8'))
    sens, pres = [], None
    for p in lista(L['ListaParlamentarEmExercicio']['Parlamentares']['Parlamentar']):
        i = p['IdentificacaoParlamentar']; m = p.get('Mandato', {})
        fim = (m.get('SegundaLegislaturaDoMandato') or {}).get('DataFim') or (m.get('PrimeiraLegislaturaDoMandato') or {}).get('DataFim') or ''
        s = {'id': str(i['CodigoParlamentar']), 'n': i['NomeParlamentar'], 'p': LBL.get(i.get('SiglaPartidoParlamentar'), i.get('SiglaPartidoParlamentar') or ''),
             'uf': i.get('UfParlamentar') or m.get('UfParlamentar') or '', 'sx': (i.get('SexoParlamentar') or 'M')[0],
             'fim': fim[:4], 'sup': m.get('DescricaoParticipacao') != 'Titular'}
        sens.append(s)
    ids = [s['id'] for s in sens]

    # presidente: quem aparece como "Presidente (art. 51 RISF)" na votação mais recente
    for v in reversed(vots):
        pr = [k for k, x in v['votos'].items() if x.startswith('Presidente')]
        if pr:
            pres = pr[0]; break

    # posição: componente principal dos votos Sim/Não nas votações disputadas
    disp = []
    for v in vots:
        c = collections.Counter(x for x in v['votos'].values() if x in ('Sim', 'Não'))
        t = c['Sim'] + c['Não']
        if t >= 30 and min(c['Sim'], c['Não']) / t >= LIMIAR:
            disp.append(v)
    M = np.full((len(ids), len(disp)), np.nan)
    for j, v in enumerate(disp):
        for k, x in v['votos'].items():
            if k in ids and x in ('Sim', 'Não'):
                M[ids.index(k), j] = 1 if x == 'Sim' else -1
    n_obs = (~np.isnan(M)).sum(1)
    Z = M - np.nanmean(M, 0)
    Z = np.nan_to_num(Z)
    _, S, Vt = np.linalg.svd(Z, full_matrices=False)
    var = float(S[0] ** 2 / (S ** 2).sum()) if len(S) else 0
    score = Z @ Vt[0] / np.maximum(n_obs, 1)
    part = [s['p'] for s in sens]
    pt = [score[k] for k in range(len(ids)) if part[k] == 'PT' and n_obs[k] >= MIN_VOTOS]
    if pt and np.mean(pt) > 0:
        score = -score
    ok = n_obs >= MIN_VOTOS
    esc = np.max(np.abs(score[ok])) if ok.any() else 1
    score = score / esc
    pm = collections.defaultdict(list)
    for k, s in enumerate(sens):
        if ok[k]:
            pm[s['p']].append(score[k])
    for k, s in enumerate(sens):
        if ok[k]:
            s['s'] = round(float(score[k]), 3)
        else:
            s['s'] = round(float(np.mean(pm[s['p']])) if pm[s['p']] else 0.0, 3); s['e'] = 1
        s['v'] = int(n_obs[k])

    # presença e fidelidade ao partido (todas as votações abertas de 2025-26)
    maioria = []
    for v in vots:
        cp = collections.defaultdict(collections.Counter)
        for k, x in v['votos'].items():
            if x in ('Sim', 'Não') and k in ids:
                cp[part[ids.index(k)]][x] += 1
        maioria.append({p: c.most_common(1)[0][0] for p, c in cp.items()
                        if sum(c.values()) >= 2 and (len(c) == 1 or c['Sim'] != c['Não'])})
    for k, s in enumerate(sens):
        tot = vt = jus = seg = segt = 0
        for v, mj in zip(vots, maioria):
            x = v['votos'].get(s['id'])
            if x is None or x.startswith('Presidente'):
                continue
            tot += 1
            if x in VOTOU:
                vt += 1
            elif x in JUSTIF:
                jus += 1
            if x in ('Sim', 'Não') and s['p'] in mj:
                segt += 1; seg += mj[s['p']] == x
        s['pr'] = [vt, tot, jus]
        s['fp'] = round(100 * seg / segt) if segt >= 5 else None

    # votações recentes para a página de cada senador e para o destaque
    rec = []
    for v in vots[-30:][::-1]:
        c = collections.Counter(v['votos'].values())
        desc = v['desc'].replace('Votação nominal d', 'D', 1)
        rec.append({'id': v['id'], 'd': v['d'], 'ident': v['ident'], 'nome': NOMES.get(v['ident'], ''),
                    'desc': desc, 'mat': v['mat'], 'res': v['res'],
                    'pl': [c['Sim'], c['Não'], c['Abstenção']],
                    'vt': {k: x for k, x in v['votos'].items()}})
    sens = [s for s in sens if s['id'] != pres]
    presd = next(({'id': p['IdentificacaoParlamentar']['CodigoParlamentar'], 'n': p['IdentificacaoParlamentar']['NomeParlamentar'],
                   'p': LBL.get(p['IdentificacaoParlamentar'].get('SiglaPartidoParlamentar'), p['IdentificacaoParlamentar'].get('SiglaPartidoParlamentar')),
                   'uf': p['IdentificacaoParlamentar'].get('UfParlamentar')}
                  for p in lista(L['ListaParlamentarEmExercicio']['Parlamentares']['Parlamentar'])
                  if str(p['IdentificacaoParlamentar']['CodigoParlamentar']) == pres), None)
    sens.sort(key=lambda s: s['s'])
    out = {'disputadas': len(disp), 'abertas': len(vots), 'var': round(var * 100), 'sens': sens, 'pres': presd, 'rec': rec}
    json.dump(out, open('senado_data.json', 'w', encoding='utf-8'), ensure_ascii=False, separators=(',', ':'))
    print(len(vots), 'abertas;', len(disp), 'disputadas; variação explicada', round(var * 100), '%;',
          len(sens), 'senadores;', sum(1 for s in sens if s.get('e')), 'estimados; presidente', presd and presd['n'])


if __name__ == '__main__':
    main()
