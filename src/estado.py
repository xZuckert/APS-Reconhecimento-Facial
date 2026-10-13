
from threading import Lock
from time import time

estado_lock = Lock()

estado_reconhecimento = {
    "autenticado": False,
    "usuario": None,
    "nivel_acesso": 0,
    "distancia": None,
    "atualizado_em": 0
}


def atualizar_estado(
    autenticado=False,
    usuario=None,
    nivel_acesso=0,
    distancia=None
):
    with estado_lock:
        estado_reconhecimento.update({
            "autenticado": autenticado,
            "usuario": usuario,
            "nivel_acesso": nivel_acesso,
            "distancia": distancia,
            "atualizado_em": time()
        })


def obter_estado():
    with estado_lock:
        estado = estado_reconhecimento.copy()

    # Não manter a autenticação válida indefinidamente
    if time() - estado["atualizado_em"] > 3:
        estado.update({
            "autenticado": False,
            "usuario": None,
            "nivel_acesso": 0,
            "distancia": None
        })

    estado.pop("atualizado_em", None)
    return estado