import unittest
from unittest.mock import patch

from fastapi.testclient import TestClient
from src.api import app


class TestAPI(unittest.TestCase):

    def setUp(self):
        self.client = TestClient(app)

    def test_dados_sem_token_retorna_401(self):
        resposta = self.client.get("/dados/1")

        self.assertEqual(resposta.status_code, 401)
        self.assertEqual(
            resposta.json()["detail"],
            "Token de autenticação não informado."
        )

    @patch("src.api.obter_sessao", return_value=None)
    def test_sessao_invalida_retorna_401(self, mock_sessao):
        resposta = self.client.get(
            "/dados/1",
            headers={"Authorization": "Bearer token-invalido"}
        )

        self.assertEqual(resposta.status_code, 401)
        self.assertIn("Sessão inválida", resposta.json()["detail"])
        mock_sessao.assert_called_once_with("token-invalido")

    @patch("src.api.consultar_dados")
    @patch("src.api.obter_sessao")
    def test_acesso_negado_retorna_403(
        self, mock_sessao, mock_consultar
    ):
        mock_sessao.return_value = {
            "usuario": "Usuario Teste",
            "nivel_acesso": 1
        }
        mock_consultar.return_value = {
            "sucesso": False,
            "mensagem": "Acesso negado.",
            "dados": []
        }

        resposta = self.client.get(
            "/dados/2",
            headers={"Authorization": "Bearer token-teste"}
        )

        self.assertEqual(resposta.status_code, 403)
        self.assertEqual(resposta.json()["detail"], "Acesso negado.")

    @patch("src.api.consultar_dados")
    @patch("src.api.obter_sessao")
    def test_falha_banco_retorna_503(
        self, mock_sessao, mock_consultar
    ):
        mock_sessao.return_value = {
            "usuario": "Usuario Teste",
            "nivel_acesso": 1
        }
        mock_consultar.return_value = {
            "sucesso": False,
            "mensagem": "Não foi possível consultar os dados no momento.",
            "dados": []
        }

        resposta = self.client.get(
            "/dados/1",
            headers={"Authorization": "Bearer token-teste"}
        )

        self.assertEqual(resposta.status_code, 503)
        self.assertEqual(
            resposta.json()["detail"],
            "Não foi possível consultar os dados no momento."
        )


    @patch("src.api.obter_estado")
    def test_status_retorna_estado(self, mock_estado):
        mock_estado.return_value = {
            "autenticado": True,
            "usuario": "Usuario Teste",
            "nivel_acesso": 1
        }

        resposta = self.client.get("/status")

        self.assertEqual(resposta.status_code, 200)
        self.assertEqual(resposta.json()["usuario"], "Usuario Teste")
        mock_estado.assert_called_once()

    @patch("src.api.obter_estado")
    def test_status_sem_usuario_autenticado(self, mock_estado):
        mock_estado.return_value = {
            "autenticado": False,
            "usuario": None,
            "nivel_acesso": None
        }

        resposta = self.client.get("/status")

        self.assertEqual(resposta.status_code, 200)
        self.assertFalse(resposta.json()["autenticado"])

    @patch("src.api.criar_sessao", return_value="token-teste")
    @patch("src.api.obter_estado")
    def test_iniciar_sessao_com_usuario_autenticado(
        self, mock_estado, mock_criar_sessao
    ):
        mock_estado.return_value = {
            "autenticado": True,
            "usuario": "Usuario Teste",
            "nivel_acesso": 2
        }

        resposta = self.client.post("/sessao")

        self.assertEqual(resposta.status_code, 200)
        self.assertTrue(resposta.json()["sucesso"])
        self.assertEqual(resposta.json()["token"], "token-teste")
        self.assertEqual(resposta.json()["tipo"], "Bearer")
        self.assertEqual(resposta.json()["nivel_acesso"], 2)
        mock_criar_sessao.assert_called_once_with(
            usuario="Usuario Teste",
            nivel_acesso=2
        )

    @patch("src.api.criar_sessao")
    @patch("src.api.obter_estado")
    def test_iniciar_sessao_sem_usuario_retorna_401(
        self, mock_estado, mock_criar_sessao
    ):
        mock_estado.return_value = {
            "autenticado": False,
            "usuario": None,
            "nivel_acesso": None
        }

        resposta = self.client.post("/sessao")

        self.assertEqual(resposta.status_code, 401)
        self.assertEqual(
            resposta.json()["detail"],
            "Nenhum usuário autenticado pela câmera."
        )
        mock_criar_sessao.assert_not_called()


    @patch("src.api.encerrar_sessao")
    def test_finalizar_sessao_com_token(self, mock_encerrar):
        resposta = self.client.delete(
            "/sessao",
            headers={"Authorization": "Bearer token-teste"}
        )

        self.assertEqual(resposta.status_code, 200)
        self.assertTrue(resposta.json()["sucesso"])
        self.assertEqual(
            resposta.json()["mensagem"],
            "Sessão encerrada."
        )
        mock_encerrar.assert_called_once_with("token-teste")

    @patch("src.api.consultar_dados")
    @patch("src.api.obter_sessao")
    def test_consulta_autorizada_retorna_dados(
        self, mock_sessao, mock_consultar
    ):
        mock_sessao.return_value = {
            "usuario": "Usuario Teste",
            "nivel_acesso": 2
        }

        mock_consultar.return_value = {
            "sucesso": True,
            "mensagem": "Acesso autorizado.",
            "usuario": "Usuario Teste",
            "nivel_acesso": 2,
            "nivel_recurso": 2,
            "dados": ["Temperatura: 25 graus"]
        }

        resposta = self.client.get(
            "/dados/2",
            headers={"Authorization": "Bearer token-teste"}
        )

        self.assertEqual(resposta.status_code, 200)
        self.assertTrue(resposta.json()["sucesso"])
        self.assertEqual(
            resposta.json()["dados"],
            ["Temperatura: 25 graus"]
        )

        mock_sessao.assert_called_once_with("token-teste")
        mock_consultar.assert_called_once_with(
            nome="Usuario Teste",
            nivel_usuario=2,
            nivel_recurso=2
        )


    @patch("src.api.consultar_dados")
    @patch("src.api.obter_sessao")
    def test_erro_generico_retorna_400(
        self, mock_sessao, mock_consultar
    ):
        mock_sessao.return_value = {
            "usuario": "Usuario Teste",
            "nivel_acesso": 2
        }
        mock_consultar.return_value = {
            "sucesso": False,
            "mensagem": "Erro genérico de consulta.",
            "dados": []
        }

        resposta = self.client.get(
            "/dados/2",
            headers={"Authorization": "Bearer token-teste"}
        )

        self.assertEqual(resposta.status_code, 400)
        self.assertEqual(
            resposta.json()["detail"],
            "Erro genérico de consulta."
        )


if __name__ == "__main__":
    unittest.main()
