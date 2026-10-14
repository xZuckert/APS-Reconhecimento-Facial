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


    @patch("src.main.cv2.imwrite", return_value=True)
    @patch("src.main.DeepFace.find")
    @patch("src.main.buscar_usuario_por_imagem")
    @patch("src.main.atualizar_estado")
    def test_usuario_reconhecido(
        self, atualizar_estado, buscar_usuario, deepface, imwrite
    ):
        resultados = pd.DataFrame([
            {"distance": 0.30, "identity": "/imagem.jpg"}
        ])
        deepface.return_value = [resultados]
        buscar_usuario.return_value = (1, "12345678901", "Caique", 2)

        main.reconhecer_rosto(np.zeros((100, 100, 3), dtype=np.uint8))

        self.assertEqual(main.nome_pessoa, "Caique")
        self.assertEqual(main.nivel_acesso, 2)
        atualizar_estado.assert_called_once_with(
            autenticado=True,
            usuario="Caique",
            nivel_acesso=2,
            distancia=0.30
        )


    @patch("src.main.cv2.imwrite", return_value=True)
    @patch("src.main.DeepFace.find")
    @patch("src.main.atualizar_estado")
    def test_nenhuma_correspondencia(
        self, atualizar_estado, deepface, imwrite
    ):
        deepface.return_value = [pd.DataFrame()]

        main.reconhecer_rosto(np.zeros((100, 100, 3), dtype=np.uint8))

        self.assertEqual(main.nome_pessoa, "")
        atualizar_estado.assert_called_once_with()


    @patch("src.main.cv2.imwrite", return_value=False)
    @patch("src.main.atualizar_estado")
    def test_falha_ao_salvar_frame(self, atualizar_estado, imwrite):
        main.reconhecer_rosto(np.zeros((100, 100, 3), dtype=np.uint8))

        self.assertEqual(main.nome_pessoa, "")
        atualizar_estado.assert_called_once_with()
        self.assertFalse(main.reconhecimento_em_andamento)


    def test_reconhecimento_libera_estado_ao_finalizar(self):
        with patch("src.main.cv2.imwrite", side_effect=RuntimeError("erro")):
            main.reconhecer_rosto(np.zeros((100, 100, 3), dtype=np.uint8))

        self.assertFalse(main.reconhecimento_em_andamento)


    @patch("src.main.cv2.imwrite", return_value=True)
    @patch("src.main.DeepFace.find")
    @patch("src.main.buscar_usuario_por_imagem", return_value=None)
    @patch("src.main.atualizar_estado")
    def test_usuario_reconhecido_mas_nao_cadastrado(
            self, atualizar_estado, buscar_usuario, deepface, imwrite
    ):
        resultados = pd.DataFrame([
            {"distance": 0.30, "identity": "/imagem.jpg"}
        ])
        deepface.return_value = [resultados]

        main.reconhecer_rosto(
            np.zeros((100, 100, 3), dtype=np.uint8)
        )

        self.assertEqual(main.nome_pessoa, "")
        self.assertEqual(main.score, 0)
        self.assertEqual(main.nivel_acesso, 0)
        buscar_usuario.assert_called_once_with("/imagem.jpg")
        atualizar_estado.assert_called_once_with()


    @patch("src.main.cv2.imwrite", return_value=True)
    @patch("src.main.DeepFace.find")
    @patch("src.main.buscar_usuario_por_imagem")
    @patch("src.main.atualizar_estado")
    def test_distancia_acima_do_limite(
            self, atualizar_estado, buscar_usuario, deepface, imwrite
    ):
        resultados = pd.DataFrame([
            {"distance": 0.80, "identity": "/imagem.jpg"}
        ])
        deepface.return_value = [resultados]

        main.atualizar_interface("Pessoa anterior", 0.20, 1)

        main.reconhecer_rosto(
            np.zeros((100, 100, 3), dtype=np.uint8)
        )

        self.assertEqual(main.nome_pessoa, "")
        self.assertEqual(main.score, 0)
        self.assertEqual(main.nivel_acesso, 0)
        buscar_usuario.assert_not_called()
        atualizar_estado.assert_called_once_with()


    @patch("src.main.cv2.imwrite", return_value=True)
    @patch("src.main.DeepFace.find")
    @patch("src.main.buscar_usuario_por_imagem", return_value=None)
    @patch("src.main.atualizar_estado")
    def test_usuario_reconhecido_mas_nao_cadastrado(
        self, atualizar_estado, buscar_usuario, deepface, imwrite
    ):
        resultados = pd.DataFrame([
            {"distance": 0.30, "identity": "/imagem.jpg"}
        ])
        deepface.return_value = [resultados]

        main.reconhecer_rosto(
            np.zeros((100, 100, 3), dtype=np.uint8)
        )

        self.assertEqual(main.nome_pessoa, "")
        self.assertEqual(main.score, 0)
        self.assertEqual(main.nivel_acesso, 0)
        buscar_usuario.assert_called_once_with("/imagem.jpg")
        atualizar_estado.assert_called_once_with()


    @patch("src.main.cv2.imwrite", return_value=True)
    @patch("src.main.DeepFace.find")
    @patch("src.main.buscar_usuario_por_imagem")
    @patch("src.main.atualizar_estado")
    def test_distancia_acima_do_limite(
        self, atualizar_estado, buscar_usuario, deepface, imwrite
    ):
        resultados = pd.DataFrame([
            {"distance": 0.80, "identity": "/imagem.jpg"}
        ])
        deepface.return_value = [resultados]

        main.atualizar_interface("Pessoa anterior", 0.20, 1)

        main.reconhecer_rosto(
            np.zeros((100, 100, 3), dtype=np.uint8)
        )

        self.assertEqual(main.nome_pessoa, "")
        self.assertEqual(main.score, 0)
        self.assertEqual(main.nivel_acesso, 0)
        buscar_usuario.assert_not_called()
        atualizar_estado.assert_called_once_with()


    @patch("src.main.os.remove", side_effect=OSError("Erro simulado"))
    @patch("src.main.os.path.exists", return_value=True)
    @patch("src.main.cv2.imwrite", return_value=False)
    @patch("src.main.atualizar_estado")
    def test_falha_ao_remover_arquivo_temporario(
        self, atualizar_estado, imwrite, arquivo_existe, remover
    ):
        main.reconhecer_rosto(
            np.zeros((100, 100, 3), dtype=np.uint8)
        )

        remover.assert_called_once()
        atualizar_estado.assert_called()
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
