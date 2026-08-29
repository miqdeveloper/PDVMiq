from tinydb import TinyDB, Query
from datetime import datetime
from collections import Counter
import json

db_stock = TinyDB(r"./DataBaseJson/stock_db.json", indent=4)
db_vendas = TinyDB(r"./DataBaseJson/vendas_db.json", indent=4)
db_ordens = TinyDB(r"./DataBaseJson/ordens_db.json", indent=4)

def _safe_float(val) -> float:
    """Converte valores diversos (int, float, str com R$ ou vírgula) para float com segurança."""
    if isinstance(val, (int, float)):
        return float(val)
    if not val:
        return 0.0
    s = str(val).replace("R$", "").replace(" ", "").replace(",", ".")
    try:
        return float(s)
    except ValueError:
        return 0.0

def _safe_int(val) -> int:
    """Converte valores diversos para int com segurança."""
    if isinstance(val, int):
        return val
    try:
        return int(_safe_float(val))
    except (ValueError, TypeError):
        return 0

def _parse_date_key(d_str: str):
    """Converte string 'DD-MM-YYYY' em objeto datetime para ordenação cronológica real."""
    try:
        return datetime.strptime(d_str, "%d-%m-%Y")
    except (ValueError, TypeError):
        return datetime.min

def _parse_datetime_key(dt_str: str):
    """Converte string 'DD-MM-YYYY HH:MM:SS' em objeto datetime para ordenação."""
    try:
        return datetime.strptime(dt_str, "%d-%m-%Y %H:%M:%S")
    except (ValueError, TypeError):
        return datetime.min

def calculate_dashboard_metrics() -> dict:
    """
    Calcula todas as métricas gerenciais do sistema com validação rigorosa dos tipos.
    """
    table_vendas = db_vendas.table("sells_history").all()
    table_produtos = db_stock.table("Produtos").all()
    table_ordens = db_ordens.table("ordens_servico").all()

    hoje_str = datetime.now().strftime("%d-%m-%Y")

    # --- MÉTRICAS DE VENDAS ---
    total_vendas_qtd = len(table_vendas)
    faturamento_total = 0.0
    faturamento_hoje = 0.0
    vendas_hoje_qtd = 0

    faturamento_por_pagamento = {}
    vendas_por_vendedor = {}
    faturamento_por_data = {}
    itens_vendidos_counter = Counter()

    for venda in table_vendas:
        valor = _safe_float(venda.get("total_venda", 0))
        data_v = str(venda.get("data_venda", hoje_str)).strip()

        faturamento_total += valor

        if data_v == hoje_str:
            faturamento_hoje += valor
            vendas_hoje_qtd += 1

        # Agrupamento por data (para gráfico temporal de vendas)
        if data_v not in faturamento_por_data:
            faturamento_por_data[data_v] = 0.0
        faturamento_por_data[data_v] += valor

        # Por forma de pagamento
        tipo_pag = str(venda.get("tipo_pagamento", "OUTROS")).upper().strip()
        if tipo_pag not in faturamento_por_pagamento:
            faturamento_por_pagamento[tipo_pag] = {"total": 0.0, "qtd": 0}
        faturamento_por_pagamento[tipo_pag]["total"] += valor
        faturamento_por_pagamento[tipo_pag]["qtd"] += 1

        # Por vendedor
        vendedor = str(venda.get("quem_vendeu", "Desconhecido")).strip()
        if vendedor not in vendas_por_vendedor:
            vendas_por_vendedor[vendedor] = {"total": 0.0, "qtd": 0}
        vendas_por_vendedor[vendedor]["total"] += valor
        vendas_por_vendedor[vendedor]["qtd"] += 1

        # Contagem de itens vendidos
        for item_id in venda.get("itens_venda", []):
            itens_vendidos_counter[str(item_id)] += 1

    ticket_medio = (faturamento_total / total_vendas_qtd) if total_vendas_qtd > 0 else 0.0

    # Arredondar totais por pagamento e vendedor
    for k in faturamento_por_pagamento:
        faturamento_por_pagamento[k]["total"] = round(faturamento_por_pagamento[k]["total"], 2)
    for k in vendas_por_vendedor:
        vendas_por_vendedor[k]["total"] = round(vendas_por_vendedor[k]["total"], 2)

    # Ordenação cronológica REAL das datas para o gráfico de evolução
    datas_ordenadas = sorted(faturamento_por_data.keys(), key=_parse_date_key)
    datas_7_dias = datas_ordenadas[-7:] if len(datas_ordenadas) >= 7 else datas_ordenadas

    grafico_vendas_diarias = {
        "labels": datas_7_dias,
        "valores": [round(faturamento_por_data[d], 2) for d in datas_7_dias]
    }

    # Top produtos mais vendidos
    produtos_dict = {str(p.get("id")): p for p in table_produtos}
    top_produtos = []
    for pid, count in itens_vendidos_counter.most_common(5):
        p = produtos_dict.get(pid, {})
        top_produtos.append({
            "nome": p.get("nome", f"Produto #{pid[:6]}"),
            "qtd_vendida": count,
            "preco": _safe_float(p.get("preco", 0))
        })

    # --- MÉTRICAS DE ESTOQUE ---
    total_produtos_cadastrados = len(table_produtos)
    total_itens_estoque = 0
    valor_total_estoque = 0.0
    produtos_alerta_estoque = 0
    categorias_estoque = {}

    for prod in table_produtos:
        qtd = _safe_int(prod.get("quantidade_prd", 0))
        aviso = _safe_int(prod.get("aviso_acabando", 0))
        preco = _safe_float(prod.get("preco", 0))

        total_itens_estoque += qtd
        valor_total_estoque += (qtd * preco)

        if qtd <= aviso:
            produtos_alerta_estoque += 1

        cat = str(prod.get("categoria", "Geral")).capitalize().strip()
        if cat not in categorias_estoque:
            categorias_estoque[cat] = 0
        categorias_estoque[cat] += qtd

    # === MÉTRICAS DE NOTAS DE SERVIÇO ===
    valor_total_os = 0.0
    valor_os_hoje = 0.0
    os_com_valor = [os for os in table_ordens if os.get("valor")]

    for os in os_com_valor:
        valor = _safe_float(os.get("valor", 0))
        data_os = str(os.get("data_abertura", "")).split(" ")[0]
        valor_total_os += valor
        if data_os == hoje_str:
            valor_os_hoje += valor

    # Valor por tipo de serviço (se houver campo tipo)
    valor_por_tipo = {}
    for os in os_com_valor:
        tipo = str(os.get("tipo", "Serviço")).strip() or "Serviço"
        valor = _safe_float(os.get("valor", 0))
        if tipo not in valor_por_tipo:
            valor_por_tipo[tipo] = {"total": 0.0, "qtd": 0}
        valor_por_tipo[tipo]["total"] += valor
        valor_por_tipo[tipo]["qtd"] += 1

    for k in valor_por_tipo:
        valor_por_tipo[k]["total"] = round(valor_por_tipo[k]["total"], 2)

    # Ticket médio de OS
    ticket_medio_os = (valor_total_os / len(os_com_valor)) if os_com_valor else 0.0

    # === RECEITA POR TÉCNICO ===
    receita_por_tecnico = {}
    for os in os_com_valor:
        tecnico = str(os.get("quem_abriu", "Desconhecido")).strip()
        valor = _safe_float(os.get("valor", 0))
        if tecnico not in receita_por_tecnico:
            receita_por_tecnico[tecnico] = {"valor_total": 0.0, "qtd_os": 0}
        receita_por_tecnico[tecnico]["valor_total"] += valor
        receita_por_tecnico[tecnico]["qtd_os"] += 1
    for k in receita_por_tecnico:
        receita_por_tecnico[k]["valor_total"] = round(receita_por_tecnico[k]["valor_total"], 2)
        receita_por_tecnico[k]["ticket_medio"] = round(
            receita_por_tecnico[k]["valor_total"] / receita_por_tecnico[k]["qtd_os"], 2
        ) if receita_por_tecnico[k]["qtd_os"] > 0 else 0.0

    # === OS ESTAGNADAS (abertas há mais de 7 dias) ===
    os_estagnadas = []
    agora = datetime.now()
    for os in table_ordens:
        if os.get("status") == "aberta" and os.get("data_abertura"):
            try:
                dt_ab = _parse_datetime_key(os.get("data_abertura", ""))
                if dt_ab != datetime.min:
                    dias_aberta = (agora - dt_ab).days
                    if dias_aberta >= 7:
                        os_estagnadas.append({
                            "id": os.get("id", ""),
                            "cliente": os.get("cliente", ""),
                            "aparelho": os.get("aparelho", ""),
                            "tecnico": os.get("quem_abriu", ""),
                            "dias_aberta": dias_aberta,
                            "valor": _safe_float(os.get("valor", 0))
                        })
            except (ValueError, TypeError):
                pass
    os_estagnadas.sort(key=lambda x: x["dias_aberta"], reverse=True)

    # === TOP DEFEITOS/PROBLEMAS ===
    defeitos_counter = Counter()
    for os in table_ordens:
        defeito = str(os.get("defeito", "")).strip()
        if defeito and defeito.lower() not in ["", "não informado", "nao informado", "sem defeito"]:
            defeitos_counter[defeito] += 1
    top_defeitos = [{"defeito": k, "qtd": v} for k, v in defeitos_counter.most_common(10)]

    # === RECEITA OS POR MÊS (últimos 6 meses) ===
    receita_por_mes = {}
    for os in os_com_valor:
        data_os = str(os.get("data_abertura", "")).split(" ")[0]
        try:
            dt = _parse_date_key(data_os)
            if dt != datetime.min:
                mes_key = dt.strftime("%m-%Y")
                valor = _safe_float(os.get("valor", 0))
                if mes_key not in receita_por_mes:
                    receita_por_mes[mes_key] = 0.0
                receita_por_mes[mes_key] += valor
        except (ValueError, TypeError):
            pass
    # Ordenar e pegar últimos 6 meses
    meses_ordenados = sorted(receita_por_mes.keys(), key=lambda x: _parse_date_key("01-" + x))
    meses_6 = meses_ordenados[-6:] if len(meses_ordenados) >= 6 else meses_ordenados
    grafico_receita_mensal = {
        "labels": [datetime.strptime(m, "%m-%Y").strftime("%b/%Y") for m in meses_6],
        "valores": [round(receita_por_mes[m], 2) for m in meses_6]
    }

    # === COMPARATIVO MÊS ATUAL VS ANTERIOR ===
    mes_atual = datetime.now().strftime("%m-%Y")
    mes_anterior_dt = datetime.now().replace(day=1) - __import__('datetime').timedelta(days=1)
    mes_anterior = mes_anterior_dt.strftime("%m-%Y")
    receita_mes_atual = receita_por_mes.get(mes_atual, 0.0)
    receita_mes_anterior = receita_por_mes.get(mes_anterior, 0.0)
    variacao_mensal = 0.0
    if receita_mes_anterior > 0:
        variacao_mensal = ((receita_mes_atual - receita_mes_anterior) / receita_mes_anterior) * 100

    # === STATUS PAGAMENTO OS (se houver campo) ===
    os_pagas = 0
    os_pendentes = 0
    valor_recebido_os = 0.0
    valor_a_receber_os = 0.0
    for os in table_ordens:
        status_pag = str(os.get("status_pagamento", "pendente")).lower().strip()
        valor = _safe_float(os.get("valor", 0))
        if status_pag in ["pago", "recebido", "finalizado"]:
            os_pagas += 1
            valor_recebido_os += valor
        else:
            os_pendentes += 1
            valor_a_receber_os += valor

    # === MÉTRICAS DE ORDENS DE SERVIÇO (DETALHADAS) ===
    total_os = len(table_ordens)
    os_abertas = sum(1 for os in table_ordens if os.get("status") == "aberta")
    os_fechadas = sum(1 for os in table_ordens if os.get("status") == "fechada")
    taxa_conclusao_os = (os_fechadas / total_os * 100) if total_os > 0 else 0.0

    # OS por técnico (quem_abriu)
    os_por_tecnico = {}
    for os in table_ordens:
        tecnico = str(os.get("quem_abriu", "Desconhecido")).strip()
        if tecnico not in os_por_tecnico:
            os_por_tecnico[tecnico] = {"total": 0, "abertas": 0, "fechadas": 0}
        os_por_tecnico[tecnico]["total"] += 1
        if os.get("status") == "aberta":
            os_por_tecnico[tecnico]["abertas"] += 1
        elif os.get("status") == "fechada":
            os_por_tecnico[tecnico]["fechadas"] += 1

    # OS por data de abertura (últimos 7 dias)
    os_por_data = {}
    os_abertas_hoje = 0
    os_fechadas_hoje = 0
    for os in table_ordens:
        data_abertura = str(os.get("data_abertura", "")).split(" ")[0]  # Pega só a data
        if not data_abertura:
            continue
        if data_abertura not in os_por_data:
            os_por_data[data_abertura] = {"abertas": 0, "fechadas": 0, "total": 0}
        os_por_data[data_abertura]["total"] += 1
        if os.get("status") == "aberta":
            os_por_data[data_abertura]["abertas"] += 1
            if data_abertura == hoje_str:
                os_abertas_hoje += 1
        elif os.get("status") == "fechada":
            os_por_data[data_abertura]["fechadas"] += 1
            if data_abertura == hoje_str:
                os_fechadas_hoje += 1

    # Ordenar datas das OS para gráfico
    datas_os_ordenadas = sorted(os_por_data.keys(), key=_parse_date_key)
    datas_os_7 = datas_os_ordenadas[-7:] if len(datas_os_ordenadas) >= 7 else datas_os_ordenadas
    grafico_os_diarias = {
        "labels": datas_os_7,
        "abertas": [os_por_data[d]["abertas"] for d in datas_os_7],
        "fechadas": [os_por_data[d]["fechadas"] for d in datas_os_7],
        "total": [os_por_data[d]["total"] for d in datas_os_7]
    }

    # Tempo médio de conclusão (apenas OS fechadas com data_fechamento)
    tempos_conclusao = []
    for os in table_ordens:
        if os.get("status") == "fechada" and os.get("data_fechamento"):
            try:
                dt_ab = _parse_datetime_key(os.get("data_abertura", ""))
                dt_fech = _parse_datetime_key(os.get("data_fechamento", ""))
                if dt_ab != datetime.min and dt_fech != datetime.min:
                    diff_horas = (dt_fech - dt_ab).total_seconds() / 3600
                    if diff_horas >= 0:
                        tempos_conclusao.append(diff_horas)
            except (ValueError, TypeError):
                pass
    tempo_medio_conclusao = sum(tempos_conclusao) / len(tempos_conclusao) if tempos_conclusao else 0.0

    # Top aparelhos com mais OS
    aparelhos_counter = Counter()
    for os in table_ordens:
        aparelho = str(os.get("aparelho", "Não informado")).strip()
        if aparelho:
            aparelhos_counter[aparelho] += 1
    top_aparelhos = [{"aparelho": k, "qtd": v} for k, v in aparelhos_counter.most_common(5)]

    # Top clientes com mais OS
    clientes_counter = Counter()
    for os in table_ordens:
        cliente = str(os.get("cliente", "Não informado")).strip()
        if cliente:
            clientes_counter[cliente] += 1
    top_clientes = [{"cliente": k, "qtd": v} for k, v in clientes_counter.most_common(5)]

    # OS por status (para gráfico de pizza)
    os_por_status = {
        "aberta": os_abertas,
        "fechada": os_fechadas
    }

    return {
        "vendas": {
            "total_faturamento": round(faturamento_total, 2),
            "faturamento_hoje": round(faturamento_hoje, 2),
            "vendas_hoje_qtd": vendas_hoje_qtd,
            "total_vendas": total_vendas_qtd,
            "ticket_medio": round(ticket_medio, 2),
            "por_pagamento": faturamento_por_pagamento,
            "por_vendedor": vendas_por_vendedor,
            "grafico_diario": grafico_vendas_diarias,
            "top_produtos": top_produtos,
        },
        "estoque": {
            "total_produtos": total_produtos_cadastrados,
            "total_itens_fisicos": total_itens_estoque,
            "valor_total_estoque": round(valor_total_estoque, 2),
            "alerta_pouco_estoque": produtos_alerta_estoque,
            "por_categoria": categorias_estoque,
        },
        "ordens_servico": {
            "total": total_os,
            "abertas": os_abertas,
            "fechadas": os_fechadas,
            "abertas_hoje": os_abertas_hoje,
            "fechadas_hoje": os_fechadas_hoje,
            "taxa_conclusao": round(taxa_conclusao_os, 1),
            "tempo_medio_conclusao_horas": round(tempo_medio_conclusao, 1),
            "por_tecnico": os_por_tecnico,
            "grafico_diario": grafico_os_diarias,
            "por_status": os_por_status,
            "top_aparelhos": top_aparelhos,
            "top_clientes": top_clientes,
            "valor_total": round(valor_total_os, 2),
            "valor_hoje": round(valor_os_hoje, 2),
            "ticket_medio": round(ticket_medio_os, 2),
            "por_tipo": valor_por_tipo,
            "receita_por_tecnico": receita_por_tecnico,
            "os_estagnadas": os_estagnadas[:10],
            "top_defeitos": top_defeitos,
            "grafico_receita_mensal": grafico_receita_mensal,
            "receita_mes_atual": round(receita_mes_atual, 2),
            "receita_mes_anterior": round(receita_mes_anterior, 2),
            "variacao_mensal": round(variacao_mensal, 1),
            "os_pagas": os_pagas,
            "os_pendentes": os_pendentes,
            "valor_recebido": round(valor_recebido_os, 2),
            "valor_a_receber": round(valor_a_receber_os, 2),
        },
        "gerado_em": datetime.now().strftime("%d-%m-%Y %H:%M:%S")
    }

def get_dashboard_metrics_json() -> str:
    """Retorna as métricas formatadas em JSON."""
    return json.dumps(calculate_dashboard_metrics(), ensure_ascii=False)