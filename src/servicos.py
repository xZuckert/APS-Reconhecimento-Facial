import logging
import psycopg

from banco_dados import conectar

# Configurar o registro de erros
logger = logging.getLogger(__name__)


def pode_acessar(nivel_usuario, nivel_recurso):
    # Verificar se o nível do usuário permite o acesso
    return nivel_usuario >= nivel_recurso


def consultar_dados(nome, nivel_usuario, nivel_recurso):
    # Validar o nível do recurso solicitado
    if nivel_recurso not in (1, 2, 3):
        return {
            "sucesso": False,
            "mensagem": "Nível de recurso inválido.",
            "dados": []
        }

    # Verificar a permissão de acesso
    if not pode_acessar(nivel_usuario, nivel_recurso):
        return {
            "sucesso": False,
            "mensagem": "Acesso negado.",
            "dados": []
        }

    try:
        # Consultar os dados no banco de dados
        with conectar() as conexao:
            with conexao.cursor() as cursor:
                cursor.execute("""
                    SELECT descricao
                    FROM dados_ambientais
                    WHERE nivel_acesso = %s
                    ORDER BY id
                """, (nivel_recurso,))

                dados = [linha[0] for linha in cursor.fetchall()]

    except psycopg.Error:
        # Registrar o erro sem expor detalhes ao cliente
        logger.exception(
            "Falha ao consultar dados ambientais no PostgreSQL."
        )

        return {
            "sucesso": False,
            "mensagem": "Não foi possível consultar os dados no momento.",
            "dados": []
        }

    # Retornar os dados quando a consulta for concluída
    return {
        "sucesso": True,
        "mensagem": "Acesso autorizado.",
        "usuario": nome,
        "nivel_acesso": nivel_usuario,
        "nivel_recurso": nivel_recurso,
        "dados": dados
    }
