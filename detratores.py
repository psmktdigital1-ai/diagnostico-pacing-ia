"""
Produtos detratores: identifica, dentro de cada campanha, os SKUs cujo ROAS
esta significativamente abaixo da media da propria campanha e que tem
investimento relevante o suficiente pra estar de fato puxando o resultado
pra baixo (evita apontar ruido de SKU com R$ 5 gastos no mes).

Mesma logica da planilha de detratores: nao e "SKU com ROAS baixo" isolado,
e "SKU que, dado o quanto investiu, tirou receita do resultado da campanha".
"""
from dataclasses import dataclass

import pandas as pd

LIMIAR_ROAS_RELATIVO = 0.6     # SKU entra na lista se ROAS < 60% do ROAS medio da campanha
PARTICIPACAO_MINIMA_INVESTIMENTO = 0.03  # e tiver investido pelo menos 3% da verba da campanha


@dataclass
class SkuDetrator:
    campanha: str
    sku: str
    investimento: float
    receita: float
    roas_sku: float
    roas_campanha: float
    participacao_investimento_pct: float
    receita_perdida_estimada: float  # receita que faria se performasse no ROAS medio da campanha


def identificar_detratores(diario: pd.DataFrame,
                            limiar_roas_relativo=LIMIAR_ROAS_RELATIVO,
                            participacao_minima=PARTICIPACAO_MINIMA_INVESTIMENTO
                            ) -> list[SkuDetrator]:
    detratores = []

    agrupado = diario.groupby(["Campanha", "SKU"], as_index=False).agg(
        Investimento=("Investimento", "sum"),
        Receita=("Receita", "sum"),
    )

    for campanha, grupo in agrupado.groupby("Campanha"):
        investimento_total_campanha = grupo["Investimento"].sum()
        receita_total_campanha = grupo["Receita"].sum()
        roas_campanha = (receita_total_campanha / investimento_total_campanha
                          if investimento_total_campanha else 0.0)

        for _, linha in grupo.iterrows():
            if linha["Investimento"] <= 0:
                continue
            roas_sku = linha["Receita"] / linha["Investimento"]
            participacao = linha["Investimento"] / investimento_total_campanha if investimento_total_campanha else 0

            if roas_sku < roas_campanha * limiar_roas_relativo and participacao >= participacao_minima:
                receita_no_roas_medio = linha["Investimento"] * roas_campanha
                receita_perdida = receita_no_roas_medio - linha["Receita"]

                detratores.append(SkuDetrator(
                    campanha=campanha,
                    sku=linha["SKU"],
                    investimento=round(linha["Investimento"], 2),
                    receita=round(linha["Receita"], 2),
                    roas_sku=round(roas_sku, 2),
                    roas_campanha=round(roas_campanha, 2),
                    participacao_investimento_pct=round(participacao * 100, 1),
                    receita_perdida_estimada=round(max(receita_perdida, 0), 2),
                ))

    detratores.sort(key=lambda d: d.receita_perdida_estimada, reverse=True)
    return detratores
