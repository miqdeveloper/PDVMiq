from tinydb import TinyDB, Query
import uuid
import random
import json
import re
from datetime import datetime
# import datetime

db = TinyDB(r"./DataBaseJson/stock_db.json", indent=4)
db_vendas = TinyDB(r"./DataBaseJson/vendas_db.json", indent=4)
db_users = TinyDB(r"./DataBaseJson/users_db.json", indent=4)
db_ordens = TinyDB(r"./DataBaseJson/ordens_db.json", indent=4)


def format_date(date_str: str) -> str:
    """
    Formata uma string de data 'DD-MM-YYYY' para um objeto datetime.
    """
    try:
        return datetime.strptime(date_str, "%d-%m-%Y")
    except ValueError:
        print(f"Data inválida: {date_str}")
        return None
        

    
def subtract_stock(product_id: str, quantity: int) -> bool:
    """
    Subtrai a quantidade especificada do estoque do produto com o ID fornecido.
    Retorna True se a operação for bem-sucedida, False caso contrário.
    """
    product_table = db.table("Produtos")
    Product_q = Query()

    try:
        product = product_table.get(Product_q.id == product_id)

        if product is None:
            print(f"Produto com ID {product_id} não encontrado.")
            return False

        new_quantity = int(product["quantidade_prd"]) - quantity

        if new_quantity < 0:
            print(
                f"Quantidade insuficiente em estoque para o produto {product['nome']}."
            )
            return False

        product_table.update(
            {"quantidade_prd": str(new_quantity)}, Product_q.id == product_id
        )
        return True

    except Exception as err:
        print(f"Erro ao atualizar o estoque: {err}")
        return False


def query_products():
    product_tb = db.table("Produtos")
    obj_json = json.dumps(product_tb.all(), ensure_ascii=False)

    return obj_json


# print(query_products())


def insert_product(
    table,
    nome,
    descricao_breve,
    preco,
    aviso_acabando,
    imagem,
    categoria,
    desc_complete,
    quantidade_prd,
):

    table_produtos = db.table("Produtos")
    try:
        table_produtos.insert(
            {
                "id": uuid.uuid4().hex,
                "nome": nome,
                "descricao_breve": descricao_breve,
                "preco": preco,
                "aviso_acabando": aviso_acabando,
                "imagem": imagem,
                "categoria": categoria,
                "descricao_completa": desc_complete,
                "quantidade_prd": quantidade_prd,
            }
        )

        return True
    except Exception as err:
        print(f"Erro ao gravar no banco {err}")
        return False


def clear_tables_products():
    db_ = db.table("Produtos")
    db_.truncate()


# clear_tables_products()
def search_item(term):
    Produto_q = Query()

    db_t = db.table("Produtos")
    normalized = term.strip().lower()
    # print(normalized)# remove espaços extras + minúsculas
    results = db_t.search(
        Produto_q.nome.matches(f".*{re.escape(term)}.*", flags=re.IGNORECASE)
    )
    return results


def get_os_table():
    return db_ordens.table("ordens_servico")


def list_ordens_servico():
    return get_os_table().all()


def query_json_ordens():
    """Retorna todas as ordens de serviço como JSON string (para o frontend)."""
    return json.dumps(get_os_table().all(), ensure_ascii=False)


def count_ordens_abertas():
    return len(get_os_table().search(Query().status == "aberta"))


def count_ordens_fechadas():
    return len(get_os_table().search(Query().status == "fechada"))


def insert_servico(cliente, telefone, aparelho, problema, observacoes, quem_abriu):
    table = get_os_table()
    try:
        table.insert({
            "id": uuid.uuid4().hex,
            "cliente": cliente,
            "telefone": telefone,
            "aparelho": aparelho,
            "problema": problema,
            "observacoes": observacoes,
            "status": "aberta",
            "quem_abriu": quem_abriu,
            "data_abertura": datetime.now().strftime("%d-%m-%Y %H:%M:%S"),
            "data_fechamento": None,
        })
        return True
    except Exception as err:
        print(f"Erro ao gravar ordem de servico: {err}")
        return False


def get_servico(os_id):
    table = get_os_table()
    Os_q = Query()
    result = table.get(Os_q.id == os_id)
    if result:
        return result
    return None


def update_servico(os_id, **fields):
    table = get_os_table()
    Os_q = Query()
    result = table.get(Os_q.id == os_id)
    if not result:
        return False
    try:
        table.update(fields, Os_q.id == os_id)
        return True
    except Exception as err:
        print(f"Erro ao atualizar ordem de servico: {err}")
        return False


def alterar_status_servico(os_id, status):
    data_fechamento = datetime.now().strftime("%d-%m-%Y %H:%M:%S") if status == "fechada" else None
    return update_servico(os_id, status=status, data_fechamento=data_fechamento)


def toggle_status_servico(os_id):
    servico = get_servico(os_id)
    if not servico:
        return False
    novo_status = "fechada" if servico["status"] == "aberta" else "aberta"
    return alterar_status_servico(os_id, novo_status)


def delete_servico(os_id):
    table = get_os_table()
    Os_q = Query()
    try:
        table.remove(Os_q.id == os_id)
        return True
    except Exception as err:
        print(f"Erro ao remover ordem de servico: {err}")
        return False


def query_services():
    """Lista de serviços (compatiblidade legada) - retorna todas as ordens."""
    return list_ordens_servico()


def save_vendas(
    total_venda: float,
    quantidade_itens: int,
    itens_venda: list,
    tipo_pagamento: str,
    quem_vendeu: str,
    data_venda: str | None = None,
    hora_venda: str | None = None,
) -> bool:
    """
    Salva uma venda no histórico e atualiza o estoque de forma atômica.
    """
    from collections import Counter

    db_vendas_s_table = db_vendas.table("sells_history")
    product_table = db.table("Produtos")
    Product_q = Query()

    now = datetime.now()
    if data_venda is None:
        data_venda = now.strftime("%d-%m-%Y")
    if hora_venda is None:
        hora_venda = now.strftime("%H:%M:%S")

    try:
        # 1. Valida se o estoque é suficiente para TODOS os itens antes de alterar algo
        counts = Counter(itens_venda)
        for pid, qty in counts.items():
            prod = product_table.get(Product_q.id == pid)
            if not prod:
                print(f"Produto {pid} não encontrado no estoque.")
                return False
            qtd_atual = int(prod.get("quantidade_prd", 0))
            if qtd_atual < qty:
                print(f"Estoque insuficiente para {prod.get('nome')}: necessário {qty}, disponível {qtd_atual}.")
                return False

        # 2. Abate do estoque
        for pid, qty in counts.items():
            prod = product_table.get(Product_q.id == pid)
            nova_qtd = int(prod.get("quantidade_prd", 0)) - qty
            product_table.update({"quantidade_prd": str(nova_qtd)}, Product_q.id == pid)

        # 3. Registra a venda
        db_vendas_s_table.insert(
            {
                "id": uuid.uuid4().hex,
                "total_venda": float(total_venda),
                "quantidade_itens": int(quantidade_itens),
                "itens_venda": list(itens_venda),
                "tipo_pagamento": str(tipo_pagamento),
                "data_venda": data_venda,
                "hora_venda": hora_venda,
                "quem_vendeu": str(quem_vendeu),
            }
        )

        return True

    except Exception as err:
        print(f"Erro ao salvar venda: {err}")
        return False


#  pegar historico de vendas
def get_sells_history(data_str: str | None = None, data_final: str | None = None ):
    db_vendas_s_table = db_vendas.table("sells_history")
    
    
    dt_inicio = format_date(data_str) if data_str else None
    dt_fim = format_date(data_final) if data_final else None

    filtered = []
    if not dt_inicio and not dt_fim:
        return db_vendas_s_table.all()

    for venda in db_vendas_s_table.all():
        # converte data da venda para datetime
        dt_venda = datetime.strptime(venda["data_venda"], "%d-%m-%Y")

        if dt_inicio and dt_fim:
            if dt_inicio <= dt_venda <= dt_fim:
                filtered.append(venda)
        elif dt_inicio:
            if dt_venda == dt_inicio:
                filtered.append(venda)
        else:
            filtered.append(venda)

    return filtered
    # return db_vendas_s_table.all()
    # return filter_by_date(data_str, data_final)

# print(get_sells_history())
# manage USERS


def insert_user(username: str, password: str, role: str) -> bool:
    table_users = db_users.table("users")
    db_query = Query()

    result = table_users.search(db_query.username == username)

    if result:
        return False

    try:
        table_users.insert(
            {
                "id": uuid.uuid4().hex,
                "username": username,
                "password": password,
                "role": role,
            }
        )

        return True
    except Exception as err:
        print(f"Erro ao gravar no banco {err}")
        return False


def query_users_login(user: str, password: str) -> bool:
    users_tb = db_users.table("users")
    User_q = Query()

    try:
        result = users_tb.search(
            (User_q.username == user) & (User_q.password == password)
        )

        if result:
            # print("Usuário encontrado:", result[0]['role'])
            return {"role": result[0]["role"], "id": result[0]["id"], "user_name": result[0]["username"]}
        else:
            return False
    except Exception as err:
        print(f"Erro ao consultar usuário: {err}")
        return False
