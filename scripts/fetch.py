"""Baixa os dados oficiais para a pasta RAW.

Cada grupo (votos, emendas, cota) só é marcado como OK se todos os arquivos
dele chegaram inteiros. Se uma fonte falhar, o grupo fica de fora e o site
mantém os dados da semana anterior para aquela parte.
"""
import io, os, sys, time, zipfile, urllib.request

RAW = os.environ.get('RAW', 'raw')
os.makedirs(RAW, exist_ok=True)
CAMARA = 'https://dadosabertos.camara.leg.br/arquivos'
UA = {'User-Agent': 'Mozilla/5.0 (compatible; CentroPoliticoBot/1.0; +https://centropolitico.com.br)'}

def get(url, tries=4):
    for i in range(tries):
        try:
            req = urllib.request.Request(url, headers=UA)
            with urllib.request.urlopen(req, timeout=300) as r:
                return r.read()
        except Exception as e:
            print(f'  tentativa {i+1} falhou: {e}', flush=True)
            time.sleep(15 * (i + 1))
    raise RuntimeError(f'não consegui baixar {url}')

def save_csv(data, name, must_have):
    head = data[:4000].decode('utf-8-sig', 'ignore') + data[:4000].decode('latin1', 'ignore')
    if len(data) < 1000 or must_have not in head:
        raise RuntimeError(f'{name}: o arquivo não parece o CSV esperado (sem a coluna {must_have})')
    with open(os.path.join(RAW, name), 'wb') as f:
        f.write(data)
    print(f'  ok {name} ({len(data)/1e6:.1f} MB)', flush=True)

def from_zip(data, wanted):
    z = zipfile.ZipFile(io.BytesIO(data))
    for n in z.namelist():
        if os.path.basename(n).lower() == wanted.lower():
            return z.read(n)
    raise RuntimeError(f'{wanted} não está dentro do zip ({z.namelist()})')

def votos():
    for a in (2025, 2026):
        save_csv(get(f'{CAMARA}/votacoesVotos/csv/votacoesVotos-{a}.csv'), f'votacoesVotos-{a}.csv', 'deputado_id')
        save_csv(get(f'{CAMARA}/votacoesOrientacoes/csv/votacoesOrientacoes-{a}.csv'), f'votacoesOrientacoes-{a}.csv', 'orientacao')
    save_csv(get(f'{CAMARA}/votacoes/csv/votacoes-2026.csv'), 'votacoes-2026.csv', 'descricao')
    save_csv(get(f'{CAMARA}/votacoesProposicoes/csv/votacoesProposicoes-2026.csv'), 'votacoesProposicoes-2026.csv', 'proposicao_id')

def cota():
    for a in (2023, 2024, 2025, 2026):
        z = get(f'https://www.camara.leg.br/cotas/Ano-{a}.csv.zip')
        save_csv(from_zip(z, f'Ano-{a}.csv'), f'Ano-{a}.csv', 'ideCadastro')

def emendas():
    z = get('https://portaldatransparencia.gov.br/download-de-dados/emendas-parlamentares/UNICO')
    save_csv(from_zip(z, 'EmendasParlamentares.csv'), 'EmendasParlamentares.csv', 'Código da Emenda')
    save_csv(from_zip(z, 'EmendasParlamentares_PorFavorecido.csv'), 'EmendasParlamentares_PorFavorecido.csv', 'Favorecido')

ok = []
for nome, f in [('votos', votos), ('cota', cota), ('emendas', emendas)]:
    print(f'▶ {nome}', flush=True)
    try:
        f(); ok.append(nome)
    except Exception as e:
        print(f'✗ {nome}: {e}', flush=True)
open(os.path.join(RAW, 'ok.txt'), 'w').write('\n'.join(ok) + '\n')
print('Grupos baixados:', ', '.join(ok) or 'nenhum')
sys.exit(0 if ok else 1)
