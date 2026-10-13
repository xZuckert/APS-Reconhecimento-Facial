from deepface import DeepFace
import cv2
import os
import tempfile
import threading
import api
import uvicorn
from usuarios import buscar_usuario_por_imagem
from estado import atualizar_estado

# Variáveis globais
LIMITE_DISTANCIA = 0.55
nivel_acesso = 0

def reconhecer_rosto(frame):
    global nome_pessoa, score
    global reconhecimento_em_andamento, nivel_acesso

    temp_file_path = None

    try:
        # Salvar a imagem temporariamente
        with tempfile.NamedTemporaryFile(
            delete=False, suffix=".jpg"
        ) as temp_file:
            temp_file_path = temp_file.name
            cv2.imwrite(temp_file_path, frame)

        # Fazer o reconhecimento
        results = DeepFace.find(
            img_path=temp_file_path,
            db_path="database",
            detector_backend="opencv",
            enforce_detection=False
        )

        # Verificar os resultados
        if results and not results[0].empty:
            first_match = results[0].iloc[0]
            distancia = first_match["distance"]

            if distancia <= LIMITE_DISTANCIA:
                first_match_path = first_match["identity"]
                #print("Imagem reconhecida:", os.path.realpath(first_match_path))
                usuario = buscar_usuario_por_imagem(first_match_path)

                if usuario:
                    id_usuario, cpf, nome, nivel = usuario

                    nome_pessoa = nome
                    score = distancia
                    nivel_acesso = nivel

                    atualizar_estado(
                        autenticado=True,
                        usuario=nome_pessoa,
                        nivel_acesso=nivel_acesso,
                        distancia=float(score)
                    )

                    print("Pessoa encontrada:", nome_pessoa)
                    print("Distância:", round(score, 3))
                    print("Nível de acesso:", nivel_acesso)

                else:
                    nome_pessoa = ""
                    score = 0
                    nivel_acesso = 0

                    atualizar_estado()

                    print("Pessoa reconhecida, mas não cadastrada no banco.")

            else:
                nome_pessoa = ""
                score = 0
                nivel_acesso = 0

                atualizar_estado()

                print(
                    "Pessoa não identificada. Distância:",
                    round(distancia, 3)
                )

        else:
            nome_pessoa = ""
            score = 0
            nivel_acesso = 0

            atualizar_estado()

            print("Nenhuma correspondência encontrada")

    except Exception as erro:
        nome_pessoa = ""
        score = 0
        nivel_acesso = 0

        atualizar_estado()

        print("Erro no reconhecimento:", erro)

    finally:
        if temp_file_path and os.path.exists(temp_file_path):
            os.remove(temp_file_path)

        reconhecimento_em_andamento = False


def draw_rounded_retangle(
    img, top_left, bottom_right, color,
    radius=10, thickness=-1
):
    x1, y1 = top_left
    x2, y2 = bottom_right

    cv2.rectangle(
        img, (x1 + radius, y1),
        (x2 - radius, y2), color, thickness
    )
    cv2.rectangle(
        img, (x1, y1 + radius),
        (x2, y2 - radius), color, thickness
    )

    cv2.ellipse(
        img, (x1 + radius, y1 + radius),
        (radius, radius), 180, 0, 90, color, thickness
    )
    cv2.ellipse(
        img, (x2 - radius, y1 + radius),
        (radius, radius), 270, 0, 90, color, thickness
    )
    cv2.ellipse(
        img, (x1 + radius, y2 - radius),
        (radius, radius), 90, 0, 90, color, thickness
    )
    cv2.ellipse(
        img, (x2 - radius, y2 - radius),
        (radius, radius), 0, 0, 90, color, thickness
    )


def put_text(frame, name, score, nivel_acesso):
    texts = [
        f"ID: {name}",
        f"Distância: {score:.3f}",
        f"Nível de acesso: {nivel_acesso}"
    ]

    font = cv2.FONT_HERSHEY_SIMPLEX
    font_scale = 0.6
    thickness = 2
    bg_color = (0, 165, 0)
    text_color = (0, 165, 255)

    # Calcular o tamanho de todas as linhas
    text_sizes = [
        cv2.getTextSize(text, font, font_scale, thickness)[0]
        for text in texts
    ]

    max_text_width = max(width for width, _ in text_sizes) + 20
    text_height = sum(height for _, height in text_sizes)
    text_height += (len(texts) - 1) * 10 + 20

    # Posicionar o painel na parte inferior
    x_puttext = 20
    y_puttext = frame.shape[0] - text_height - 30

    draw_rounded_retangle(
        frame,
        (x_puttext, y_puttext - 10),
        (x_puttext + max_text_width, y_puttext + text_height),
        bg_color,
        radius=10
    )

    y_offset = 0

    for text, (_, height) in zip(texts, text_sizes):
        cv2.putText(
            frame,
            text,
            (x_puttext + 10, y_puttext + y_offset + height),
            font,
            font_scale,
            text_color,
            thickness
        )

        y_offset += height + 10

def iniciar_api():
    uvicorn.run(
        api.app,
        host="127.0.0.1",
        port=8000,
        log_level="warning"
    )

threading.Thread(
    target=iniciar_api,
    daemon=True
).start()

# Abrir câmera
webcam = cv2.VideoCapture(0)
webcam.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
webcam.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

# Tamanho da janela
display_width, display_height = 320, 240

cv2.namedWindow("Camera", cv2.WINDOW_NORMAL)
cv2.resizeWindow("Camera", display_width, display_height)

frame_count = 0
nome_pessoa = ""
score = 0
reconhecimento_em_andamento = False

while webcam.isOpened():
    verificador, frame = webcam.read()
    frame_count += 1

    if not verificador:
        print("Falha ao capturar o vídeo")
        break

    # Iniciar reconhecimento a cada 15 frames
    if (
        frame_count % 15 == 0
        and not reconhecimento_em_andamento
    ):
        reconhecimento_em_andamento = True

        thread = threading.Thread(
            target=reconhecer_rosto,
            args=(frame.copy(),)
        )

        thread.start()

    # Exibir as informações da pessoa identificada
    if nome_pessoa:
        put_text(frame, nome_pessoa, score, nivel_acesso)

    frame_resized = cv2.resize(
        frame, (display_width, display_height)
    )

    cv2.imshow("Camera", frame_resized)

    if cv2.waitKey(5) == 27:
        break

# Encerrar a câmera
webcam.release()
cv2.destroyAllWindows()