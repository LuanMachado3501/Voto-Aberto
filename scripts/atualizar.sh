#!/usr/bin/env bash
# Baixa os dados oficiais, recalcula o que mudou e gera o index.html.
# Uso: bash scripts/atualizar.sh   (o robô do GitHub roda isto toda semana)
set -uo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
export RAW="${RAW:-$ROOT/raw}" PYTHONPATH="$ROOT/scripts"
mkdir -p "$RAW"; : > "$RAW/falhas.txt"

if [ "${SKIP_FETCH:-0}" = 1 ]; then echo "(pulando download: usando os arquivos que já estão em $RAW)"; else python3 "$ROOT/scripts/fetch.py" || echo "download falhou em todas as fontes" >> "$RAW/falhas.txt"; fi

cd "$ROOT/data"
run() {  # run <grupo> <script...>
  local g="$1"; shift
  if ! grep -qx "$g" "$RAW/ok.txt" 2>/dev/null; then
    echo "⏭ $g: sem dados novos, mantém os da última atualização"; echo "$g (download)" >> "$RAW/falhas.txt"; return
  fi
  for s in "$@"; do
    echo "▶ $s"
    python3 "$ROOT/scripts/$s.py" > /dev/null || { echo "✗ $s falhou"; echo "$s" >> "$RAW/falhas.txt"; }
  done
}
run votos   build_recentes build_pres build_governo build_destaques
run senado  build_senado
run cota    build_cota build_cota_page
run emendas build_emendas build_favorecidos

DATA="$ROOT/data" TEMPLATE="$ROOT/scripts/template.html" OUT="$ROOT/index.html" python3 "$ROOT/scripts/build_page.py"
echo "✓ index.html gerado"
if [ -s "$RAW/falhas.txt" ]; then echo "Partes que não atualizaram:"; cat "$RAW/falhas.txt"; fi
