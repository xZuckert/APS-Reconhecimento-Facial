import os
import sys
import unittest
import tempfile
from unittest.mock import patch, MagicMock

import numpy as np
import pandas as pd

# Simular dependências que não devem iniciar durante os testes.
sys.modules.setdefault("api", MagicMock())
sys.modules.setdefault("uvicorn", MagicMock())

# Evitar carregar TensorFlow e DeepFace reais.
deepface_mock = MagicMock()
sys.modules["deepface"] = MagicMock(DeepFace=deepface_mock)

from src import main

class TestAtualizarInterface(unittest.TestCase):
    def test_atualizar_interface_com_dados(self):
        main.atualizar_interface("Caique", 0.25, 2)

        self.assertEqual(main.nome_pessoa, "Caique")
        self.assertEqual(main.score, 0.25)
        self.assertEqual(main.nivel_acesso, 2)


    def test_atualizar_interface_limpa_dados(self):
        main.atualizar_interface()

        self.assertEqual(main.nome_pessoa, "")
        self.assertEqual(main.score, 0)
        self.assertEqual(main.nivel_acesso, 0)



class TestReconhecerRosto(unittest.TestCase):
    def setUp(self):
        main.atualizar_interface()
        main.reconhecimento_em_andamento = True

    def usuario_teste(self, usuario_id=1, nome="Caique", nivel=2):
        return (
            usuario_id,
            "12345678901",
            nome,
            nivel,
            b"imagem_de_teste"
        )

    @patch("src.main.atualizar_estado")
    @patch("src.main.cv2.imwrite", return_value=True)
    @patch("src.main.DeepFace.find")
    @patch("src.main.listar_imagens_usuarios")
    def test_usuario_reconhecido(
        self, listar_usuarios, deepface, imwrite, atualizar_estado
    ):
        listar_usuarios.return_value = [self.usuario_teste()]
        deepface.return_value = [
            pd.DataFrame([
                {"distance": 0.30, "identity": "/tmp/referencias/1.jpg"}
            ])
        ]

        main.reconhecer_rosto(
            np.zeros((100, 100, 3), dtype=np.uint8)
        )

        self.assertEqual(main.nome_pessoa, "Caique")
        self.assertEqual(main.nivel_acesso, 2)
        self.assertEqual(main.score, 0.30)

        atualizar_estado.assert_called_once_with(
            autenticado=True,
            usuario="Caique",
            nivel_acesso=2,
            distancia=0.30
        )

    @patch("src.main.atualizar_estado")
    @patch("src.main.cv2.imwrite", return_value=True)
    @patch("src.main.DeepFace.find")
    @patch("src.main.listar_imagens_usuarios")
    def test_nenhuma_correspondencia(
        self, listar_usuarios, deepface, imwrite, atualizar_estado
    ):
        listar_usuarios.return_value = [self.usuario_teste()]
        deepface.return_value = [pd.DataFrame()]

        main.reconhecer_rosto(
            np.zeros((100, 100, 3), dtype=np.uint8)
        )

        self.assertEqual(main.nome_pessoa, "")
        atualizar_estado.assert_called_once_with()

    @patch("src.main.atualizar_estado")
    @patch("src.main.cv2.imwrite", return_value=False)
    @patch("src.main.listar_imagens_usuarios")
    def test_falha_ao_salvar_frame(
        self, listar_usuarios, imwrite, atualizar_estado
    ):
        listar_usuarios.return_value = [self.usuario_teste()]

        main.reconhecer_rosto(
            np.zeros((100, 100, 3), dtype=np.uint8)
        )

        self.assertEqual(main.nome_pessoa, "")
        atualizar_estado.assert_called_once_with()
        self.assertFalse(main.reconhecimento_em_andamento)

    @patch("src.main.cv2.imwrite", side_effect=RuntimeError("erro"))
    @patch("src.main.listar_imagens_usuarios")
    def test_reconhecimento_libera_estado_ao_finalizar(
        self, listar_usuarios, imwrite
    ):
        listar_usuarios.return_value = [self.usuario_teste()]

        main.reconhecer_rosto(
            np.zeros((100, 100, 3), dtype=np.uint8)
        )

        self.assertFalse(main.reconhecimento_em_andamento)

    @patch("src.main.atualizar_estado")
    @patch("src.main.cv2.imwrite", return_value=True)
    @patch("src.main.DeepFace.find")
    @patch("src.main.listar_imagens_usuarios")
    def test_usuario_reconhecido_mas_nao_cadastrado(
        self, listar_usuarios, deepface, imwrite, atualizar_estado
    ):
        listar_usuarios.return_value = [self.usuario_teste(usuario_id=1)]
        deepface.return_value = [
            pd.DataFrame([
                {"distance": 0.30, "identity": "/tmp/referencias/99.jpg"}
            ])
        ]

        main.reconhecer_rosto(
            np.zeros((100, 100, 3), dtype=np.uint8)
        )

        self.assertEqual(main.nome_pessoa, "")
        self.assertEqual(main.score, 0)
        self.assertEqual(main.nivel_acesso, 0)
        atualizar_estado.assert_called_once_with()

    @patch("src.main.atualizar_estado")
    @patch("src.main.cv2.imwrite", return_value=True)
    @patch("src.main.DeepFace.find")
    @patch("src.main.listar_imagens_usuarios")
    def test_distancia_acima_do_limite(
        self, listar_usuarios, deepface, imwrite, atualizar_estado
    ):
        listar_usuarios.return_value = [self.usuario_teste()]
        deepface.return_value = [
            pd.DataFrame([
                {"distance": 0.80, "identity": "/tmp/referencias/1.jpg"}
            ])
        ]

        main.atualizar_interface("Pessoa anterior", 0.20, 1)

        main.reconhecer_rosto(
            np.zeros((100, 100, 3), dtype=np.uint8)
        )

        self.assertEqual(main.nome_pessoa, "")
        self.assertEqual(main.score, 0)
        self.assertEqual(main.nivel_acesso, 0)
        atualizar_estado.assert_called_once_with()

    @patch("src.main.atualizar_estado")
    @patch("src.main.listar_imagens_usuarios", return_value=[])
    def test_nenhum_usuario_com_imagem(
        self, listar_usuarios, atualizar_estado
    ):
        main.reconhecer_rosto(
            np.zeros((100, 100, 3), dtype=np.uint8)
        )

        self.assertEqual(main.nome_pessoa, "")
        atualizar_estado.assert_called_once_with()
        self.assertFalse(main.reconhecimento_em_andamento)


class TestDesenho(unittest.TestCase):
    @patch("src.main.cv2.rectangle")
    @patch("src.main.cv2.ellipse")
    def test_draw_rounded_retangle(self, ellipse, rectangle):
        imagem = np.zeros((100, 100, 3), dtype=np.uint8)

        main.draw_rounded_retangle(
            imagem, (10, 10), (80, 80), (0, 255, 0)
        )

        self.assertEqual(rectangle.call_count, 2)
        self.assertEqual(ellipse.call_count, 4)


    @patch("src.main.cv2.putText")
    @patch("src.main.cv2.getTextSize", return_value=((100, 20), 5))
    @patch("src.main.cv2.ellipse")
    @patch("src.main.cv2.rectangle")
    def test_put_text(
        self, rectangle, ellipse, get_text_size, put_text
    ):
        imagem = np.zeros((480, 640, 3), dtype=np.uint8)

        main.put_text(imagem, "Caique", 0.25, 2)

        self.assertEqual(get_text_size.call_count, 3)
        self.assertEqual(put_text.call_count, 3)


class TestIniciarAPI(unittest.TestCase):
    @patch("src.main.uvicorn.run")
    def test_iniciar_api(self, executar):
        main.iniciar_api()

        executar.assert_called_once_with(
            main.api.app,
            host="127.0.0.1",
            port=8000,
            log_level="warning"
        )



class TestCamera(unittest.TestCase):
    @patch("src.main.cv2.VideoCapture")
    def test_camera_nao_abre(self, video_capture):
        video_capture.return_value.isOpened.return_value = False

        with self.assertRaises(SystemExit) as erro:
            main.executar_loop_camera()

        self.assertEqual(erro.exception.code, 1)
        video_capture.return_value.release.assert_not_called()


class TestLoopCamera(unittest.TestCase):
    def setUp(self):
        main.atualizar_interface()
        main.reconhecimento_em_andamento = False


    @patch("src.main.cv2.destroyAllWindows")
    @patch("src.main.cv2.waitKey", return_value=27)
    @patch("src.main.cv2.imshow")
    @patch("src.main.cv2.resize", side_effect=lambda frame, tamanho: frame)
    @patch("src.main.cv2.resizeWindow")
    @patch("src.main.cv2.namedWindow")
    @patch("src.main.cv2.VideoCapture")
    def test_exibe_dados_da_pessoa_reconhecida(
        self,
        video_capture,
        named_window,
        resize_window,
        resize,
        imshow,
        wait_key,
        destroy_windows,
    ):
        from unittest.mock import patch

        camera = video_capture.return_value
        camera.isOpened.return_value = True
        camera.read.return_value = (
            True,
            np.zeros((480, 640, 3), dtype=np.uint8),
        )

        main.atualizar_interface("Caique", 0.25, 2)

        with patch("src.main.put_text") as put_text:
            main.executar_loop_camera()

        put_text.assert_called_once()
        self.assertEqual(put_text.call_args.args[1:], ("Caique", 0.25, 2))
        camera.release.assert_called_once()
        destroy_windows.assert_called_once()


    @patch("src.main.cv2.destroyAllWindows")
    @patch("src.main.cv2.waitKey", return_value=0)
    @patch("src.main.cv2.imshow")
    @patch("src.main.cv2.resize", side_effect=lambda frame, tamanho: frame)
    @patch("src.main.cv2.resizeWindow")
    @patch("src.main.cv2.namedWindow")
    @patch("src.main.cv2.VideoCapture")
    def test_falha_ao_capturar_video(
        self,
        video_capture,
        named_window,
        resize_window,
        resize,
        imshow,
        wait_key,
        destroy_windows,
    ):
        camera = video_capture.return_value
        camera.isOpened.side_effect = [True, True]
        camera.read.return_value = (False, None)

        main.executar_loop_camera()

        camera.release.assert_called_once()
        destroy_windows.assert_called_once()
        imshow.assert_not_called()


    @patch("src.main.threading.Thread")
    @patch("src.main.cv2.destroyAllWindows")
    @patch("src.main.cv2.waitKey", return_value=27)
    @patch("src.main.cv2.imshow")
    @patch("src.main.cv2.resize", side_effect=lambda frame, tamanho: frame)
    @patch("src.main.cv2.resizeWindow")
    @patch("src.main.cv2.namedWindow")
    @patch("src.main.cv2.VideoCapture")
    def test_falha_ao_iniciar_thread(
        self,
        video_capture,
        named_window,
        resize_window,
        resize,
        imshow,
        wait_key,
        destroy_windows,
        thread,
    ):
        camera = video_capture.return_value
        camera.isOpened.return_value = True
        camera.read.return_value = (
            True,
            np.zeros((480, 640, 3), dtype=np.uint8),
        )

        thread.return_value.start.side_effect = RuntimeError("Erro simulado")

        # O 15º frame inicia a tentativa de reconhecimento.
        wait_key.side_effect = [0] * 14 + [27]

        main.reconhecimento_em_andamento = False

        main.executar_loop_camera()

        thread.return_value.start.assert_called_once()
        self.assertFalse(main.reconhecimento_em_andamento)
        camera.release.assert_called_once()
        destroy_windows.assert_called_once()


if __name__ == "__main__":
    unittest.main()
