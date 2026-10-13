from usuarios import cadastrar_usuario, buscar_usuario_por_cpf, buscar_usuario_por_nome

try:
    id_usuario = cadastrar_usuario(
        cpf="12345678901",
        nome="Usuario Teste",
        nivel_acesso=1,
        caminho_imagem="database/usuario_teste.jpg"
    )

    print("Usuário cadastrado. ID:", id_usuario)

except Exception as erro:
    print("Erro no cadastro:", erro)

usuario = buscar_usuario_por_cpf("12345678901")
print("Consulta:", usuario)

usuario = buscar_usuario_por_nome("Usuario Teste")

if usuario:
    cpf, nome, nivel = usuario
    print("Nome:", nome)
    print("Nível de acesso:", nivel)
else:
    print("Usuário não encontrado ou inativo.")
