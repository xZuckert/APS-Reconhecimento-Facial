import cv2 #opencv = controlar webcam e carregar imagem
import mediapipe as mp #face detection
from pathlib import Path

#inicializar opencv e mediapipe
webcam = cv2.VideoCapture(0)

# deteccao de rostos com o mediapipe
BaseOptions = mp.tasks.BaseOptions
FaceDetector = mp.tasks.vision.FaceDetector
FaceDetectorOptions = mp.tasks.vision.FaceDetectorOptions

# carrega o modelo baixado do mediapipe para deteccao facial
BASE_DIR = Path(__file__).resolve().parent.parent
MODEL_PATH = BASE_DIR / "models" / "blaze_face_short_range.tflite"
options = FaceDetectorOptions(
    base_options=BaseOptions(
        model_asset_path=str(MODEL_PATH)
    )
)
print(MODEL_PATH)
detector = FaceDetector.create_from_options(options)

while True:
    # ler as informacoes da webcam
    verificador, frame = webcam.read() # a funcao do opencv retorna um verificador e outra o frame que foi capturado
    if not verificador: #Se o verificador falhar encerra o programa
        break

    # detectar os rostos
    frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    imagem = mp.Image(
        image_format=mp.ImageFormat.SRGB,
        data=frame_rgb
    )
    resultado = detector.detect(imagem)

    # mostra as marcacoes da deteccao
    if resultado.detections:
        for rosto in resultado.detections:
            caixa = rosto.bounding_box
            x = caixa.origin_x
            y = caixa.origin_y
            largura = caixa.width
            altura = caixa.height
            cv2.rectangle(
                frame,
                (x, y),
                (x + largura, y + altura),
                (0, 255, 0),
                2
            )
            for ponto in rosto.keypoints:
                px = int(ponto.x * frame.shape[1])
                py = int(ponto.y * frame.shape[0])

                cv2.circle(
                    frame,
                    (px, py),
                    4,
                    (0, 0, 255),
                    -1
                )
    cv2.imshow("APS Reconhecimento Facial", frame)



    # ESC = sair do loop
    if cv2.waitKey(5) == 27: # a tecla 27 = ESC
        break

# encerra a webcam ao finalizar o programa
webcam.release()
cv2.destroyAllWindows()