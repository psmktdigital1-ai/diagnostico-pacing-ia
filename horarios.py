"""
Relação de conversões por horário e dia da semana: aponta em quais janelas de
horário/dia cada campanha (ou o conjunto todo) mais converteu, pra orientar
concentração de orçamento e ajuste de lance por horário (dayparting).
"""
from dataclasses import dataclass

import pandas as pd

DIAS_SEMANA_PT = ["Segunda", "Terça", "Quarta", "Quinta", "Sexta", "Sábado", "Domingo"]


@dataclass
class ResumoHorario:
    campanha: str
    top_horas: list[tuple[int, int]]        # [(hora, conversoes), ...]
    top_dias_semana: list[tuple[str, int]]  # [(dia, conversoes), ...]
    pct_conversoes_fora_do_pico: float      # % de conversoes fora das top horas


def analisar_horarios(eventos: pd.DataFrame, top_n=3) -> list[ResumoHorario]:
    if eventos.empty:
        return []

    eventos = eventos.copy()
    eventos["DiaSemana"] = eventos["Data"].dt.weekday.map(lambda i: DIAS_SEMANA_PT[i])

    resumos = []
    for campanha, grupo in eventos.groupby("Campanha"):
        por_hora = grupo.groupby("Hora").size().sort_values(ascending=False)
        por_dia = grupo.groupby("DiaSemana").size().sort_values(ascending=False)

        top_horas = list(por_hora.head(top_n).items())
        top_dias = list(por_dia.head(top_n).items())

        total = len(grupo)
        conversoes_no_pico = por_hora.head(top_n).sum()
        pct_fora_do_pico = 100 * (1 - conversoes_no_pico / total) if total else 0.0

        resumos.append(ResumoHorario(
            campanha=campanha,
            top_horas=[(int(h), int(c)) for h, c in top_horas],
            top_dias_semana=[(d, int(c)) for d, c in top_dias],
            pct_conversoes_fora_do_pico=round(pct_fora_do_pico, 1),
        ))

    return resumos


def resumo_geral(eventos: pd.DataFrame, top_n=5) -> ResumoHorario:
    """Mesmo resumo, mas olhando todas as campanhas juntas - visão de conta."""
    if eventos.empty:
        return ResumoHorario("Todas as campanhas", [], [], 0.0)

    eventos = eventos.copy()
    eventos["DiaSemana"] = eventos["Data"].dt.weekday.map(lambda i: DIAS_SEMANA_PT[i])
    por_hora = eventos.groupby("Hora").size().sort_values(ascending=False)
    por_dia = eventos.groupby("DiaSemana").size().sort_values(ascending=False)

    total = len(eventos)
    conversoes_no_pico = por_hora.head(top_n).sum()
    pct_fora_do_pico = 100 * (1 - conversoes_no_pico / total) if total else 0.0

    return ResumoHorario(
        campanha="Todas as campanhas",
        top_horas=[(int(h), int(c)) for h, c in por_hora.head(top_n).items()],
        top_dias_semana=[(d, int(c)) for d, c in por_dia.head(top_n).items()],
        pct_conversoes_fora_do_pico=round(pct_fora_do_pico, 1),
    )
