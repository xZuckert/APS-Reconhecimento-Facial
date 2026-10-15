import base64
import logging
import cv2
import psycopg
from fastapi.responses import FileResponse
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from camera_compartilhada import obter_frame_atual
from estado import obter_estado
from fotos_temporarias import obter_caminho_foto, salvar_foto
from reconhecimento import reconhecer_imagem
from servicos import consultar_dados
from sessoes import criar_sessao, obter_sessao, encerrar_sessao
from usuarios import cadastrar_usuario, buscar_usuario_por_id
from fastapi import (
    Depends,
    FastAPI,
    File,
    Form,
    HTTPException,
    UploadFile,
)

logger = logging.getLogger(__name__)

# Configura a API e suas informações básicas
app = FastAPI(
    title="API de Reconhecimento Facial",
    version="1.1.0",
)

# Permite receber tokens Bearer nas requisições protegidas
seguranca = HTTPBearer(auto_error=False)

TAMANHO_MAXIMO_IMAGEM = 5 * 1024 * 1024
TIPOS_IMAGEM_PERMITIDOS = {"image/jpeg", "image/png"}


def obter_token(
    credenciais: HTTPAuthorizationCredentials | None = Depends(seguranca),
):
    # Exige um token de autenticação na requisição
    if credenciais is None:
        raise HTTPException(
            status_code=401,
            detail="Token de autenticação não informado.",
        )

    return credenciais.credentials


def obter_frame_webcam():
    # Recupera o último frame disponibilizado pela câmera compartilhada
    frame = obter_frame_atual()

    if frame is None:
        raise HTTPException(
            status_code=503,
            detail="A webcam ainda não disponibilizou uma imagem.",
        )

    return frame


@app.post("/usuarios", status_code=201)
async def cadastrar_usuario_api(
    cpf: str = Form(...),
    nome: str = Form(...),
    nivel_acesso: int = Form(...),
    imagem: UploadFile = File(...),
):
    # Recebe os dados do formulário enviado à API
    cpf = cpf.strip()
    nome = nome.strip()

    try:
        # Aceita somente imagens JPEG ou PNG
        if imagem.content_type not in TIPOS_IMAGEM_PERMITIDOS:
            raise HTTPException(
                status_code=400,
                detail="Envie uma imagem JPEG ou PNG.",
            )

        # Lê no máximo 5 MB mais um byte para detectar arquivos grandes
        conteudo_imagem = await imagem.read(TAMANHO_MAXIMO_IMAGEM + 1)

        if not conteudo_imagem:
            raise HTTPException(
                status_code=400,
                detail="A imagem enviada está vazia.",
            )

        if len(conteudo_imagem) > TAMANHO_MAXIMO_IMAGEM:
            raise HTTPException(
                status_code=413,
                detail="A imagem não pode ultrapassar 5 MB.",
            )

        # Salva os dados do usuário e os bytes da imagem no banco
        id_usuario = cadastrar_usuario(
            cpf=cpf,
            nome=nome,
            nivel_acesso=nivel_acesso,
            caminho_imagem=f"BYTEA:{cpf}",
            imagem=conteudo_imagem,
        )

    except HTTPException:
        raise

    except ValueError as erro:
        raise HTTPException(
            status_code=400,
            detail=str(erro),
        ) from erro

    except psycopg.errors.UniqueViolation as erro:
        raise HTTPException(
            status_code=409,
            detail="Já existe um usuário cadastrado com esse CPF.",
        ) from erro

    except psycopg.Error as erro:
        logger.exception("Falha ao cadastrar usuário.")
        raise HTTPException(
            status_code=503,
            detail="Não foi possível cadastrar o usuário no momento.",
        ) from erro

    finally:
        # Fecha o arquivo recebido após o processamento
        await imagem.close()

    return {
        "sucesso": True,
        "mensagem": "Usuário cadastrado com sucesso.",
        "id": id_usuario,
        "cpf": cpf,
        "nome": nome,
        "nivel_acesso": nivel_acesso,
    }


@app.post("/cadastro/foto")
def tirar_foto_cadastro():
    # Captura o frame atual da webcam
    frame = obter_frame_webcam()

    sucesso, imagem_codificada = cv2.imencode(".jpg", frame)

    if not sucesso:
        raise HTTPException(
            status_code=500,
            detail="Não foi possível codificar a foto.",
        )

    # Armazena a foto temporariamente e gera uma URL para consultá-la
    foto_id = salvar_foto(imagem_codificada.tobytes())

    return {
        "sucesso": True,
        "mensagem": "Foto capturada e armazenada temporariamente.",
        "foto_id": foto_id,
        "url_imagem": f"/cadastro/foto/{foto_id}",
    }


@app.post("/reconhecimento")
def reconhecer_usuario_api():
    frame = obter_frame_webcam()

    # Salva temporariamente a mesma imagem usada no reconhecimento
    sucesso, imagem_codificada = cv2.imencode(".jpg", frame)

    if not sucesso:
        raise HTTPException(
            status_code=500,
            detail="Não foi possível codificar a imagem do reconhecimento.",
        )

    foto_id = salvar_foto(imagem_codificada.tobytes())
    url_imagem = f"/cadastro/foto/{foto_id}"

    try:
        # Executa o reconhecimento facial no frame capturado
        resultado = reconhecer_imagem(frame)

    except Exception as erro:
        logger.exception("Falha ao realizar reconhecimento facial.")
        raise HTTPException(
            status_code=503,
            detail="Não foi possível realizar o reconhecimento.",
        ) from erro

    # Retorna o resultado do reconhecimento e o endereço da foto
    return {
        "sucesso": True,
        "autenticado": resultado["autenticado"],
        "mensagem": resultado["mensagem"],
        "usuario": resultado.get("usuario"),
        "nivel_acesso": resultado.get("nivel_acesso"),
        "distancia": resultado.get("distancia"),
        "url_imagem": url_imagem,
    }


@app.get("/status")
def status_reconhecimento(token: str = Depends(obter_token)):
    # Verifica se o token corresponde a uma sessão válida
    sessao = obter_sessao(token)

    if sessao is None:
        raise HTTPException(
            status_code=401,
            detail="Sessão inválida ou expirada. Autentique-se novamente.",
        )

    # Consulta os dados do usuário associado à sessão
    usuario = buscar_usuario_por_id(sessao["id_usuario"])

    if usuario is None:
        raise HTTPException(
            status_code=404,
            detail="Usuário da sessão não encontrado ou inativo.",
        )

    id_usuario, cpf, nome, nivel_acesso, imagem = usuario

    if not imagem:
        raise HTTPException(
            status_code=404,
            detail="O usuário não possui uma foto cadastrada.",
        )

    imagem = bytes(imagem)

    # Identifica o formato da imagem pelos seus bytes iniciais
    if imagem.startswith(b"\xff\xd8\xff"):
        tipo_imagem = "image/jpeg"
    elif imagem.startswith(b"\x89PNG\r\n\x1a\n"):
        tipo_imagem = "image/png"
    else:
        raise HTTPException(
            status_code=500,
            detail="O formato da imagem cadastrada não é válido.",
        )

    # Converte a imagem para Base64 para incluí-la na resposta JSON
    imagem_base64 = base64.b64encode(imagem).decode("utf-8")

    return {
        "sucesso": True,
        "usuario": nome,
        "cpf": cpf,
        "nivel_acesso": nivel_acesso,
        "foto": imagem_base64,
        "tipo_imagem": tipo_imagem,
    }


@app.post("/sessao")
def iniciar_sessao():
    # Só permite criar uma sessão após um reconhecimento recente
    estado = obter_estado()

    if not estado["autenticado"] or estado["id_usuario"] is None:
        raise HTTPException(
            status_code=401,
            detail="Nenhum usuário reconhecido recentemente pela câmera.",
        )

    # Cria um token vinculado ao usuário reconhecido
    token = criar_sessao(
        id_usuario=estado["id_usuario"],
        usuario=estado["usuario"],
        nivel_acesso=estado["nivel_acesso"],
    )

    return {
        "sucesso": True,
        "mensagem": "Sessão iniciada.",
        "token": token,
        "tipo": "Bearer",
        "expiracao_inatividade_segundos": 900,
        "usuario": estado["usuario"],
        "nivel_acesso": estado["nivel_acesso"],
    }


@app.delete("/sessao")
def finalizar_sessao(token: str = Depends(obter_token)):
    # Encerra a sessão associada ao token recebido
    encerrar_sessao(token)

    return {
        "sucesso": True,
        "mensagem": "Sessão encerrada.",
    }


@app.get("/dados/{nivel_recurso}")
def obter_dados_ambientais(
    nivel_recurso: int,
    token: str = Depends(obter_token),
):
    # Verifica a sessão antes de consultar informações protegidas
    sessao = obter_sessao(token)

    if sessao is None:
        raise HTTPException(
            status_code=401,
            detail="Sessão inválida ou expirada. Autentique-se novamente.",
        )

    # A consulta verifica se o nível do usuário permite acessar o recurso
    resultado = consultar_dados(
        nome=sessao["usuario"],
        nivel_usuario=sessao["nivel_acesso"],
        nivel_recurso=nivel_recurso,
    )

    if not resultado["sucesso"]:
        mensagem = resultado["mensagem"]

        # Traduz os erros do serviço para códigos HTTP
        status_por_mensagem = {
            "Acesso negado.": 403,
            "Não foi possível consultar os dados no momento.": 503,
        }

        raise HTTPException(
            status_code=status_por_mensagem.get(mensagem, 400),
            detail=mensagem,
        )

    return resultado
