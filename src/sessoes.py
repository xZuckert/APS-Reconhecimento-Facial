from secrets import token_urlsafe
from threading import Lock
from time import time

TEMPO_EXPIRACAO = 15 * 60       # 15 minutos de inatividade
TEMPO_MAXIMO_SESSAO = 8 * 60 * 60  # 8 horas de duração máxima

sessoes_ativas = {}
sessoes_lock = Lock()


def _expirada(sessao, agora):
    inativa = agora - sessao["ultima_atividade"] > TEMPO_EXPIRACAO
    duracao_excedida = agora - sessao["criada_em"] > TEMPO_MAXIMO_SESSAO

    return inativa or duracao_excedida


def _remover_expiradas(agora):
    expiradas = [
        token
        for token, sessao in sessoes_ativas.items()
        if _expirada(sessao, agora)
    ]

    for token in expiradas:
        del sessoes_ativas[token]


def criar_sessao(usuario, nivel_acesso):
    token = token_urlsafe(32)
    agora = time()

    with sessoes_lock:
        _remover_expiradas(agora)

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

        if _expirada(sessao, agora):
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