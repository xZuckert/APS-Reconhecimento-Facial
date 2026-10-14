import unittest
from unittest import TestCase
from unittest.mock import patch

from src.estado import (
    atualizar_estado,
    obter_estado,
    estado_reconhecimento,
)


class TestEstado(TestCase):

    def setUp(self):
        self.estado_original = estado_reconhecimento.copy()
        atualizar_estado()

    def tearDown(self):
        estado_reconhecimento.update(self.estado_original)

    @patch("src.estado.time", return_value=100)
    def test_atualizar_estado(self, mock_time):
        atualizar_estado(
            autenticado=True,
            usuario="Usuario Teste",
            nivel_acesso=2,
            distancia=0.45,
        )

        self.assertTrue(estado_reconhecimento["autenticado"])
        self.assertEqual(estado_reconhecimento["usuario"], "Usuario Teste")
        self.assertEqual(estado_reconhecimento["nivel_acesso"], 2)
        self.assertEqual(estado_reconhecimento["distancia"], 0.45)
        self.assertEqual(estado_reconhecimento["atualizado_em"], 100)

    @patch("src.estado.time", return_value=101)
    def test_obter_estado_atualizado(self, mock_time):
        atualizar_estado(
            autenticado=True,
            usuario="Usuario Teste",
            nivel_acesso=2,
            distancia=0.45,
        )

        estado = obter_estado()

        self.assertTrue(estado["autenticado"])
        self.assertEqual(estado["usuario"], "Usuario Teste")
        self.assertEqual(estado["nivel_acesso"], 2)
        self.assertEqual(estado["distancia"], 0.45)
        self.assertNotIn("atualizado_em", estado)

    @patch("src.estado.time", side_effect=[100, 104])
    def test_expira_estado_apos_tres_segundos(self, mock_time):
        atualizar_estado(
            autenticado=True,
            usuario="Usuario Teste",
            nivel_acesso=2,
            distancia=0.45,
        )

        estado = obter_estado()

        self.assertFalse(estado["autenticado"])
        self.assertIsNone(estado["usuario"])
        self.assertEqual(estado["nivel_acesso"], 0)
        self.assertIsNone(estado["distancia"])

    @patch("src.estado.time", side_effect=[100, 103])
    def test_estado_nao_expira_exatamente_em_tres_segundos(self, mock_time):
        atualizar_estado(
            autenticado=True,
            usuario="Usuario Teste",
            nivel_acesso=2,
            distancia=0.45,
        )

        estado = obter_estado()

        self.assertTrue(estado["autenticado"])
        self.assertEqual(estado["usuario"], "Usuario Teste")

    def test_obter_estado_retorna_copia(self):
        atualizar_estado(
            autenticado=True,
            usuario="Usuario Teste",
            nivel_acesso=2,
            distancia=0.45,
        )

        with patch("src.estado.time", return_value=101):
            estado = obter_estado()

        estado["usuario"] = "Outro Usuario"

        self.assertEqual(
            estado_reconhecimento["usuario"],
            "Usuario Teste",
        )


if __name__ == "__main__":
    unittest.main()