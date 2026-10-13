from secrets import token_urlsafe
from threading import Lock
from time import time

TEMPO_EXPIRACAO = 15 * 60  # 15 minutos de inatividade

sessoes_ativas = {}
sessoes_lock = Lock()


def criar_sessao(usuario, nivel_acesso):
    token = token_urlsafe(32)
    agora = time()

    with sessoes_lock:
        sessoes_ativas[token] = {
            "usuario": usuario,
            "nivel_acesso": nivel_acesso,
            "criada_em": agora,
            "ultima_atividade": agora
        }

    return token


def obter_sessao(token):
    agora = time()

    with sessoes_lock:
        sessao = sessoes_ativas.get(token)

        if sessao is None:
            return None

        if agora - sessao["ultima_atividade"] > TEMPO_EXPIRACAO:
            del sessoes_ativas[token]
            return None

        sessao["ultima_atividade"] = agora
        return sessao.copy()


def encerrar_sessao(token):
    with sessoes_lock:
        return sessoes_ativas.pop(token, None) is not None


def invalidar_sessoes():
    with sessoes_lock:
        sessoes_ativas.clear()