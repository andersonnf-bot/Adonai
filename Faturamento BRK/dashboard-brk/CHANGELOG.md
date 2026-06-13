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

### Hover desalinhado em todos os gráficos (11/06)
- **Causa**: `zoom: 0.85` global no CSS — o Plotly não compensa zoom CSS no
  cálculo da posição do mouse; a caixinha de hover abria deslocada (mostrando
  meses anteriores) e a primeira/última coluna ficava inacessível. Zoom
  removido — **não reintroduzir**
- Datas dos eixos e hovers em inglês ("Oct 1, 2024") → padronizadas em mm/aaaa
  nos gráficos de série temporal

### Etapa 2 — Análise de Clientes repaginada (11/06)
- Removidas as colunas NFs, Serviços e Ticket Médio NF (pouco acionáveis)
- Novas colunas: **Média 3M** + variação vs 3 meses anteriores e **Média 6M** +
  variação vs 6 meses anteriores (meses completos; variações em verde/vermelho)
- Tabela com **rolagem contínua virtualizada** no lugar da paginação
  (sem fixed_rows: combinado com virtualization trava — bug do dash_table)
- Var. M/M validada e mantida como mês vs mês anterior (decisão 11/06);
  abr/26 vermelho é efeito do pico atípico de mar/26
- KPI "Faturado no Ano" → **"Faturado 12 Meses"** (janela móvel) — alinha a
  escada 1M/3M/6M/12M; o ano parcial aparecia menor que o 6M e confundia
- Tema **Light é o padrão de abertura** (Dark a um clique, escolha memorizada)
- Para reverter qualquer item: `git revert` do commit correspondente

### Etapa 2 — Rodapé e ícones ainda mais discretos (13/06)
- Rodapé reduzido: data/nome 11→9,5px, cargo 10→8,5px, nome com peso 500
- Ícones menores de novo: bandeiras 20×14 → 17×12, tema 16×16 → 13×13

### Etapa 2 — Preferências reposicionadas para o rodapé + ícones menores (13/06)
- Tema/idioma desceram para junto da identidade no rodapé (padrão de apps com
  sidebar: Linear/Notion/Slack — preferências não se misturam à navegação).
  Ordem na sidebar: módulos (topo) → Resumo da Base → preferências → rodapé;
  os módulos ganharam respiro (antes as prefs ficavam coladas neles)
- Ícones reduzidos: bandeiras 24×17 → 20×14, tema 19×19 → 16×16
- `.sidebar-prefs` passou a usar `border-top` (separa do Resumo)

### Etapa 2 — Union Jack + tema em ícones sol/lua (13/06)
- Bandeira do inglês trocada de Inglaterra (cruz de São Jorge) para **Reino
  Unido / Union Jack** (padrão mundial), construída com clip de contraordem
- Tema Light/Dark também virou **ícones clicáveis** (sol âmbar / lua índigo),
  mesma lógica das bandeiras: dropdown `theme-select` oculto guarda valor +
  persistência; clientside callbacks fazem clique→valor e valor→destaque
- Classes unificadas: `.pref-icons`/`.pref-icon` (tema e idioma); imagens em
  `.pref-flag-img` (retangular, com contorno) e `.pref-theme-img` (quadrado)
- Novos assets: `assets/icons/sun.svg`, `assets/icons/moon.svg`

### Etapa 2 — Bandeiras reais no seletor de idioma (13/06)
- Emoji de bandeira (🇧🇷🇺🇸🇪🇸) NÃO renderiza no Windows (vira "BR"/"US"/"ES") —
  trocado por SVGs reais em `assets/flags/` (br, en, es)
- Idioma vira 3 bandeirinhas clicáveis: Brasil (PT), **Inglaterra** (EN, antes
  era EUA) e Espanha (ES). Inativas esmaecidas, ativa com anel laranja; sutil
- O `dcc.Dropdown#lang-select` fica oculto só guardando valor + persistência;
  clientside callbacks traduzem o clique→valor e valor→destaque. Toda a
  engrenagem de i18n (Input('lang-select','value')) segue intacta
- Contorno fino nas bandeiras p/ a da Inglaterra (fundo branco) não sumir no
  tema claro

### Etapa 2 — Preferências na sidebar + dica de clique reforçada + rodapé de controle (13/06)
- **Tema e idioma saíram da barra de filtros para a sidebar** (abaixo dos
  módulos): são preferências, não filtros. A barra superior fica só com o que
  filtra dados e, em telas ~1920px, colapsa de 2 linhas para 1 (104→59px) —
  os gráficos sobem ~45px
- Refatoração: sidebar virou shell estático com 2 containers dinâmicos (nav e
  resumo) + 2 blocos estáticos (preferências e rodapé). Os selects tema/idioma
  ficam fora dos callbacks de navegação — recriá-los dentro da navbar criaria
  loop e perderia o estado (são Input de muitos callbacks)
- **Dica "clique para detalhar" mais visível**: glow laranja pulsante e lento
  na pílula (animação `hint-pulse`, 2,4s), idêntico nos 3 módulos; respeita
  `prefers-reduced-motion`
- **Rodapé de controle na sidebar**: "🔄 Atualizado em DD/MM/AAAA" (mtime do
  parquet, via `get_data_mtime` no loader) + "Adonai · Anderson Ferreira ·
  Gerente de Área"

### Etapa 2 — Mesma dinâmica em Produtos e Radar (12/06)
- Tabelas de Produtos & Serviços (10 colunas) e Central de Gestão do Radar
  (15 colunas) enquadradas na tela: larguras percentuais + table-layout fixed
  via CSS, cabeçalho em 2 linhas, células densas
- Cursor de mão, hover laranja na linha, pílula "clique para detalhar" e
  célula ativa destacada também nas duas páginas; tooltip com nome completo
  (serviço/cliente) quando a coluna trunca
- Larguras do Radar calibradas no preview até zero células cortadas
  (inclusive outliers tipo "+2573,4%")

### Etapa 2 — Tabela de Clientes enquadrada + affordance de clique (12/06)
- **Toda a tabela cabe na tela** (fim da rolagem horizontal): larguras
  percentuais por coluna (`_COL_WIDTHS`) + `table-layout: fixed` no CSS.
  ⚠️ Forçar isso via prop `css=` do DataTable infla a tabela para 800000px
  com virtualization — a regra tem que viver no style.css (`#clientes-table`)
- Cabeçalho quebra em 2 linhas quando preciso; células mais densas (6px 8px);
  nome completo do cliente em tooltip quando a coluna trunca
- **Clique mais óbvio**: cursor de mão sobre a tabela, linha inteira com
  realce laranja no hover, pílula "👆 Clique numa linha para detalhar" no
  cabeçalho do card e célula clicada destacada em laranja

### Etapa 2 — Cockpit em todas as páginas + contexto nos espaços vazios (12/06)
- Trilho lateral da Visão Executiva ganhou **Top 5 Clientes** e **Top 5 Serviços**
  do período (com barras de proporção) — fim do vão abaixo dos insights
- Sidebar ganhou **Resumo da Base**: período dos dados, receita líquida,
  grupos econômicos e serviços — preenche o vão abaixo dos módulos
- Headers compactos em linha única nas 4 páginas
- Radar: KPIs em dois pesos (3 heróis de receita + 6 contadores compactos)
- Densidade global: paddings/margens reduzidos em cards, KPIs e grids

### Etapa 2 — Visão Executiva vira Cockpit Executivo (12/06)
- Header em linha única (título + subtítulo inline + tag de mês parcial)
- KPIs em dois pesos: 6 heróis (Receita, 12M, 6M, Trimestre, Mês, MRR) +
  4 compactos (clientes e tickets)
- Gráfico de Receita Mensal como herói no topo da coluna principal
- **Insights viram trilho lateral** fixo (sticky) — visíveis durante a rolagem
- Títulos internos dos gráficos removidos (duplicavam o cabeçalho do card);
  informação dinâmica foi para o subtítulo (risco de concentração, pico/vale)
- Espaçamentos reduzidos — primeira tela mostra KPIs + tendência + alertas

### Tema claro + 3 idiomas (11/06)
- Seletores na barra de filtros: 🌙 Dark / ☀️ Light e 🇧🇷 PT / 🇺🇸 EN / 🇪🇸 ES,
  memorizados pelo navegador de cada usuário
- Tema claro completo: CSS por variáveis (`data-theme` no shell), template
  Plotly `nstech_light`, estilos de tabela por tema
- i18n em `components/i18n.py` (~150 chaves × 3 idiomas): navegação, filtros,
  KPIs, títulos de gráficos, colunas, status e insights traduzidos
- Status nas tabelas marcados por emoji (independem do idioma para as cores)
- Login dispensado em localhost (fora do Render) — facilita uso local e dev

### Autenticação (11/06)
- Login básico (usuário/senha) em todo o dashboard — dados de faturamento
  deixam de ficar públicos para quem tiver o link
- Credenciais via variáveis de ambiente `DASH_USER` / `DASH_PASS` no Render
  (padrão definido no código para uso imediato)

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
