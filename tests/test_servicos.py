import unittest
from unittest.mock import patch

from src.servicos import pode_acessar, consultar_dados


class TestAutorizacao(unittest.TestCase):

    def test_nivel_1_acessa_recurso_nivel_1(self):
        self.assertTrue(pode_acessar(1, 1))

    def test_nivel_1_nao_acessa_recurso_nivel_2(self):
        self.assertFalse(pode_acessar(1, 2))

    def test_nivel_2_acessa_recurso_nivel_1(self):
        self.assertTrue(pode_acessar(2, 1))

    def test_nivel_2_acessa_recurso_nivel_2(self):
        self.assertTrue(pode_acessar(2, 2))

    def test_nivel_2_nao_acessa_recurso_nivel_3(self):
        self.assertFalse(pode_acessar(2, 3))

    def test_nivel_3_acessa_todos_os_niveis(self):
        for nivel_recurso in (1, 2, 3):
            with self.subTest(nivel_recurso=nivel_recurso):
                self.assertTrue(pode_acessar(3, nivel_recurso))

    @patch("src.servicos.conectar")
    def test_acesso_negado_nao_consulta_banco(self, mock_conectar):
        resultado = consultar_dados(
            nome="Usuario Teste",
            nivel_usuario=1,
            nivel_recurso=2
        )

        self.assertFalse(resultado["sucesso"])
        self.assertEqual(resultado["mensagem"], "Acesso negado.")
        self.assertEqual(resultado["dados"], [])
        mock_conectar.assert_not_called()

    @patch("src.servicos.conectar")
    def test_nivel_recurso_invalido(self, mock_conectar):
        resultado = consultar_dados(
            nome="Usuario Teste",
            nivel_usuario=3,
            nivel_recurso=4
        )

        self.assertFalse(resultado["sucesso"])
        self.assertEqual(
            resultado["mensagem"],
            "Nível de recurso inválido."
        )
        mock_conectar.assert_not_called()


    @patch("src.servicos.conectar")
    def test_acesso_autorizado_retorna_dados(self, mock_conectar):
        conexao = mock_conectar.return_value.__enter__.return_value
        cursor = conexao.cursor.return_value.__enter__.return_value
        cursor.fetchall.return_value = [
            ("Informações públicas sobre fiscalização ambiental",),
            ("Orientações gerais sobre uso de agrotóxicos",)
        ]

        resultado = consultar_dados(
            nome="Usuario Teste",
            nivel_usuario=1,
            nivel_recurso=1
        )

        self.assertTrue(resultado["sucesso"])
        self.assertEqual(resultado["mensagem"], "Acesso autorizado.")
        self.assertEqual(resultado["usuario"], "Usuario Teste")
        self.assertEqual(resultado["nivel_acesso"], 1)
        self.assertEqual(resultado["nivel_recurso"], 1)
        self.assertEqual(len(resultado["dados"]), 2)
        mock_conectar.assert_called_once()

    @patch("src.servicos.conectar")
    def test_falha_no_banco_retorna_erro_controlado(self, mock_conectar):
        import psycopg

        mock_conectar.side_effect = psycopg.OperationalError(
            "Erro interno de conexão"
        )

        resultado = consultar_dados(
            nome="Usuario Teste",
            nivel_usuario=1,
            nivel_recurso=1
        )

        self.assertFalse(resultado["sucesso"])
        self.assertEqual(
            resultado["mensagem"],
            "Não foi possível consultar os dados no momento."
        )
        self.assertEqual(resultado["dados"], [])
        self.assertNotIn("Erro interno de conexão", str(resultado))


if __name__ == "__main__":
    unittest.main()
