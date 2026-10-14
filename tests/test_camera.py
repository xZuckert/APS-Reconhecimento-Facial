import os
import subprocess
import sys
import unittest
from pathlib import Path
import textwrap

PROJETO = Path(__file__).resolve().parent.parent

class TestCamera(unittest.TestCase):
    def executar_main(self, codigo_camera):
        codigo_camera = textwrap.dedent(codigo_camera).strip()

        codigo_base = textwrap.dedent(f"""\
            import runpy
            import sys
            import cv2
            from unittest.mock import MagicMock, patch

            sys.path.insert(0, {str(PROJETO / "src")!r})
            sys.path.insert(0, {str(PROJETO)!r})

            sys.modules["api"] = MagicMock()
            sys.modules["uvicorn"] = MagicMock()
            sys.modules["deepface"] = MagicMock(
                DeepFace=MagicMock()
            )

            with patch.object(cv2, "VideoCapture") as captura:
                camera = captura.return_value
                # CONFIGURACAO_CAMERA

                try:
                    runpy.run_module("src.main", run_name="__main__")
                except SystemExit as erro:
                    print("CODIGO_SAIDA:", erro.code)
        """)

        codigo_camera = textwrap.indent(codigo_camera, "    ")

        codigo = codigo_base.replace(
            "    # CONFIGURACAO_CAMERA",
            codigo_camera,
        )

        ambiente = os.environ.copy()
        ambiente["PYTHONPATH"] = os.pathsep.join([
            str(PROJETO / "src"),
            str(PROJETO),
        ])

        return subprocess.run(
            [sys.executable, "-c", codigo],
            cwd=PROJETO,
            env=ambiente,
            capture_output=True,
            text=True,
            timeout=15,
        )


    def test_camera_nao_abre(self):
        resultado = self.executar_main(
            "camera.isOpened.return_value = False"
        )

        saida = resultado.stdout + resultado.stderr

        self.assertIn(
            "Não foi possível abrir a câmera.",
            saida,
            msg=(
                f"Processo terminou com código {resultado.returncode}.\n"
                f"STDOUT:\n{resultado.stdout}\n"
                f"STDERR:\n{resultado.stderr}"
            ),
        )


    def test_falha_ao_capturar_video(self):
        resultado = self.executar_main(
            "camera.isOpened.return_value = True\n"
            "camera.read.return_value = (False, None)"
        )

        saida = resultado.stdout + resultado.stderr

        self.assertIn(
            "Falha ao capturar o vídeo",
            saida,
            msg=(
                f"Processo terminou com código {resultado.returncode}.\n"
                f"Saída do processo:\n{saida}"
            ),
        )


if __name__ == "__main__":
    unittest.main()