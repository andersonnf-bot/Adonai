# BRK Analytics — Histórico do Projeto

Dashboard de faturamento BRK Tecnologia · Nstech — https://brk-analytics.onrender.com

## Fase 3 — Auditoria e correções (10-11/06/2026)

Auditoria completa de código + inspeção visual página a página.

### Correções de bugs (`bc8c747`)
- **Drill-down de Produtos**: clicar em um serviço lançava `KeyError 'Nome'` e o
  painel de detalhe nunca abria (groupby por GrupoEcon selecionava coluna inexistente)
- **Donut de Concentração**: Plotly reordenava as fatias por valor e as cores
  deixavam de corresponder às faixas (`sort=False` + cores distintas por faixa)
- **Ordenação das tabelas**: colunas de R$ eram texto e ordenavam alfabeticamente
  (R$ 9M acima de R$ 22M) — agora numéricas com formato pt-BR (`R$ 96.347.368`)
- **Matrizes de bolhas legíveis**: Portfólio (rótulo só top 12, outliers ±100%,
  eixo log, corte de receitas < R$ 1 mil) e Ação Gerencial (bolhas com mínimo
  visível, eixo ±200%)
- **Performance dos filtros**: campos de faturamento recalculavam todas as
  páginas a cada tecla digitada (`debounce=True`)

### Honestidade dos números (`0162e85`)
- **Mês parcial fora das comparações**: o export corta no meio do mês; KPIs,
  variações M/M, status (Em Queda/Churn) e insights usam só meses completos.
  Tag ⚠️ no topo avisa qual mês é parcial; a barra aparece esmaecida no gráfico
- **Faturado no Ano = YTD vs YTD**: antes comparava 2026 parcial com 2025
  inteiro (-36,4% enganoso); agora +65,2% vs mesmo período — o sinal verdadeiro
- **Receita em Risco = últimos 12 meses**: antes somava a receita histórica
  total de clientes inativos (R$ 146,6M); agora R$ 35,8M defensáveis
- **Insights com base mínima**: fim do "+7.587% de aceleração" em serviço de
  R$ 200; crescimento explosivo mostra valores ("Iscas: R$ 186K → R$ 3,3M em 3 meses")
- **pt-BR em todos os gráficos**: `separators` no template Plotly (eixos e
  hovers em 15.000.000) e helpers com vírgula decimal
- **Filtro de data incluía só até a meia-noite do último dia** — NFs do próprio
  dia do corte eram descartadas silenciosamente
- Filtro de faixa de valor por GrupoEcon (consistente com filtro de cliente);
  float64 nas somas; subtítulos com contagem fixa removidos

## Fase 2 — Dados e inteligência (04-10/06/2026)
- Normalização: merge EBAZAR, 15 serviços com grafias unificadas, correção
  HEALTH LOGISTICA / JNTL (289 registros exatos)
- Novos KPIs de crescimento: ano / semestre / trimestre / mês + clientes + tickets
- Radar Gerencial de Clientes (página Tendências): Health Score, matriz de ação,
  heatmap top 50, rankings de crescimento/queda, central de gestão exportável
- Sazonalidade, tendência com IC 80% e detecção automática de anomalias (⚡)
- Pipeline parquet (atualizar_dados.bat regenera e publica automaticamente)

## Fase 1 — Plataforma (até 03/06/2026)
- 4 páginas: Visão Executiva, Clientes, Produtos & Serviços, Tendências
- Sistema GrupoEcon de agrupamento de clientes em 3 camadas
  (mapeamento manual + 62 prefixos genéricos + primeira palavra como marca),
  219 grupos multi-entidade validados em 3 rodadas
- Filtros globais: período, ano, cliente (autocomplete), serviço, faixa de faturamento
- Receita líquida excluindo séries RET e DAV
- Insights automáticos de negócio (concentração, churn, novos clientes)
- Deploy no Render com republicação automática via push no GitHub
- Atualização mensal: soltar planilha nova + `atualizar_dados.bat`

## Próximos passos
1. Página "Receita & Risco": análise de reajuste por cliente vs IPCA/IGP-M
   ("receita deixada na mesa") + radar de churn com limiar configurável —
   migrar base para a planilha v2 (tem CNPJ) e reforçar GrupoEcon com CNPJ raiz
2. Recolocar projeção/forecast de 6 meses com intervalo de confiança
3. Painel explicativo do pico atípico de mar/2026 (R$ 31M)
4. Página de Metas · comparativo entre 2 clientes · exportação PDF · filtro vendedor
