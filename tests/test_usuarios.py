import unittest
from unittest import TestCase
from unittest.mock import patch, MagicMock
from src.usuarios import (
    cadastrar_usuario,
    buscar_usuario_por_cpf,
    buscar_usuario_por_nome,
    buscar_usuario_por_imagem,
)


class TestBuscarUsuarioPorImagem(TestCase):

    @patch("src.usuarios.conectar")
    def test_encontra_usuario_pelo_caminho_da_imagem(self, mock_conectar):
        usuario = (1, "12345678901", "Usuario Teste", 2, "/fotos/rosto.jpg")

        mock_cursor = MagicMock()
        mock_cursor.fetchall.return_value = [usuario]
        mock_conectar.return_value.__enter__.return_value.cursor.return_value.__enter__.return_value = mock_cursor

        with patch("src.usuarios.os.path.realpath", side_effect=lambda caminho: caminho):
            resultado = buscar_usuario_por_imagem("/fotos/rosto.jpg")

        self.assertEqual(resultado, (1, "12345678901", "Usuario Teste", 2))

    @patch("src.usuarios.conectar")
    def test_retorna_none_quando_imagem_nao_e_encontrada(self, mock_conectar):
        mock_cursor = MagicMock()
        mock_cursor.fetchall.return_value = [
            (1, "12345678901", "Usuario Teste", 2, "/fotos/outra.jpg")
        ]
        mock_conectar.return_value.__enter__.return_value.cursor.return_value.__enter__.return_value = mock_cursor

        with patch("src.usuarios.os.path.realpath", side_effect=lambda caminho: caminho):
            resultado = buscar_usuario_por_imagem("/fotos/nao_existe.jpg")

        self.assertIsNone(resultado)

    @patch("src.usuarios.conectar")
    def test_compara_caminhos_sem_diferenciar_maiusculas(self, mock_conectar):
        mock_cursor = MagicMock()
        mock_cursor.fetchall.return_value = [
            (1, "12345678901", "Usuario Teste", 2, "/FOTOS/Rosto.jpg")
        ]
        mock_conectar.return_value.__enter__.return_value.cursor.return_value.__enter__.return_value = mock_cursor

        with patch("src.usuarios.os.path.realpath", side_effect=lambda caminho: caminho):
            resultado = buscar_usuario_por_imagem("/fotos/rosto.jpg")

        self.assertEqual(resultado, (1, "12345678901", "Usuario Teste", 2))

    @patch("src.usuarios.conectar")
    def test_retorna_none_quando_nao_existem_usuarios_ativos(self, mock_conectar):
        mock_cursor = MagicMock()
        mock_cursor.fetchall.return_value = []
        mock_conectar.return_value.__enter__.return_value.cursor.return_value.__enter__.return_value = mock_cursor

        resultado = buscar_usuario_por_imagem("/fotos/rosto.jpg")

        self.assertIsNone(resultado)


class TestUsuarios(TestCase):

    @patch("src.usuarios.conectar")
    def test_cadastrar_usuario(self, mock_conectar):
        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = (10,)
        mock_conectar.return_value.__enter__.return_value.cursor.return_value.__enter__.return_value = mock_cursor

        resultado = cadastrar_usuario(
            "12345678901",
            "Usuario Teste",
            2,
            "/fotos/rosto.jpg",
        )

        self.assertEqual(resultado, 10)
        mock_cursor.execute.assert_called_once()

    def test_cadastrar_usuario_cpf_invalido(self):
        with self.assertRaises(ValueError):
            cadastrar_usuario("123", "Usuario Teste", 2, "/fotos/rosto.jpg")

    def test_cadastrar_usuario_nivel_invalido(self):
        with self.assertRaises(ValueError):
            cadastrar_usuario("12345678901", "Usuario Teste", 4, "/fotos/rosto.jpg")

    @patch("src.usuarios.conectar")
    def test_buscar_usuario_por_cpf(self, mock_conectar):
        usuario = (1, "12345678901", "Usuario Teste", 2, "/fotos/rosto.jpg", True)

        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = usuario
        mock_conectar.return_value.__enter__.return_value.cursor.return_value.__enter__.return_value = mock_cursor

        resultado = buscar_usuario_por_cpf("12345678901")

        self.assertEqual(resultado, usuario)
        mock_cursor.execute.assert_called_once()

    @patch("src.usuarios.conectar")
    def test_buscar_usuario_por_cpf_nao_encontrado(self, mock_conectar):
        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = None
        mock_conectar.return_value.__enter__.return_value.cursor.return_value.__enter__.return_value = mock_cursor

        resultado = buscar_usuario_por_cpf("00000000000")

        self.assertIsNone(resultado)

    @patch("src.usuarios.conectar")
    def test_buscar_usuario_por_nome(self, mock_conectar):
        usuario = ("12345678901", "Usuario Teste", 2)

        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = usuario
        mock_conectar.return_value.__enter__.return_value.cursor.return_value.__enter__.return_value = mock_cursor

        resultado = buscar_usuario_por_nome("  Usuario Teste  ")

        self.assertEqual(resultado, usuario)
        mock_cursor.execute.assert_called_once()

    @patch("src.usuarios.conectar")
    def test_buscar_usuario_por_nome_nao_encontrado(self, mock_conectar):
        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = None
        mock_conectar.return_value.__enter__.return_value.cursor.return_value.__enter__.return_value = mock_cursor

        resultado = buscar_usuario_por_nome("Nome Inexistente")

        self.assertIsNone(resultado)


if __name__ == "__main__":
    unittest.main()
