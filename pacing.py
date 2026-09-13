"""
Controle de pacing por campanha: compara o gasto real acumulado no mes com o
esperado pela regra de distribuicao (padrao: 65% do orcamento entre os dias
1-15, 35% entre os dias 16-30) e sinaliza campanhas sem investimento recente.

Essa e a mesma logica da planilha de pacing: baixa a base, olha investido x
orcamento planejado x estimado pro fim do mes, e alerta em caso de
under-pacing, over-pacing ou campanha parada.
"""
from dataclasses import dataclass

import pandas as pd

# curva de distribuicao esperada do orcamento ao longo do mes.
# (dia_final_do_bloco, % acumulado esperado ate esse dia)
CURVA_PADRAO = [(15, 0.65), (30, 1.00)]

DIAS_SEM_MOVIMENTACAO_ALERTA = 3
TOLERANCIA_PACING = 0.10  # +-10% em torno do esperado = "on pace"


@dataclass
class StatusPacing:
    campanha: str
    orcamento_mensal: float
    dia_atual: int
    investido_acumulado: float
    pct_investido: float
    pct_esperado: float
    diferenca_pp: float          # pontos percentuais: investido - esperado
    status: str                  # "on_pace" | "underpacing" | "overpacing"
    estimativa_fim_mes: float
    dias_sem_investimento: int
    alerta_parada: bool


def _pct_esperado_ate_o_dia(dia: int, curva=CURVA_PADRAO) -> float:
    """% do orcamento que deveria ter sido investido ate `dia`, interpolando
    linearmente dentro de cada bloco da curva."""
    dia_anterior, pct_anterior = 0, 0.0
    for dia_final, pct_acumulado in curva:
        if dia <= dia_final:
            se_bloco_dias = dia_final - dia_anterior
            avanco_no_bloco = (dia - dia_anterior) / se_bloco_dias if se_bloco_dias else 1
            return pct_anterior + (pct_acumulado - pct_anterior) * avanco_no_bloco
        dia_anterior, pct_anterior = dia_final, pct_acumulado
    return curva[-1][1]


def avaliar_pacing(diario: pd.DataFrame, orcamento_mensal_por_campanha: dict,
                    dia_atual: int, data_referencia: pd.Timestamp, curva=CURVA_PADRAO,
                    dias_alerta=DIAS_SEM_MOVIMENTACAO_ALERTA,
                    tolerancia=TOLERANCIA_PACING) -> list[StatusPacing]:
    """`data_referencia` e o "hoje" simulado (ultimo dia com dados no mes) -
    usado pra calcular ha quantos dias uma campanha nao recebe investimento."""
    resultados = []
    pct_esperado = _pct_esperado_ate_o_dia(dia_atual, curva)

    for campanha, orcamento in orcamento_mensal_por_campanha.items():
        df_camp = diario[diario["Campanha"] == campanha]
        investido = float(df_camp["Investimento"].sum())
        pct_investido = investido / orcamento if orcamento else 0.0
        diferenca_pp = (pct_investido - pct_esperado) * 100

        if diferenca_pp > tolerancia * 100:
            status = "overpacing"
        elif diferenca_pp < -tolerancia * 100:
            status = "underpacing"
        else:
            status = "on_pace"

        # extrapola o ritmo medio diario observado ate aqui pro mes inteiro (30 dias)
        estimativa_fim_mes = (investido / dia_atual) * 30 if dia_atual else 0.0

        df_com_verba = df_camp[df_camp["Investimento"] > 0]
        if df_com_verba.empty:
            dias_sem_investimento = dia_atual
        else:
            ultimo_dia_com_verba = df_com_verba["Data"].max()
            dias_sem_investimento = (data_referencia.normalize()
                                      - ultimo_dia_com_verba.normalize()).days

        resultados.append(StatusPacing(
            campanha=campanha,
            orcamento_mensal=orcamento,
            dia_atual=dia_atual,
            investido_acumulado=round(investido, 2),
            pct_investido=round(pct_investido * 100, 1),
            pct_esperado=round(pct_esperado * 100, 1),
            diferenca_pp=round(diferenca_pp, 1),
            status=status,
            estimativa_fim_mes=round(estimativa_fim_mes, 2),
            dias_sem_investimento=int(dias_sem_investimento),
            alerta_parada=dias_sem_investimento >= dias_alerta,
        ))

    return resultados
