from banco_dados import conectar

try:
    with conectar() as conexao:
        with conexao.cursor() as cursor:
            cursor.execute("SELECT current_database()")
            banco = cursor.fetchone()[0]
            print("Conexão realizada com sucesso!")
            print("Banco:", banco)

except Exception as erro:
    print("Erro ao conectar:", erro)