"""
Gera dados sinteticos de investimento diario em midia paga, por campanha e SKU,
simulando a extracao que normalmente se baixa direto da plataforma (Meta Ads,
Google Ads, Amazon Ads, Mercado Ads etc.) e cola numa aba de planilha.

Isso NAO se conecta a nenhuma plataforma real - e um gerador de dados de
exemplo pra rodar o projeto de ponta a ponta sem precisar de credencial de
nenhuma conta. Pra usar com dados reais, troque as duas funcoes abaixo por um
carregador que le o export/CSV da sua plataforma (ver README).

Retorna duas tabelas, no mesmo espirito das duas abas que normalmente
compoem esse tipo de planilha:
  - diario:  1 linha por (Data, Campanha, SKU) com Investimento/Cliques/
             Conversoes/Receita  -> usada pelo pacing e pelos detratores
  - eventos: 1 linha por conversao individual, com a Hora em que ela
             aconteceu -> usada pela analise de horario
"""
import numpy as np
import pandas as pd
from datetime import datetime, timedelta

RNG = np.random.default_rng(42)

CAMPANHAS = [
    {"campanha": "Eletro - Lançamento",          "orcamento_mes": 18000, "skus": 6},
    {"campanha": "Casa & Decoração - Sempre On", "orcamento_mes": 9000,  "skus": 5},
    {"campanha": "Beleza - Black Week Prep",     "orcamento_mes": 6000,  "skus": 4},
    {"campanha": "Infantil - Institucional",     "orcamento_mes": 4000,  "skus": 3},
]

# dia do mes (1-30) em que cada campanha "parou de rodar" - usado pra testar
# o alerta de campanha sem movimentacao. Ausente da lista = rodou o mes inteiro.
CAMPANHA_PAROU_NO_DIA = {
    "Infantil - Institucional": 21,
}

# fator que acelera/desacelera o ritmo de investimento de cada campanha em
# relacao ao esperado pela curva de pacing - existe so pra essa demonstracao
# mostrar os tres status possiveis (on pace / underpacing / overpacing) num
# unico relatorio. Numa extracao real esse "fator" nao existe, e so o reflexo
# de como o time de mídia pausou/acelerou lances ao longo do mes.
FATOR_RITMO = {
    "Eletro - Lançamento": 1.0,            # no ritmo
    "Casa & Decoração - Sempre On": 1.35,  # acelerou o investimento
    "Beleza - Black Week Prep": 0.8,       # ficou pra trás
    "Infantil - Institucional": 1.0,       # (parada a partir do dia 21, ver acima)
}


# multiplicador de taxa de conversao por dia da semana (Seg=0 ... Dom=6) -
# pico leve na quarta-feira e no fim de semana, padrao comum em e-commerce BR
FATOR_CONVERSAO_DIA_SEMANA = [1.0, 1.05, 1.25, 1.05, 0.95, 1.15, 1.2]


def _gerar_skus(campanha: str, n: int) -> list[str]:
    return [f"{campanha[:3].upper()}-SKU{str(i + 1).zfill(2)}" for i in range(n)]


def carregar_dados(dia_atual: int = 24, ano: int = 2026, mes: int = 9):
    """Gera os dados sinteticos do mes ate `dia_atual`.

    Retorna (diario, eventos):
      diario  -> colunas Data, Campanha, SKU, Investimento, Cliques,
                 Conversoes, Receita
      eventos -> colunas Data, Campanha, SKU, Hora (uma linha por conversao)
    """
    linhas_diario = []
    linhas_evento = []
    data_inicio = datetime(ano, mes, 1)
    horas_pico = {12, 13, 14, 19, 20, 21, 22}
    horas_todas = list(range(24))
    prob_hora = np.array([3.0 if h in horas_pico else 1.0 for h in horas_todas])
    prob_hora = prob_hora / prob_hora.sum()

    for camp in CAMPANHAS:
        nome = camp["campanha"]
        orcamento_mes = camp["orcamento_mes"]
        skus = _gerar_skus(nome, camp["skus"])
        para_no_dia = CAMPANHA_PAROU_NO_DIA.get(nome)

        # 1 a cada 3 SKUs vira "detrator": ROAS estruturalmente mais baixo
        n_detratores = max(1, camp["skus"] // 3)
        detratores = set(RNG.choice(skus, size=n_detratores, replace=False))

        orcamento_diario_base = orcamento_mes / 30
        fator_ritmo = FATOR_RITMO.get(nome, 1.0)

        for dia in range(1, dia_atual + 1):
            data = data_inicio + timedelta(days=dia - 1)

            if para_no_dia and dia > para_no_dia:
                continue  # campanha parou de investir a partir daqui

            invest_dia_total = orcamento_diario_base * fator_ritmo * RNG.uniform(0.9, 1.1)

            pesos = RNG.dirichlet(np.ones(len(skus)))
            for sku, peso in zip(skus, pesos):
                investimento = round(invest_dia_total * peso, 2)
                if investimento <= 0:
                    continue

                roas_base = 1.15 if sku in detratores else RNG.uniform(2.8, 4.5)
                roas_dia = max(0.3, RNG.normal(roas_base, 0.35))
                receita = round(investimento * roas_dia, 2)

                cliques = max(1, int(RNG.poisson(investimento / 2.5)))
                # taxa de conversao varia um pouco por dia da semana, simulando
                # o padrao tipico de e-commerce BR (quarta e fim de semana convertem melhor)
                fator_dia_semana_conv = FATOR_CONVERSAO_DIA_SEMANA[data.weekday()]
                taxa_conv = RNG.uniform(0.03, 0.08) * fator_dia_semana_conv
                conversoes = int(cliques * taxa_conv)

                linhas_diario.append({
                    "Data": data,
                    "Campanha": nome,
                    "SKU": sku,
                    "Investimento": investimento,
                    "Cliques": cliques,
                    "Conversoes": conversoes,
                    "Receita": receita,
                })

                if conversoes > 0:
                    horas_sorteadas = RNG.choice(horas_todas, size=conversoes, p=prob_hora)
                    for hora in horas_sorteadas:
                        linhas_evento.append({
                            "Data": data,
                            "Campanha": nome,
                            "SKU": sku,
                            "Hora": int(hora),
                        })

    diario = pd.DataFrame(linhas_diario)
    eventos = pd.DataFrame(linhas_evento)
    return diario, eventos


def orcamento_mensal(campanha: str) -> float:
    for c in CAMPANHAS:
        if c["campanha"] == campanha:
            return c["orcamento_mes"]
    raise KeyError(campanha)
