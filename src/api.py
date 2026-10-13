from fastapi import FastAPI, HTTPException
from estado import obter_estado
from servicos import consultar_dados

app = FastAPI(
    title="API de Reconhecimento Facial",
    version="1.0.0"
)

@app.get("/status")
def status_reconhecimento():
    return obter_estado()

@app.get("/dados/{nivel_recurso}")
def obter_dados_ambientais(nivel_recurso: int):
    estado = obter_estado()

    if not estado["autenticado"]:
        raise HTTPException(
            status_code=401,
            detail="Usuário não autenticado."
        )

    resultado = consultar_dados(
        nome=estado["usuario"],
        nivel_usuario=estado["nivel_acesso"],
        nivel_recurso=nivel_recurso
    )

    if not resultado["sucesso"]:
        status = 403 if resultado["mensagem"] == "Acesso negado." else 400
        raise HTTPException(
            status_code=status,
            detail=resultado["mensagem"]
        )

    return resultado