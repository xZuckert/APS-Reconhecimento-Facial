import unittest
from unittest.mock import patch

from src.usuarios import cadastrar_usuario


class TestCadastroUsuario(unittest.TestCase):

    @patch("src.usuarios.conectar")
    def test_cpf_invalido(self, mock_conectar):
        with self.assertRaisesRegex(ValueError, "11 dígitos"):
            cadastrar_usuario(
                cpf="123",
                nome="Usuario Teste",
                nivel_acesso=1,
                caminho_imagem="database/usuario_teste.jpg"
            )

        mock_conectar.assert_not_called()

    @patch("src.usuarios.conectar")
    def test_nivel_acesso_invalido(self, mock_conectar):
        with self.assertRaisesRegex(ValueError, "nível de acesso"):
            cadastrar_usuario(
                cpf="12345678901",
                nome="Usuario Teste",
                nivel_acesso=4,
                caminho_imagem="database/usuario_teste.jpg"
            )

        mock_conectar.assert_not_called()


    @patch("src.usuarios.conectar")
    def test_cadastro_valido(self, mock_conectar):
        conexao = mock_conectar.return_value.__enter__.return_value
        cursor = conexao.cursor.return_value.__enter__.return_value
        cursor.fetchone.return_value = (99,)

        resultado = cadastrar_usuario(
            cpf="98765432100",
            nome="Usuario Teste",
            nivel_acesso=1,
            caminho_imagem="database/usuario_teste.jpg"
        )

        self.assertEqual(resultado, 99)
        cursor.execute.assert_called_once()
        mock_conectar.assert_called_once()

if __name__ == "__main__":
    unittest.main()
