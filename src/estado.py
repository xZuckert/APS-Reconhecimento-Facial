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

ultimo_usuario_reconhecido = None


def atualizar_estado(
    autenticado=False,
    usuario=None,
    nivel_acesso=0,
    distancia=None
):
    global ultimo_usuario_reconhecido

    with estado_lock:
        mudou_identidade = (
            autenticado
            and usuario is not None
            and ultimo_usuario_reconhecido is not None
            and usuario != ultimo_usuario_reconhecido
        )

        if autenticado and usuario is not None:
            ultimo_usuario_reconhecido = usuario

        estado_reconhecimento.update({
            "autenticado": autenticado,
            "usuario": usuario,
            "nivel_acesso": nivel_acesso,
            "distancia": distancia,
            "atualizado_em": time()
        })

    # Invalidar sessões somente quando outra pessoa for reconhecida
    if mudou_identidade:
        from sessoes import invalidar_sessoes
        invalidar_sessoes()


def obter_estado():
    with estado_lock:
        estado = estado_reconhecimento.copy()

    if time() - estado["atualizado_em"] > 3:
        estado.update({
            "autenticado": False,
            "usuario": None,
            "nivel_acesso": 0,
            "distancia": None
        })

    estado.pop("atualizado_em", None)
    return estado