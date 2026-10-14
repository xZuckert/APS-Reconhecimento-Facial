from fastapi import FastAPI, HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from estado import obter_estado
from sessoes import criar_sessao, obter_sessao, encerrar_sessao
from servicos import consultar_dados

app = FastAPI(
    title="API de Reconhecimento Facial",
    version="1.1.0"
)

seguranca = HTTPBearer(auto_error=False)


def obter_token(
    credenciais: HTTPAuthorizationCredentials | None = Depends(seguranca)
):
    if credenciais is None:
        raise HTTPException(
            status_code=401,
            detail="Token de autenticação não informado."
        )

    return credenciais.credentials


@app.get("/status")
def status_reconhecimento():
    return obter_estado()


@app.post("/sessao")
def iniciar_sessao():
    estado = obter_estado()

    if not estado["autenticado"]:
        raise HTTPException(
            status_code=401,
            detail="Nenhum usuário autenticado pela câmera."
        )

    token = criar_sessao(
        usuario=estado["usuario"],
        nivel_acesso=estado["nivel_acesso"]
    )

    return {
        "sucesso": True,
        "mensagem": "Sessão iniciada.",
        "token": token,
        "tipo": "Bearer",
        "expiracao_inatividade_segundos": 900,
        "usuario": estado["usuario"],
        "nivel_acesso": estado["nivel_acesso"]
    }


@app.delete("/sessao")
def finalizar_sessao(token: str = Depends(obter_token)):
    encerrar_sessao(token)

    return {
        "sucesso": True,
        "mensagem": "Sessão encerrada."
    }


@app.get("/dados/{nivel_recurso}")
def obter_dados_ambientais(
    nivel_recurso: int,
    token: str = Depends(obter_token)
):
    sessao = obter_sessao(token)

    if sessao is None:
        raise HTTPException(
            status_code=401,
            detail="Sessão inválida ou expirada. Autentique-se novamente."
        )

    resultado = consultar_dados(
        nome=sessao["usuario"],
        nivel_usuario=sessao["nivel_acesso"],
        nivel_recurso=nivel_recurso
    )

    if not resultado["sucesso"]:
        mensagem = resultado["mensagem"]

        # Definir o código HTTP conforme o tipo de erro
        if mensagem == "Acesso negado.":
            status = 403
        elif mensagem == "Não foi possível consultar os dados no momento.":
            status = 503
        else:
            status = 400

        raise HTTPException(
            status_code=status,
            detail=mensagem
        )

    return resultado