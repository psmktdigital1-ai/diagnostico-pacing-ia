"""
Monta o diagnóstico diário em HTML, consolidando os três blocos (pacing,
detratores, horários) num único painel — a mesma ideia de parar de abrir três
planilhas separadas e olhar um resumo com a causa raiz já apontada.
"""
from datetime import date

from pacing import StatusPacing
from detratores import SkuDetrator
from horarios import ResumoHorario

STATUS_LABEL = {
    "on_pace": ("No ritmo", "#16a34a", "#f0fdf4", "#bbf7d0"),
    "underpacing": ("Abaixo do ritmo", "#b45309", "#fffbeb", "#fde68a"),
    "overpacing": ("Acima do ritmo", "#b91c1c", "#fef2f2", "#fecaca"),
}


def _fmt_moeda(v: float) -> str:
    return f"R$ {v:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def _bloco_pacing(status_list: list[StatusPacing]) -> str:
    linhas = []
    for s in status_list:
        label, cor, bg, borda = STATUS_LABEL[s.status]
        alerta_parada = (
            f"<div style='margin-top:4px;font-size:0.8rem;color:#b91c1c'>"
            f"⚠ sem investimento há {s.dias_sem_investimento} dias</div>"
            if s.alerta_parada else ""
        )
        linhas.append(f"""
        <tr>
          <td style="padding:10px 12px;border-bottom:1px solid #eee">
            <div style="font-weight:600">{s.campanha}</div>
            {alerta_parada}
          </td>
          <td style="padding:10px 12px;border-bottom:1px solid #eee;text-align:right;white-space:nowrap">{_fmt_moeda(s.investido_acumulado)}</td>
          <td style="padding:10px 12px;border-bottom:1px solid #eee;text-align:right">{s.pct_investido}%</td>
          <td style="padding:10px 12px;border-bottom:1px solid #eee;text-align:right">{s.pct_esperado}%</td>
          <td style="padding:10px 12px;border-bottom:1px solid #eee;text-align:right">{_fmt_moeda(s.estimativa_fim_mes)}</td>
          <td style="padding:10px 12px;border-bottom:1px solid #eee;text-align:center">
            <span style="background:{bg};color:{cor};border:1px solid {borda};border-radius:999px;padding:3px 10px;font-size:0.78rem;font-weight:600">{label}</span>
          </td>
        </tr>""")

    return f"""
    <h2 style="font-size:1.05rem;margin:28px 0 10px">1. Pacing por campanha</h2>
    <table style="width:100%;border-collapse:collapse;font-size:0.88rem">
      <thead>
        <tr style="background:#f4f4f5;text-align:right">
          <th style="padding:8px 12px;text-align:left">Campanha</th>
          <th style="padding:8px 12px">Investido</th>
          <th style="padding:8px 12px">% do mês</th>
          <th style="padding:8px 12px">% esperado</th>
          <th style="padding:8px 12px">Estimativa fim do mês</th>
          <th style="padding:8px 12px;text-align:center">Status</th>
        </tr>
      </thead>
      <tbody>{"".join(linhas)}</tbody>
    </table>
    <div style="font-size:0.78rem;color:#71717a;margin-top:6px">
      Regra de distribuição: 65% do orçamento entre os dias 1–15, 35% entre os dias 16–30. Tolerância de ±10 p.p. antes de virar alerta.
    </div>"""


def _bloco_detratores(detratores: list[SkuDetrator]) -> str:
    if not detratores:
        return """
        <h2 style="font-size:1.05rem;margin:28px 0 10px">2. Produtos detratores</h2>
        <div style="font-size:0.9rem;color:#3f6212">Nenhum SKU detrator relevante identificado no período.</div>"""

    linhas = []
    for d in detratores[:10]:
        linhas.append(f"""
        <tr>
          <td style="padding:8px 12px;border-bottom:1px solid #eee">{d.campanha}</td>
          <td style="padding:8px 12px;border-bottom:1px solid #eee">{d.sku}</td>
          <td style="padding:8px 12px;border-bottom:1px solid #eee;text-align:right">{_fmt_moeda(d.investimento)}</td>
          <td style="padding:8px 12px;border-bottom:1px solid #eee;text-align:right;color:#b91c1c">{d.roas_sku}x</td>
          <td style="padding:8px 12px;border-bottom:1px solid #eee;text-align:right">{d.roas_campanha}x</td>
          <td style="padding:8px 12px;border-bottom:1px solid #eee;text-align:right">{_fmt_moeda(d.receita_perdida_estimada)}</td>
        </tr>""")

    return f"""
    <h2 style="font-size:1.05rem;margin:28px 0 10px">2. Produtos detratores</h2>
    <table style="width:100%;border-collapse:collapse;font-size:0.88rem">
      <thead>
        <tr style="background:#f4f4f5">
          <th style="padding:8px 12px;text-align:left">Campanha</th>
          <th style="padding:8px 12px;text-align:left">SKU</th>
          <th style="padding:8px 12px;text-align:right">Investimento</th>
          <th style="padding:8px 12px;text-align:right">ROAS do SKU</th>
          <th style="padding:8px 12px;text-align:right">ROAS da campanha</th>
          <th style="padding:8px 12px;text-align:right">Receita perdida (est.)</th>
        </tr>
      </thead>
      <tbody>{"".join(linhas)}</tbody>
    </table>
    <div style="font-size:0.78rem;color:#71717a;margin-top:6px">
      "Receita perdida (est.)" = quanto o SKU teria gerado a mais se performasse no ROAS médio da própria campanha. É uma estimativa didática, não uma medição de incrementalidade.
    </div>"""


def _bloco_horarios(resumo_geral, resumos_por_campanha) -> str:
    def _fmt_lista(pares, sufixo=""):
        return ", ".join(f"{p[0]}{sufixo} ({p[1]})" for p in pares)

    linhas_camp = "".join(f"""
        <tr>
          <td style="padding:8px 12px;border-bottom:1px solid #eee">{r.campanha}</td>
          <td style="padding:8px 12px;border-bottom:1px solid #eee">{_fmt_lista(r.top_horas, 'h')}</td>
          <td style="padding:8px 12px;border-bottom:1px solid #eee">{_fmt_lista(r.top_dias_semana)}</td>
        </tr>""" for r in resumos_por_campanha)

    return f"""
    <h2 style="font-size:1.05rem;margin:28px 0 10px">3. Conversões por horário</h2>
    <div style="font-size:0.9rem;margin-bottom:10px">
      <strong>Geral:</strong> horários com mais conversão: {_fmt_lista(resumo_geral.top_horas, 'h')}.
      Dias da semana com mais conversão: {_fmt_lista(resumo_geral.top_dias_semana)}.
    </div>
    <table style="width:100%;border-collapse:collapse;font-size:0.85rem">
      <thead>
        <tr style="background:#f4f4f5">
          <th style="padding:8px 12px;text-align:left">Campanha</th>
          <th style="padding:8px 12px;text-align:left">Top horários</th>
          <th style="padding:8px 12px;text-align:left">Top dias da semana</th>
        </tr>
      </thead>
      <tbody>{linhas_camp}</tbody>
    </table>"""


def montar_html(status_pacing, detratores, resumo_geral_horario, resumos_horario_campanha,
                 data_referencia: date) -> str:
    return f"""<!DOCTYPE html>
<html lang="pt-BR">
<head><meta charset="utf-8"></head>
<body style="margin:0;padding:0;background:#f4f4f5;font-family:Arial,Helvetica,sans-serif;color:#18181b">
  <div style="max-width:820px;margin:0 auto;padding:24px 20px">
    <div style="background:#ffffff;border-radius:14px;padding:28px 26px;border:1px solid #e4e4e7">
      <div style="font-size:0.8rem;color:#71717a;text-transform:uppercase;letter-spacing:0.05em;margin-bottom:4px">Diagnóstico diário de mídia paga</div>
      <div style="font-size:1.4rem;font-weight:700;margin-bottom:4px">{data_referencia.strftime('%d/%m/%Y')}</div>
      <div style="font-size:0.85rem;color:#71717a;margin-bottom:8px">Pacing · produtos detratores · horário de conversão, num único painel.</div>

      {_bloco_pacing(status_pacing)}
      {_bloco_detratores(detratores)}
      {_bloco_horarios(resumo_geral_horario, resumos_horario_campanha)}

      <div style="font-size:0.72rem;color:#a1a1aa;margin-top:24px">
        Gerado a partir de dados sintéticos de demonstração (dados.py). Para uso com dados reais, troque o carregador pelo export da sua plataforma — ver README.
      </div>
    </div>
  </div>
</body>
</html>
"""
