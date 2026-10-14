import unittest
from unittest.mock import MagicMock, patch

from src.usuarios import buscar_usuario_por_cpf, buscar_usuario_por_nome


class TestBuscaUsuario(unittest.TestCase):

    @patch("usuarios.conectar")
    def test_buscar_por_cpf(self, mock_conectar):
        usuario_esperado = (
            1, "12345678901", "Usuario Teste", 1,
            "database/usuario_teste.jpg", True
        )

        conexao = MagicMock()
        cursor = conexao.cursor.return_value.__enter__.return_value
        cursor.fetchone.return_value = usuario_esperado
        mock_conectar.return_value.__enter__.return_value = conexao

        resultado = buscar_usuario_por_cpf("12345678901")

        self.assertEqual(resultado, usuario_esperado)

    @patch("usuarios.conectar")
    def test_buscar_por_nome(self, mock_conectar):
        usuario_esperado = ("12345678901", "Usuario Teste", 1)

        conexao = MagicMock()
        cursor = conexao.cursor.return_value.__enter__.return_value
        cursor.fetchone.return_value = usuario_esperado
        mock_conectar.return_value.__enter__.return_value = conexao

        resultado = buscar_usuario_por_nome("Usuario Teste")

        self.assertEqual(resultado, usuario_esperado)


if __name__ == "__main__":
    unittest.main()
