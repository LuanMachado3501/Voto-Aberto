# Voto Aberto

Plataforma de acompanhamento de votos e notícias no parlamento brasileiro: como cada deputado federal vota, quanto recebe e gasta, e com quem você vota parecido.

**Site:** https://luanmachado3501.github.io/Voto-Aberto/

## O que tem
- **Plenário:** as 513 cadeiras da Câmara, posicionadas pelo voto real de cada deputado em 2025–26 (bloco do PT à esquerda, bloco do PL à direita), e a cadeira da presidência.
- **Página de cada deputado:** votos em 20 votações importantes, quanto segue o partido e o governo, emendas parlamentares e para onde foram, cota parlamentar, eleição de 2026, patrimônio declarado, histórico de candidaturas e notícias.
- **Teste "Quais deputados votam como você?":** 20 votações reais + 40 perguntas de opinião, com resultado por deputado, partido, teia de 8 eixos e mapa político. Nada é guardado.

## Fontes (todas públicas)
- Câmara dos Deputados, dados abertos: votações, votos, orientações, deputados, cota parlamentar
- Portal da Transparência: emendas parlamentares
- TSE: candidaturas, bens e histórico de candidaturas (Eleições 2026)

## Estrutura
- `index.html`: o site inteiro (um arquivo, com os dados embutidos)
- `data/`: os dados já processados (JSON)
- `scripts/`: scripts Python que geram os dados a partir dos arquivos oficiais, e o `template.html` do site

> Os scripts ainda apontam para os arquivos baixados manualmente. O próximo passo é automatizar o download e a atualização com GitHub Actions.
