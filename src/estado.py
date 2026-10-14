from threading import Lock
from time import time

# Variáveis globais
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
    # Atualizar as informações do reconhecimento
    with estado_lock:
        estado_reconhecimento.update({
            "autenticado": autenticado,
            "usuario": usuario,
            "nivel_acesso": nivel_acesso,
            "distancia": distancia,
            "atualizado_em": time()
        })


def obter_estado():
    # Obter uma cópia do estado atual
    with estado_lock:
        estado = estado_reconhecimento.copy()

    # Considerar o reconhecimento desatualizado após 3 segundos
    if time() - estado["atualizado_em"] > 3:
        estado.update({
            "autenticado": False,
            "usuario": None,
            "nivel_acesso": 0,
            "distancia": None
        })

    estado.pop("atualizado_em", None)

    return estado