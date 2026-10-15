import unittest
from unittest.mock import patch
from src import sessoes


class TestSessoes(unittest.TestCase):

    # Limpar as sessões antes de cada teste para que
    # os resultados não dependam de execuções anteriores.
    def setUp(self):
        sessoes.invalidar_sessoes()

    # Limpar novamente as sessões ao terminar cada teste.
    def tearDown(self):
        sessoes.invalidar_sessoes()

    # Simular a geração do token e o horário de criação
    # para verificar os dados armazenados na nova sessão.
    @patch("src.sessoes.time", return_value=1000)
    @patch("src.sessoes.token_urlsafe", return_value="token-teste")
    def test_criar_sessao(self, mock_token, mock_time):
        token = sessoes.criar_sessao("Usuario Teste", 2)

        # Confirmar o token e recuperar os dados da sessão criada.
        self.assertEqual(token, "token-teste")
        sessao = sessoes.obter_sessao(token)

        # Verificar o usuário, o nível de acesso e o horário inicial.
        self.assertEqual(sessao["usuario"], "Usuario Teste")
        self.assertEqual(sessao["nivel_acesso"], 2)
        self.assertEqual(sessao["criada_em"], 1000)

    # Verificar se um token que não existe retorna None.
    @patch("src.sessoes.time", return_value=1000)
    def test_token_invalido_retorna_none(self, mock_time):
        self.assertIsNone(sessoes.obter_sessao("token-inexistente"))

    # Criar uma sessão e verificar se o encerramento
    # invalida o token correspondente.
    @patch("src.sessoes.time")
    def test_encerrar_sessao_invalida_token(self, mock_time):
        mock_time.return_value = 1000
        token = sessoes.criar_sessao("Usuario Teste", 1)

        resultado = sessoes.encerrar_sessao(token)

        # Confirmar o encerramento e a impossibilidade de recuperar a sessão.
        self.assertTrue(resultado)
        self.assertIsNone(sessoes.obter_sessao(token))

    # Verificar se uma sessão expira quando o tempo
    # de inatividade ultrapassa o limite configurado.
    @patch("src.sessoes.time")
    def test_expira_por_inatividade(self, mock_time):
        mock_time.return_value = 1000
        token = sessoes.criar_sessao("Usuario Teste", 1)

        # Avançar o relógio para além do tempo de expiração.
        mock_time.return_value = 1000 + sessoes.TEMPO_EXPIRACAO + 1

        self.assertIsNone(sessoes.obter_sessao(token))

    # Verificar se uma sessão expira ao ultrapassar
    # a duração máxima permitida, mesmo que tenha atividade.
    @patch("src.sessoes.time")
    def test_expira_apos_duracao_maxima(self, mock_time):
        mock_time.return_value = 1000
        token = sessoes.criar_sessao("Usuario Teste", 1)

        # Avançar o relógio para além da duração máxima.
        mock_time.return_value = 1000 + sessoes.TEMPO_MAXIMO_SESSAO + 1

        self.assertIsNone(sessoes.obter_sessao(token))

    # Verificar se a atividade renova o prazo de inatividade
    # sem ultrapassar a duração máxima da sessão.
    @patch("src.sessoes.time")
    def test_atividade_renova_inatividade(self, mock_time):
        mock_time.return_value = 1000
        token = sessoes.criar_sessao("Usuario Teste", 1)

        # Consultar a sessão após dez minutos de atividade.
        mock_time.return_value = 1000 + 600
        self.assertIsNotNone(sessoes.obter_sessao(token))

        # Verificar novamente antes de completar o período
        # de inatividade contado a partir da última atividade.
        mock_time.return_value = (
            1000 + 600 + sessoes.TEMPO_EXPIRACAO - 1
        )
        self.assertIsNotNone(sessoes.obter_sessao(token))

    # Criar duas sessões e verificar se a função de invalidação
    # remove todas as sessões armazenadas.
    @patch("src.sessoes.time")
    def test_invalidar_todas_sessoes(self, mock_time):
        mock_time.return_value = 1000
        token1 = sessoes.criar_sessao("Usuario 1", 1)
        token2 = sessoes.criar_sessao("Usuario 2", 2)

        sessoes.invalidar_sessoes()

        # Confirmar que nenhum dos dois tokens continua válido.
        self.assertIsNone(sessoes.obter_sessao(token1))
        self.assertIsNone(sessoes.obter_sessao(token2))

    # Verificar se a criação de uma nova sessão também remove
    # sessões antigas que já ultrapassaram o prazo de expiração.
    @patch(
        "src.sessoes.token_urlsafe",
        side_effect=["token-antigo", "token-novo"]
    )
    @patch("src.sessoes.time")
    def test_criar_sessao_remove_sessoes_expiradas(
        self, mock_time, mock_token
    ):
        mock_time.return_value = 1000
        token_antigo = sessoes.criar_sessao("Usuario Antigo", 1)

        # Avançar o relógio até depois da expiração da sessão antiga.
        mock_time.return_value = 1000 + sessoes.TEMPO_EXPIRACAO + 1
        token_novo = sessoes.criar_sessao("Usuario Novo", 2)

        # Confirmar a criação dos dois tokens simulados.
        self.assertEqual(token_antigo, "token-antigo")
        self.assertEqual(token_novo, "token-novo")

        # A sessão antiga deve ter sido removida, enquanto a nova
        # deve continuar disponível.
        self.assertIsNone(sessoes.obter_sessao(token_antigo))
        self.assertIsNotNone(sessoes.obter_sessao(token_novo))


if __name__ == "__main__":
    # Executar os testes de sessão diretamente pelo arquivo.
    unittest.main()
