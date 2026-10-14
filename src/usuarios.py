import os
from banco_dados import conectar


def cadastrar_usuario(cpf, nome, nivel_acesso, caminho_imagem):
    if not cpf.isdigit() or len(cpf) != 11:
        raise ValueError("O CPF deve conter 11 dígitos.")

    if not 1 <= nivel_acesso <= 3:
        raise ValueError("O nível de acesso deve ser 1, 2 ou 3.")

    with conectar() as conexao:
        with conexao.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO usuarios
                    (cpf, nome, nivel_acesso, caminho_imagem)
                VALUES (%s, %s, %s, %s)
                RETURNING id
                """,
                (cpf, nome, nivel_acesso, caminho_imagem)
            )

            return cursor.fetchone()[0]


def buscar_usuario_por_cpf(cpf):
    with conectar() as conexao:
        with conexao.cursor() as cursor:
            cursor.execute(
                """
                SELECT id, cpf, nome, nivel_acesso,
                       caminho_imagem, ativo
                FROM usuarios
                WHERE cpf = %s
                """,
                (cpf,)
            )

            return cursor.fetchone()

def buscar_usuario_por_nome(nome):
    with conectar() as conexao:
        with conexao.cursor() as cursor:
            cursor.execute(
                """
                SELECT cpf, nome, nivel_acesso
                FROM usuarios
                WHERE LOWER(nome) = LOWER(%s)
                  AND ativo = TRUE
                """,
                (nome.strip(),)
            )

            return cursor.fetchone()

def buscar_usuario_por_imagem(caminho_imagem):
    caminho_procurado = os.path.realpath(caminho_imagem)

    with conectar() as conexao:
        with conexao.cursor() as cursor:
            cursor.execute(
                """
                SELECT id, cpf, nome, nivel_acesso, caminho_imagem
                FROM usuarios
                WHERE ativo = TRUE
                """
            )
            usuarios = cursor.fetchall()

    for id_usuario, cpf, nome, nivel, imagem in usuarios:
        if os.path.normcase(os.path.realpath(imagem)).casefold() == \
                os.path.normcase(caminho_procurado).casefold():
            return id_usuario, cpf, nome, nivel

    return None
