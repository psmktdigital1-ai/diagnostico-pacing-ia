"""
Orquestra o diagnóstico diário: carrega dados -> avalia pacing -> identifica
detratores -> analisa horário de conversão -> monta HTML -> salva em disco.

Rodar: python3 main.py
"""
import os
from datetime import datetime

from dados import carregar_dados, orcamento_mensal, CAMPANHAS
from pacing import avaliar_pacing
from detratores import identificar_detratores
from horarios import analisar_horarios, resumo_geral
from relatorio import montar_html

DIA_ATUAL = 24  # dia do mês simulado como "hoje" — mude para testar outros cenários


def main():
    print(f"1/5 Gerando dados sintéticos até o dia {DIA_ATUAL}...")
    diario, eventos = carregar_dados(dia_atual=DIA_ATUAL)
    data_referencia = diario["Data"].max()
    print(f"    {len(diario)} linhas diárias, {len(eventos)} conversões simuladas")

    print("2/5 Avaliando pacing por campanha...")
    orcamentos = {c["campanha"]: orcamento_mensal(c["campanha"]) for c in CAMPANHAS}
    status_pacing = avaliar_pacing(diario, orcamentos, dia_atual=DIA_ATUAL, data_referencia=data_referencia)
    for s in status_pacing:
        alerta = " [SEM MOVIMENTAÇÃO]" if s.alerta_parada else ""
        print(f"    {s.campanha}: {s.pct_investido}% investido (esperado {s.pct_esperado}%) — {s.status}{alerta}")

    print("3/5 Identificando produtos detratores...")
    detratores = identificar_detratores(diario)
    print(f"    {len(detratores)} SKU(s) detrator(es) identificado(s)")

    print("4/5 Analisando conversões por horário...")
    resumo_horario_geral = resumo_geral(eventos)
    resumos_horario_campanha = analisar_horarios(eventos)

    print("5/5 Montando relatório HTML...")
    html = montar_html(status_pacing, detratores, resumo_horario_geral, resumos_horario_campanha,
                        data_referencia=data_referencia.date())

    os.makedirs("saida", exist_ok=True)
    nome_arquivo = f"saida/diagnostico_{datetime.now().strftime('%Y-%m-%d_%H%M')}.html"
    with open(nome_arquivo, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"    Relatório salvo em {nome_arquivo}")


if __name__ == "__main__":
    main()
