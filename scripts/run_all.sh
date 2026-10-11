set -e
cd /home/claude/voto_aberto/site
python3 build_historico.py > /dev/null
python3 build_tenure.py > /dev/null
python3 build_emendas.py > /dev/null
python3 build_favorecidos.py > /dev/null
python3 build_governo.py > /dev/null
python3 build_tse.py > /dev/null
python3 build_hcand.py > /dev/null
python3 build_cota.py > /dev/null
python3 build_cota_page.py > /dev/null
python3 -c "
import json;H=json.load(open('historico_data.json'));print(len(H['key']),[k['t'] for k in H['key']]);d=H['deps']['209787'];print(sorted(d.keys()), d['k'])"
python3 build_recentes.py > /dev/null
