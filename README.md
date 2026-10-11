# Centro Político

Centro de informação, não posição política. **Voto Aberto** é a parte do projeto sobre como os deputados votam.

Plataforma de acompanhamento de votos e notícias no parlamento brasileiro: como cada deputado federal vota, quanto recebe e gasta, e com quem você vota parecido.

**Site:** https://centropolitico.com.br

## O que tem
- **Voto Aberto (plenário):** as 513 cadeiras da Câmara, posicionadas pelo voto real de cada deputado em 2025–26 (bloco do PT à esquerda, bloco do PL à direita), e a cadeira da presidência.
- **Página de cada deputado:** votos em 20 votações importantes, quanto segue o partido e o governo, emendas parlamentares e para onde foram, cota parlamentar, eleição de 2026, patrimônio declarado, histórico de candidaturas e notícias.
- **Cota (quanto gastam):** gasto médio por mês de cada deputado com a cota parlamentar, comparado com a mediana da bancada do próprio estado, e quanto do total foi para um só fornecedor.
- **Urna (teste) "Quais deputados votam como você?":** 20 votações reais + 40 perguntas de opinião, com resultado por deputado, partido, teia de 8 eixos e mapa político. Nada é guardado.

## Fontes (todas públicas)
- Câmara dos Deputados, dados abertos: votações, votos, orientações, deputados, cota parlamentar
- Portal da Transparência: emendas parlamentares
- TSE: candidaturas, bens e histórico de candidaturas (Eleições 2026)

## Estrutura
- `index.html`: o site inteiro (um arquivo, com os dados embutidos)
- `data/`: os dados já processados (JSON)
- `scripts/`: scripts Python que geram os dados a partir dos arquivos oficiais, e o `template.html` do site

## Atualização automática
Toda segunda às 6h (Brasília) o robô em `.github/workflows/atualizar-dados.yml` roda `scripts/atualizar.sh`:
1. `scripts/fetch.py` baixa da Câmara (votações, votos, orientações, cota) e do Portal da Transparência (emendas);
2. os scripts recalculam presença, últimas votações, alinhamento com o governo, cota e emendas;
3. se algo mudou, o `index.html` e a pasta `data/` são atualizados e o site é publicado.

Na mesma rodada, `scripts/build_destaques.py` calcula o **índice de destaque** das votações recentes do plenário (70% atenção pública, medida pelo número de notícias que citam a proposta; 30% disputa, medida por placar apertado, governo e oposição em lados opostos e número de votações) e grava `data/destaques.json`. A lista aparece no resumo de cada rodada do robô.

Se uma fonte estiver fora do ar, só aquela parte deixa de atualizar e o resto segue; o robô marca a rodada com aviso. Para rodar na hora: aba **Actions → Atualizar dados → Run workflow**.

Continuam manuais: posição das cadeiras no plenário, as 20 votações em destaque, dados do TSE (eleição de 2026) e as notícias destacadas.

## Licença
- **Dados e textos:** CC BY 4.0. Pode usar e republicar, citando "Centro Político (centropolitico.com.br)".
- **Código, visual e marca:** todos os direitos reservados. O código está aberto para conferência; reutilizar exige autorização. Detalhes em [LICENSE](LICENSE).
