from flask import Flask, render_template, url_for, make_response, Response, request, session, redirect, abort
from flask_socketio import SocketIO, join_room, leave_room
from flask_session import Session
import jinja2
from models.manageDB import query_products, insert_product, search_item, save_vendas
from models.manageDB import  query_users_login, get_sells_history, insert_user
from  models.manageDB import clear_tables_products
import json
import asyncio
import ssl
import  os
import  secrets
from cachelib import SimpleCache
from functools import wraps
from cachelib.file import FileSystemCache


# import webview
# import threading

# ------ SSL CORRETO ------
context_ssl = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
context_ssl.load_cert_chain(certfile="./SSL/cert.pem", keyfile="./SSL/privateKey.pem")
# --------------------------


def is_valid_image(path: str) -> bool:
    with open(path, "rb") as f:
        header = f.read(20)

    signatures = {
        b"\x89PNG\r\n\x1a\n": "PNG",
        b"\xFF\xD8": "JPEG",
        b"GIF87a": "GIF",
        b"GIF89a": "GIF",
        b"BM": "BMP",
        b"RIFF": "WEBP",  # precisa verificar mais bytes
        b"\x49\x49\x2A\x00": "TIFF",
        b"\x4D\x4D\x00\x2A": "TIFF",
        b"\x00\x00\x01\x00": "ICO",
    }

    # Checa assinaturas diretas
    for sig in signatures:
        if header.startswith(sig):
            return True
    # WEBP exige verificação extra (RIFF .... WEBP)
    if header.startswith(b"RIFF") and header[8:12] == b"WEBP":
        return True

    return False


app = Flask(__name__, static_folder='static', template_folder='templates',)


app.config.update(
    SECRET_KEY=secrets.token_urlsafe(192),
    SESSION_TYPE='cachelib',
    SESSION_CACHE_LIB=FileSystemCache('./flask_session'),
    SESSION_PERMANENT=True,
    SESSION_USE_SIGNER=True,
    SESSION_COOKIE_NAME='session',
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE='Lax',
)


Session(app)

socketio = SocketIO(app, cors_allowed_origins="*", async_mode="threading", async_handlers=True, max_http_buffer_size=500 * 1024 * 1024)




def role_required(*roles):
    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            user_role = session.get('user_role')

            if not user_role:
               #  abort(401)  # não autenticado
                return redirect(url_for('login'))

            if user_role not in roles:
               #  abort(403)  # sem permissão
                  return redirect(url_for('login'))

            return f(*args, **kwargs)
        return wrapper
    return decorator
 
 
# @app.before_request
# def require_login():
#     if request.endpoint in ('login', 'static'):
#         return
#     if 'user_id' not in session:
#         return redirect(url_for('login'))

   
@app.after_request
async def add_security_headers(response):
   response.headers['Server'] = 'PDV'
   response.headers['X-Content-Type-Options'] = 'nosniff'
   response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
   response.headers['Pragma'] = 'no-cache'
   response.headers['Expires'] = '0'
   response.headers['X-Frame-Options'] = 'SAMEORIGIN'
   response.headers['X-XSS-Protection'] = '1; mode=block'
   return response


@socketio.on('json_painel_event_load')
def handle_json_cardapio(data):
   session_id = data
   session['socket_id'] = session_id
   
   obj_json_burguer  = query_products()
   
   join_room(session['socket_id'])
   socketio.emit(event='json_painel_event_return_products', data=obj_json_burguer, to=session['socket_id'])
   # return obj_json_burguer

@socketio.on("send_img_stk")
def add_stock(data, buffer):
   json_obj = str(data).replace("'", '"')
   json_obj = json.loads(json_obj)
   name_file =  json_obj["filename"]
   caminho = os.path.join(r"static/imgs/stock", name_file)
   
   with open (caminho, "wb") as f:
      f.write(buffer)
      f.close()
   if not is_valid_image(caminho):
      os.remove(caminho)
   # print(" RECEBIDO ",   json_obj["filename"])
   
   
   # socketio.emit("sucess_record", "OK")
   
@socketio.on("send_products_to_stk")
def recive_products(data):
   json_obj = str(data).replace("'", '"')
   json_obj = json.loads(json_obj)
   data_prod = json_obj['data']
   
   
   name_produto = data_prod["nome"]
   descricao_breve = data_prod["breve"]
   imagem_produto =   data_prod["image_produto"]
   preco_produto = data_prod["preco"]
   categoria_produto = data_prod["categoria"]
   quantidade_item = data_prod["quantidade"]
   aviso_acabando =  data_prod["ps_pouco"]
   descricao_completa_produto = data_prod["descricao"]
   
   obj = insert_product(table="Produt",nome=name_produto,
                  descricao_breve=descricao_breve,
                  imagem=imagem_produto,
                  preco=preco_produto,
                  categoria=categoria_produto,
                  quantidade_prd=quantidade_item,
                  aviso_acabando=aviso_acabando,
                  desc_complete=descricao_completa_produto
               )
   
   socketio.emit("sucess_record",  "True", to=session['socket_id'])
   # clear_tables_products() 
   if not obj:
      socketio.emit("error_record", "error", to=session['socket_id'])
      
   # print(name_produto)
   # insert_product()
   
   # print("DATA", json_obj)

@socketio.on("end_sell")
def recive_products_sell(data: dict):
  
  
   def conte_itens(sacola: list) -> int:
     return [ item["id"] for item in sacola] 
   
   def calcate_total(sacola: list) -> float:
      total = 0.0
      for item in sacola:
         total += float(item["preco"])
      return total
   
   
   # print("Tipo:", type(data))
   sacola_ = data["sacola"]
   type_pay = data["typepay"]
   total_itens = len(sacola_)
   
   if not sacola_:
       socketio.emit("error_send_sell", "sacola vazia!!", to=session['socket_id'])
       return
    
   if not type(data) == dict:
      # (type(data)) 
      socketio.emit("error_send_sell", "envio de evento incorreto :) ", to=session['socket_id'])
      return 
   # if data:
   
   if not save_vendas(total_venda=calcate_total(sacola_),itens_venda=conte_itens(sacola_), quantidade_itens=total_itens, tipo_pagamento=type_pay, quem_vendeu=session['user_name']):
   # print(sacola_, data["typepay"])
      socketio.emit("error_send_sell", "Erro ao salvar venda!!", to=session['socket_id'])
      return
   socketio.emit("sucess_send_sell", "Venda Salva com Sucesso", to=session['socket_id'])
   socketio.emit("sucess_record",  "True", to=session['socket_id'])


@socketio.on("search_product")

def search_i(data):
   term = data["term"]
   result = search_item(str(term))
   socketio.emit("json_painel_event_return_products", result, to=session['socket_id'])
   

# pegar lista de vendas 
@socketio.on("get_sells_history")
def get_sells_history_r(data):
   data_inicial = None
   data_final = None
   result =  get_sells_history(data_inicial, data_final)
   print(session)
   socketio.emit("recive_seels_h", result)

  
@app.route('/')
@role_required('admin','vendedor')
def painel():
   s_r = session.get('user_role')
   response = make_response(render_template('painel.html', s_r=s_r))
   return response


@app.route('/services')
@role_required('admin','vendedor')
def services_():
   return make_response(render_template("servicos/Notas_de_servico.html"))


# pega os serviços - por data
@socketio.on('json_services_event_load')
def handle_json_services(data):
   pass


@app.route('/seels')
# @app.route('/json_cardapio')
@role_required('admin')
def get_seels():
   
   return make_response(render_template('historysells/seels.html'))


# @role_required('admin')
@app.route('/login')
def login():
   return make_response(render_template('usersTemplates/login.html'))


@app.route('/register')
@role_required('admin')
def register():
   return make_response(render_template('usersTemplates/register.html'))

@app.route('/auth', methods=['POST'])
def auth():
   user =  request.form.get('email')
   password = request.form.get('senha')
   q = query_users_login(user, password)
   if not q:
      print("Login inválido")
      return redirect(url_for('login'))
   
   session['user_role'] = str(q['role'])
   session['user_id'] = str(q['id'])
   session['user_name'] = str(q['user_name'])
   
   response = make_response("")
   response.headers['HX-Redirect'] = url_for('painel')
   return response

@app.route('/registe_ruser', methods=['POST'])
def register_user():
   # print("REGISTER USER", request.form)
   
   user =  request.form.get('user')
   password = request.form.get('senha')
   role_user = request.form.get('role')
   
   # insere no banco de dados
   try:
      q = insert_user(user, password, role_user)
   except Exception as err:
      print("Erro ao inserir usuário:", err)
   
   response = make_response("")
   response.headers['HX-Redirect'] = url_for('painel')
   return response

@app.route('/logout')
def logout():
   print(session.pop('user_id', None))
   # response = make_response("")
   return redirect(url_for('login'))

if __name__ == '__main__':
   # ssl_context=context_ssl
   # threading.Thread(target=socketio.run(app, debug=True, use_reloader=True, port=3000)).start()
   asyncio.run(socketio.run(app, debug=True, use_reloader=True, port=3000, ))

   # webview.create_window('GrelhosBurguer', app, frameless=False, easy_drag=True, min_size=(1400, 900))
   # asyncio.run(webview.start(http_server=True, private_mode=False, debug=True, http_port=3000), debug=True)
   
   
   