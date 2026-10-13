from banco_dados import conectar


def pode_acessar(nivel_usuario, nivel_recurso):
    return nivel_usuario >= nivel_recurso


def consultar_dados(nome, nivel_usuario, nivel_recurso):
    if nivel_recurso not in (1, 2, 3):
        return {
            "sucesso": False,
            "mensagem": "Nível de recurso inválido.",
            "dados": []
        }

    if not pode_acessar(nivel_usuario, nivel_recurso):
        return {
            "sucesso": False,
            "mensagem": "Acesso negado.",
            "dados": []
        }

    with conectar() as conexao:
        with conexao.cursor() as cursor:
            cursor.execute(
                """
                SELECT descricao
                FROM dados_ambientais
                WHERE nivel_acesso = %s
                ORDER BY id
                """,
                (nivel_recurso,)
            )

            dados = [linha[0] for linha in cursor.fetchall()]

    return {
        "sucesso": True,
        "mensagem": "Acesso autorizado.",
        "usuario": nome,
        "nivel_acesso": nivel_usuario,
        "nivel_recurso": nivel_recurso,
        "dados": dados
    }
