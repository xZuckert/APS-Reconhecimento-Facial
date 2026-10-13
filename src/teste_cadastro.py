from usuarios import cadastrar_usuario

try:
    id_usuario = cadastrar_usuario(
        cpf="43921667836",
        nome="Caique Zuckert Souza",
        nivel_acesso=3,
        caminho_imagem="database/Caique Zuckert Souza.jpg"
    )

    print("Cadastro realizado!")
    print("ID do usuário:", id_usuario)

except Exception as erro:
    print("Erro no cadastro:", erro)