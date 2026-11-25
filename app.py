from datetime import datetime, timedelta, timezone
import json
import os
from functools import wraps
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError
from flask import (
    Flask,
    render_template,
    request,
    redirect,
    url_for,
    session,
    flash,
)
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "bomburgao-chave-local-trocar-em-prod")

DATA_FILE = os.environ.get("DATA_FILE", "cardapio_data.json")
ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "bomburgao123")

# Pasta onde ficam as fotos enviadas pelo admin
UPLOAD_FOLDER = os.environ.get("UPLOAD_FOLDER", os.path.join("static", "uploads"))
ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "webp", "gif"}
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
app.config["MAX_CONTENT_LENGTH"] = 6 * 1024 * 1024  # 6 MB

DEFAULT_LOJA = {
    "nome": "BOMBURGÃO",
    "slogan": "O melhor Bomburgão da cidade!",
    "horario_texto": "Terça a Domingo • 18:30 às 00:00",
    "instagram": "@LANCHESBOMBURGAO",
    "whatsapp": os.environ.get("WHATSAPP_LOJA", "5531984246779"),
    "taxa_entrega_padrao": float(os.environ.get("TAXA_ENTREGA", "5.00")),
    "foto_lateral_esq": "side-left.png",
    "foto_lateral_dir": "side-right.png",
}

DEFAULT_CARDAPIO = [
    # DESTAQUES
    {
        "id": 14,
        "numero": "14",
        "categoria": "Destaques",
        "nome": "X-Picanha",
        "preco": 20.50,
        "imagem": "burger-destaque.png",
        "ativo": True,
        "descricao": "Pão, carne de picanha 120g, bacon, presunto, queijo, ovo, alface, tomate, batata palha",
    },
    {
        "id": 13,
        "numero": "13",
        "categoria": "Destaques",
        "nome": "Bomburguer",
        "preco": 33.00,
        "imagem": "burger-classico.png",
        "ativo": True,
        "descricao": "2 pães, 2 carnes, 2 ovos, 2 queijos, 2 presuntos, bacon, milho, frango com catupiry, alface, tomate, batata palha",
    },
    {
        "id": 18,
        "numero": "18",
        "categoria": "Destaques",
        "nome": "Macarrão na Chapa",
        "preco": 25.00,
        "imagem": "macarrao.png",
        "ativo": True,
        "descricao": "Macarrão, bacon, frango, linguiça calabresa, pernil, pimentão, cebola, muçarela e molho shoyo",
    },
    {
        "id": 17,
        "numero": "17",
        "categoria": "Destaques",
        "nome": "Omelete",
        "preco": 22.00,
        "imagem": "omelete.png",
        "ativo": True,
        "descricao": "Ovo, bacon, frango desfiado, Catupiry, presunto, muçarela, cebola e pimentão",
    },
    # LANCHES (01 a 16 com imagem única; 17 e 18 com as imagens já salvas)
    {
        "id": 1,
        "numero": "01",
        "categoria": "Lanches",
        "nome": "Misto Quente",
        "preco": 10.00,
        "imagem": "burger-padrao.png",
        "ativo": True,
        "descricao": "Pão de hambúrguer, presunto e muçarela",
    },
    {
        "id": 2,
        "numero": "02",
        "categoria": "Lanches",
        "nome": "Misto Quente Especial",
        "preco": 13.00,
        "imagem": "burger-padrao.png",
        "ativo": True,
        "descricao": "Pão de hambúrguer, bacon, ovo, presunto e muçarela",
    },
    {
        "id": 3,
        "numero": "03",
        "categoria": "Lanches",
        "nome": "Hambúrguer Especial",
        "preco": 12.00,
        "imagem": "burger-padrao.png",
        "ativo": True,
        "descricao": "Pão, carne, alface, tomate, milho, batata palha",
    },
    {
        "id": 4,
        "numero": "04",
        "categoria": "Lanches",
        "nome": "X-Burguer",
        "preco": 13.00,
        "imagem": "burger-padrao.png",
        "ativo": True,
        "descricao": "Pão, carne, queijo, alface, tomate, batata palha",
    },
    {
        "id": 5,
        "numero": "05",
        "categoria": "Lanches",
        "nome": "X-Burguer Egg",
        "preco": 14.50,
        "imagem": "burger-padrao.png",
        "ativo": True,
        "descricao": "Pão, carne, queijo, ovo, alface, tomate, batata palha",
    },
    {
        "id": 6,
        "numero": "06",
        "categoria": "Lanches",
        "nome": "X-Bacon",
        "preco": 16.50,
        "imagem": "burger-padrao.png",
        "ativo": True,
        "descricao": "Pão, carne, queijo, bacon, alface, tomate, batata palha",
    },
    {
        "id": 7,
        "numero": "07",
        "categoria": "Lanches",
        "nome": "X-Bacon Egg",
        "preco": 17.50,
        "imagem": "burger-padrao.png",
        "ativo": True,
        "descricao": "Pão, carne, queijo, bacon, ovo, alface, tomate, batata palha",
    },
    {
        "id": 8,
        "numero": "08",
        "categoria": "Lanches",
        "nome": "Kokó Bacon",
        "preco": 18.50,
        "imagem": "burger-padrao.png",
        "ativo": True,
        "descricao": "Pão, frango desfiado, catupiry, bacon, alface, tomate",
    },
    {
        "id": 9,
        "numero": "09",
        "categoria": "Lanches",
        "nome": "Kokó Catupiry",
        "preco": 17.00,
        "imagem": "burger-padrao.png",
        "ativo": True,
        "descricao": "Pão, frango desfiado, catupiry, milho, alface, tomate",
    },
    {
        "id": 10,
        "numero": "10",
        "categoria": "Lanches",
        "nome": "Hawaiano",
        "preco": 17.00,
        "imagem": "burger-padrao.png",
        "ativo": True,
        "descricao": "Pão, carne, presunto, banana, queijo, alface, batata palha, tomate",
    },
    {
        "id": 11,
        "numero": "11",
        "categoria": "Lanches",
        "nome": "Laçador",
        "preco": 20.00,
        "imagem": "burger-padrao.png",
        "ativo": True,
        "descricao": "Pão, 2 carnes, ovo, bacon, queijo, milho, alface, tomate",
    },
    {
        "id": 12,
        "numero": "12",
        "categoria": "Lanches",
        "nome": "X-Tudo",
        "preco": 22.00,
        "imagem": "burger-padrao.png",
        "ativo": True,
        "descricao": "Pão, carne, frango desfiado, bacon, ovo, presunto, queijo, alface, tomate, milho, batata palha, catupiry",
    },
    {
        "id": 13,
        "numero": "13",
        "categoria": "Lanches",
        "nome": "Bomburguer",
        "preco": 33.00,
        "imagem": "burger-padrao.png",
        "ativo": True,
        "descricao": "2 pães, 2 carnes, 2 ovos, 2 queijos, 2 presuntos, bacon, milho, frango com catupiry, alface, tomate, batata palha",
    },
    {
        "id": 14,
        "numero": "14",
        "categoria": "Lanches",
        "nome": "X-Picanha",
        "preco": 20.50,
        "imagem": "burger-padrao.png",
        "ativo": True,
        "descricao": "Pão, carne de picanha 120g, bacon, presunto, queijo, ovo, alface, tomate, batata palha",
    },
    {
        "id": 15,
        "numero": "15",
        "categoria": "Lanches",
        "nome": "Bomburgão",
        "preco": 37.00,
        "imagem": "burger-padrao.png",
        "ativo": True,
        "descricao": "2 pães, 2 carnes de picanha 120g, 2 ovos, 2 queijos, 2 presuntos, bacon, milho, frango com catupiry, alface, tomate, batata palha",
    },
    {
        "id": 16,
        "numero": "16",
        "categoria": "Lanches",
        "nome": "Tropical",
        "preco": 17.00,
        "imagem": "burger-padrao.png",
        "ativo": True,
        "descricao": "Pão, carne, presunto, abacaxi, queijo, alface, batata palha, tomate",
    },
    {
        "id": 17,
        "numero": "17",
        "categoria": "Lanches",
        "nome": "Omelete",
        "preco": 22.00,
        "imagem": "omelete.png",
        "ativo": True,
        "descricao": "Ovo, bacon, frango desfiado, Catupiry, presunto, muçarela, cebola e pimentão",
    },
    {
        "id": 18,
        "numero": "18",
        "categoria": "Lanches",
        "nome": "Macarrão na Chapa",
        "preco": 25.00,
        "imagem": "macarrao.png",
        "ativo": True,
        "descricao": "Macarrão, bacon, frango, linguiça calabresa, pernil, pimentão, cebola, muçarela e molho shoyo",
    },
    # BEBIDAS
    {
        "id": 101,
        "numero": "",
        "categoria": "Bebidas",
        "nome": "Refrigerante Lata",
        "preco": 5.00,
        "imagem": "",
        "ativo": True,
        "descricao": "Lata 350ml",
    },
    {
        "id": 102,
        "numero": "",
        "categoria": "Bebidas",
        "nome": "Refrigerante 600ml",
        "preco": 7.00,
        "imagem": "",
        "ativo": True,
        "descricao": "Garrafa 600ml",
    },
    {
        "id": 103,
        "numero": "",
        "categoria": "Bebidas",
        "nome": "Refrigerante 1L",
        "preco": 8.00,
        "imagem": "",
        "ativo": True,
        "descricao": "Garrafa 1 Litro",
    },
    {
        "id": 104,
        "numero": "",
        "categoria": "Bebidas",
        "nome": "Refrigerante Mate Couro",
        "preco": 10.00,
        "imagem": "",
        "ativo": True,
        "descricao": "Garrafa tradicional",
    },
    {
        "id": 105,
        "numero": "",
        "categoria": "Bebidas",
        "nome": "Refrigerante 2L (Fanta / Guaraná / Sprite)",
        "preco": 12.00,
        "imagem": "",
        "ativo": True,
        "descricao": "Informe o sabor desejado nas observações (Fanta, Guaraná ou Sprite)",
    },
    {
        "id": 106,
        "numero": "",
        "categoria": "Bebidas",
        "nome": "Refrigerante Coca-Cola",
        "preco": 15.00,
        "imagem": "",
        "ativo": True,
        "descricao": "Garrafa Coca-Cola",
    },
]

ADICIONAIS = [
    {"nome": "Bacon Extra", "preco": 4.00},
    {"nome": "Catupiry Extra", "preco": 3.50},
    {"nome": "Ovo Extra", "preco": 2.00},
    {"nome": "Queijo Extra", "preco": 3.00},
    {"nome": "Hambúrguer Tradicional Extra", "preco": 5.00},
]


def arquivo_permitido(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


def resolver_url_imagem(imagem):
    if not imagem:
        return ""
    if imagem.startswith("uploads/"):
        nome_arq = imagem.split("/", 1)[1]
        # Se UPLOAD_FOLDER estiver dentro de static/, usa static/<UPLOAD_FOLDER_REL>/<nome_arq>
        pasta_rel = app.config["UPLOAD_FOLDER"].replace("\\", "/")
        if pasta_rel.startswith("static/"):
            subpasta = pasta_rel[len("static/"):].strip("/")
            return url_for("static", filename=f"{subpasta}/{nome_arq}")
        return url_for("static", filename=f"uploads/{nome_arq}")
    return url_for("static", filename=f"img/{imagem}")


def carregar_dados():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            loja = {**DEFAULT_LOJA, **data.get("loja", {})}
            if not os.environ.get("WHATSAPP_LOJA"):
                loja["whatsapp"] = data.get("loja", {}).get("whatsapp", DEFAULT_LOJA["whatsapp"])
            else:
                loja["whatsapp"] = os.environ["WHATSAPP_LOJA"]

            if os.environ.get("TAXA_ENTREGA"):
                loja["taxa_entrega_padrao"] = float(os.environ["TAXA_ENTREGA"])

            cardapio = data.get("cardapio", DEFAULT_CARDAPIO)
            for item in cardapio:
                item.setdefault("ativo", True)
                item.setdefault("imagem", "")
            return loja, cardapio

    loja_inicial = dict(DEFAULT_LOJA)
    cardapio_inicial = [dict(i) for i in DEFAULT_CARDAPIO]
    salvar_dados(loja_inicial, cardapio_inicial)
    return loja_inicial, cardapio_inicial


def salvar_dados(loja, cardapio):
    pasta = os.path.dirname(DATA_FILE)
    if pasta:
        os.makedirs(pasta, exist_ok=True)
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump({"loja": loja, "cardapio": cardapio}, f, ensure_ascii=False, indent=2)


def obter_status_loja():
    try:
        tz = ZoneInfo("America/Sao_Paulo")
    except ZoneInfoNotFoundError:
        tz = timezone(timedelta(hours=-3))

    agora = datetime.now(tz)
    # weekday(): 0=Segunda, 1=Terça ... 6=Domingo
    dia_valido = agora.weekday() in (1, 2, 3, 4, 5, 6)
    minutos_atuais = agora.hour * 60 + agora.minute
    dentro_horario = minutos_atuais >= (18 * 60 + 30)

    if dia_valido and dentro_horario:
        return {
            "aberto": True,
            "texto": "ABERTO AGORA",
            "detalhe": "Terça a Domingo • 18:30 às 00:00",
        }
    return {
        "aberto": False,
        "texto": "FECHADO NO MOMENTO",
        "detalhe": "Abre Terça a Domingo às 18:30",
    }


def admin_required(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        if not session.get("admin_logado"):
            return redirect(url_for("admin_login"))
        return fn(*args, **kwargs)
    return wrapper


@app.route("/")
def index():
    loja, cardapio_completo = carregar_dados()
    cardapio_ativo = []
    for item in cardapio_completo:
        if item.get("ativo", True):
            copia = dict(item)
            copia["imagem_url"] = resolver_url_imagem(copia.get("imagem", ""))
            cardapio_ativo.append(copia)

    esq_candidatos = [
        (loja.get("foto_lateral_esq", ""), "Especial da Casa"),
        ("burger-destaque.png", "#14 X-Picanha"),
        ("macarrao.png", "#18 Macarrão"),
    ]
    dir_candidatos = [
        (loja.get("foto_lateral_dir", ""), "Na Chapa"),
        ("burger-classico.png", "#13 Bomburguer"),
        ("omelete.png", "#17 Omelete"),
    ]

    side_esq_cards = [
        {"url": resolver_url_imagem(arq), "legenda": leg}
        for arq, leg in esq_candidatos
        if arq
    ]
    side_dir_cards = [
        {"url": resolver_url_imagem(arq), "legenda": leg}
        for arq, leg in dir_candidatos
        if arq
    ]

    categorias = ["Destaques", "Lanches", "Bebidas"]
    status_loja = obter_status_loja()
    return render_template(
        "index.html",
        loja=loja,
        side_esq_cards=side_esq_cards,
        side_dir_cards=side_dir_cards,
        status_loja=status_loja,
        cardapio=cardapio_ativo,
        categorias=categorias,
        adicionais=ADICIONAIS,
    )


@app.route("/admin/login", methods=["GET", "POST"])
def admin_login():
    if request.method == "POST":
        senha = request.form.get("senha", "")
        if senha == ADMIN_PASSWORD:
            session["admin_logado"] = True
            return redirect(url_for("admin_panel"))
        flash("Senha incorreta.", "erro")
    return render_template("admin_login.html")


@app.route("/admin/logout")
def admin_logout():
    session.pop("admin_logado", None)
    return redirect(url_for("admin_login"))


@app.route("/admin", methods=["GET", "POST"])
@admin_required
def admin_panel():
    loja, cardapio = carregar_dados()

    if request.method == "POST":
        acao = request.form.get("acao")

        if acao == "salvar_loja":
            whatsapp_limpo = "".join(ch for ch in request.form.get("whatsapp", "") if ch.isdigit())
            taxa_str = request.form.get("taxa_entrega", "5.00").replace(",", ".")
            try:
                taxa_val = max(0.0, float(taxa_str))
            except ValueError:
                taxa_val = loja["taxa_entrega_padrao"]

            if whatsapp_limpo:
                loja["whatsapp"] = whatsapp_limpo
            loja["taxa_entrega_padrao"] = taxa_val
            loja["slogan"] = request.form.get("slogan", loja["slogan"]).strip() or loja["slogan"]
            salvar_dados(loja, cardapio)
            flash("Configurações da loja atualizadas!", "ok")

        elif acao == "atualizar_item":
            item_id = int(request.form.get("item_id"))
            preco_str = request.form.get("preco", "0").replace(",", ".")
            ativo_val = request.form.get("ativo") == "1"
            arquivo_foto = request.files.get("foto")

            for item in cardapio:
                if item["id"] == item_id:
                    try:
                        novo_preco = max(0.0, float(preco_str))
                        item["preco"] = novo_preco
                    except ValueError:
                        pass
                    item["ativo"] = ativo_val

                    if arquivo_foto and arquivo_foto.filename:
                        if arquivo_permitido(arquivo_foto.filename):
                            ext = arquivo_foto.filename.rsplit(".", 1)[1].lower()
                            nome_seguro = secure_filename(f"item_{item_id}_{int(datetime.now().timestamp())}.{ext}")
                            os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)
                            destino = os.path.join(app.config["UPLOAD_FOLDER"], nome_seguro)
                            arquivo_foto.save(destino)
                            item["imagem"] = f"uploads/{nome_seguro}"
                        else:
                            flash("Formato de imagem inválido. Use PNG, JPG, JPEG, WEBP ou GIF.", "erro")
                            salvar_dados(loja, cardapio)
                            return redirect(url_for("admin_panel"))
                    break

            salvar_dados(loja, cardapio)
            flash("Item atualizado com sucesso!", "ok")

        elif acao == "resetar_padrao":
            loja_reset = dict(DEFAULT_LOJA)
            cardapio_reset = [dict(i) for i in DEFAULT_CARDAPIO]
            salvar_dados(loja_reset, cardapio_reset)
            flash("Cardápio restaurado ao padrão inicial.", "ok")

        return redirect(url_for("admin_panel"))

    cardapio_admin = []
    for item in cardapio:
        copia = dict(item)
        copia["imagem_url"] = resolver_url_imagem(copia.get("imagem", ""))
        cardapio_admin.append(copia)

    return render_template("admin.html", loja=loja, cardapio=cardapio_admin)


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)