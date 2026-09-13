# Diagnóstico Diário de Pacing (mídia paga)

Protótipo que consolida em um único painel diário três controles que uso na operação real de mídia paga: **pacing** (investido x orçamento planejado), **produtos detratores** (SKUs puxando o ROAS pra baixo) e **conversões por horário** (dayparting). Em vez de abrir três planilhas separadas, o diagnóstico já aponta a causa raiz de cada alerta.

Este repositório é uma reimplementação em Python da lógica dessas planilhas, com **dados sintéticos** — não se conecta a nenhuma plataforma de mídia real. Serve pra demonstrar a lógica de cálculo de forma honesta e testável; a extração de dados real (Meta Ads, Google Ads, Amazon Ads, Mercado Ads etc.) precisa ser adaptada por conta própria (ver seção "Usar com dados reais").

## O que cada módulo faz

1. **`dados.py`** — gera dados sintéticos diários de investimento, cliques, conversões e receita por campanha/SKU, e os eventos de conversão por horário. Inclui cenários propositais: uma campanha "no ritmo", uma acelerada, uma atrasada e uma parada — pra exercitar os três status de pacing e o alerta de campanha sem movimentação.
2. **`pacing.py`** — compara o % do orçamento investido até o dia de referência com o % esperado por uma curva de distribuição (padrão: 65% do orçamento entre os dias 1–15, 35% entre os dias 16–30), calcula uma estimativa de fechamento do mês pelo ritmo atual, e sinaliza campanhas sem investimento nos últimos N dias.
3. **`detratores.py`** — para cada campanha, identifica SKUs cujo ROAS está significativamente abaixo da média da própria campanha (e que têm investimento relevante o suficiente pra isso importar), e estima quanta receita a campanha deixou de gerar por causa deles.
4. **`horarios.py`** — agrega as conversões por hora do dia e por dia da semana, por campanha e no geral, apontando os horários/dias de melhor conversão.
5. **`relatorio.py`** — monta o HTML final consolidando os três blocos.
6. **`main.py`** — orquestra os passos acima e salva o relatório em `saida/`.

Exemplo de saída real: [`exemplo_diagnostico.html`](exemplo_diagnostico.html) (baixe e abra no navegador).

## Como rodar

```bash
pip install -r requirements.txt
python3 main.py
```

Não precisa de nenhuma variável de ambiente ou credencial — os dados são gerados na hora. O relatório é salvo em `saida/diagnostico_<data>.html`.

Pra testar outro dia do mês (e ver os status de pacing mudarem), edite `DIA_ATUAL` em `main.py`.

## Usar com dados reais

Troque a chamada em `main.py`:

```python
# de:
diario, eventos = carregar_dados(dia_atual=DIA_ATUAL)
# para:
diario = carregar_diario_de_csv("investimento_diario.csv")   # Data, Campanha, SKU, Investimento, Cliques, Conversoes, Receita
eventos = carregar_eventos_de_csv("conversoes_horario.csv")  # Data, Campanha, SKU, Hora
```

E monte um dicionário `{campanha: orçamento_mensal}` real pra passar em `avaliar_pacing`, no lugar de `orcamento_mensal()` (que hoje só lê a lista fixa em `dados.py`).

A curva de distribuição do orçamento (`CURVA_PADRAO` em `pacing.py`) e os limiares de detrator (`LIMIAR_ROAS_RELATIVO`, `PARTICIPACAO_MINIMA_INVESTIMENTO` em `detratores.py`) são parâmetros — ajuste pro padrão real da sua operação.

## Stack

Python, Pandas, NumPy.

## Status

Funcional de ponta a ponta com dados sintéticos: geração de dados, cálculo de pacing (com os três status e o alerta de campanha parada), identificação de detratores e análise de horário, e montagem do HTML. Não testado com uma extração de plataforma real — a integração de dados reais (parsing de CSV/API de cada plataforma) ainda não está implementada, só documentada acima como próximo passo.
