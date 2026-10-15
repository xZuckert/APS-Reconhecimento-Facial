from threading import Lock

# Armazena o frame mais recente disponibilizado pela câmera
_frame_atual = None
_trava = Lock()


def atualizar_frame(frame):
    global _frame_atual

    # Protege a atualização do frame entre diferentes threads
    with _trava:
        _frame_atual = frame.copy()


def obter_frame_atual():
    with _trava:
        if _frame_atual is None:
            return None

        # Retorna uma cópia para evitar alterações no frame original
        return _frame_atual.copy()
