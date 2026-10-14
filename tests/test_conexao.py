import unittest

from src.banco_dados import conectar


class TestConexao(unittest.TestCase):

    def test_conectar_banco(self):
        with conectar() as conexao:
            with conexao.cursor() as cursor:
                cursor.execute("SELECT current_database()")
                banco = cursor.fetchone()[0]

        self.assertEqual(banco, "aps_reconhecimento_facial")


if __name__ == "__main__":
    unittest.main()
