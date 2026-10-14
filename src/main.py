from deepface import DeepFace
from threading import Lock
from pathlib import Path
import cv2
import os
import tempfile
import threading
import api
import uvicorn
from usuarios import listar_imagens_usuarios
from estado import atualizar_estado

# Variáveis globais
estado_interface_lock = Lock()
reconhecimento_lock = Lock()
LIMITE_DISTANCIA = 0.55
nome_pessoa = ""
score = 0
nivel_acesso = 0
reconhecimento_em_andamento = False

BASE_DIR = Path(__file__).resolve().parent.parent
DATABASE_DIR = BASE_DIR / "database"


def atualizar_interface(nome="", distancia=0, nivel=0):
    global nome_pessoa, score, nivel_acesso

    # Atualizar as informações exibidas na câmera
    with estado_interface_lock:
        nome_pessoa = nome
        score = distancia
        nivel_acesso = nivel




def reconhecer_rosto(frame):
    global reconhecimento_em_andamento

    try:
        # Buscar no banco os usuários ativos que possuem imagem cadastrada.
        usuarios = listar_imagens_usuarios()

        # Associar cada ID aos dados do usuário para localizar rapidamente quem corresponde à imagem reconhecida.
        usuarios_por_id = {
            str(usuario_id): (usuario_id, cpf, nome, nivel)
            for usuario_id, cpf, nome, nivel, imagem in usuarios
        }

        # Encerrar a busca quando não houver imagens de referência.
        if not usuarios_por_id:
            atualizar_interface()
            atualizar_estado()
            print("Nenhum usuário possui imagem cadastrada no banco.")
            return

        # Criar uma pasta temporária para preparar as imagens do DeepFace. Os arquivos serão removidos automaticamente ao sair deste bloco.
        with tempfile.TemporaryDirectory() as temp_dir:
            pasta_temp = Path(temp_dir)
            pasta_referencias = pasta_temp / "referencias"
            pasta_referencias.mkdir()

            # Gravar temporariamente as imagens recuperadas do PostgreSQL. O nome do arquivo corresponde ao ID do usuário.
            for usuario_id, cpf, nome, nivel, imagem in usuarios:
                if not imagem:
                    continue

                caminho = pasta_referencias / f"{usuario_id}.jpg"
                caminho.write_bytes(imagem)

            # Salvar temporariamente o frame capturado pela câmera.
            caminho_frame = pasta_temp / "captura.jpg"

            if not cv2.imwrite(str(caminho_frame), frame):
                raise RuntimeError(
                    "Não foi possível salvar o frame temporário."
                )

            # Comparar o rosto capturado com as imagens de referência.
            results = DeepFace.find(
                img_path=str(caminho_frame),
                db_path=str(pasta_referencias),
                detector_backend="opencv",
                enforce_detection=True
            )

            # Verificar se o DeepFace encontrou alguma correspondência.
            if results and not results[0].empty:
                first_match = results[0].iloc[0]
                distancia = float(first_match["distance"])

                # Aceitar a correspondência somente se estiver dentro do limite de distância definido para o projeto.
                if distancia <= LIMITE_DISTANCIA:
                    caminho_identidade = Path(
                        str(first_match["identity"])
                    )

                    # Recuperar o ID pelo nome do arquivo de referência.
                    id_encontrado = caminho_identidade.stem
                    usuario = usuarios_por_id.get(id_encontrado)

                    if usuario:
                        id_usuario, cpf, nome, nivel = usuario

                        # Atualizar a interface e o estado de autenticação.
                        atualizar_interface(nome, distancia, nivel)
                        atualizar_estado(
                            autenticado=True,
                            usuario=nome,
                            nivel_acesso=nivel,
                            distancia=distancia
                        )

                        print("Pessoa encontrada:", nome)
                        print("Distância:", round(distancia, 3))
                        print("Nível de acesso:", nivel)
                    else:
                        # Limpar o estado caso a referência não corresponda a um usuário retornado pelo banco.
                        atualizar_interface()
                        atualizar_estado()
                        print("Correspondência sem usuário cadastrado.")
                else:
                    # Limpar os dados quando a distância exceder o limite.
                    atualizar_interface()
                    atualizar_estado()
                    print(
                        "Pessoa não identificada. Distância:",
                        round(distancia, 3)
                    )
            else:
                # Limpar os dados quando nenhuma correspondência for obtida.
                atualizar_interface()
                atualizar_estado()
                print("Nenhuma correspondência encontrada")

    except Exception as erro:
        # Garantir que uma falha não mantenha dados de autenticação antigos.
        atualizar_interface()
        atualizar_estado()

        # Não exibir como erro inesperado a ausência de um rosto no frame.
        if "Face could not be detected" not in str(erro):
            print(f"Erro no reconhecimento: {erro}")

    finally:
        # Liberar o reconhecimento para permitir a próxima execução.
        with reconhecimento_lock:
            reconhecimento_em_andamento = False


def draw_rounded_retangle(
    img, top_left, bottom_right, color,
    radius=10, thickness=-1
):
    # Definir as coordenadas do retângulo
    x1, y1 = top_left
    x2, y2 = bottom_right

    # Desenhar as partes retas do retângulo
    cv2.rectangle(
        img, (x1 + radius, y1),
        (x2 - radius, y2), color, thickness
    )
    cv2.rectangle(
        img, (x1, y1 + radius),
        (x2, y2 - radius), color, thickness
    )

    # Desenhar os cantos arredondados
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
    # Definir as informações que serão exibidas
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

    # Desenhar o fundo do painel
    draw_rounded_retangle(
        frame,
        (x_puttext, y_puttext - 10),
        (x_puttext + max_text_width, y_puttext + text_height),
        bg_color,
        radius=10
    )

    # Exibir cada linha de texto
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
    # Iniciar o servidor da API
    uvicorn.run(
        api.app,
        host="127.0.0.1",
        port=8000,
        log_level="warning"
    )


# Executar a API em uma thread separada
threading.Thread(
    target=iniciar_api,
    daemon=True
).start()


def executar_loop_camera():
    global reconhecimento_em_andamento

    # Abrir câmera
    webcam = cv2.VideoCapture(0)

    if not webcam.isOpened():
        print("Não foi possível abrir a câmera.")
        raise SystemExit(1)

    # Definir a resolução da câmera
    webcam.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    webcam.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

    # Definir o tamanho da janela
    display_width, display_height = 320, 240

    frame_count = 0

    try:
        # Criar e dimensionar a janela da câmera
        cv2.namedWindow("Camera", cv2.WINDOW_NORMAL)
        cv2.resizeWindow("Camera", display_width, display_height)

        while webcam.isOpened():
            # Capturar um frame da câmera
            verificador, frame = webcam.read()

            if not verificador:
                print("Falha ao capturar o vídeo")
                break

            frame_count += 1

            # Iniciar reconhecimento a cada 15 frames
            if frame_count % 15 == 0:
                iniciar_reconhecimento = False

                with reconhecimento_lock:
                    if not reconhecimento_em_andamento:
                        reconhecimento_em_andamento = True
                        iniciar_reconhecimento = True

                if iniciar_reconhecimento:
                    try:
                        # Executar o reconhecimento em uma thread separada
                        thread = threading.Thread(
                            target=reconhecer_rosto,
                            args=(frame.copy(),)
                        )
                        thread.start()

                    except Exception as erro:
                        # Liberar o reconhecimento caso a thread não inicie
                        with reconhecimento_lock:
                            reconhecimento_em_andamento = False

                        print("Erro ao iniciar reconhecimento:", erro)

            # Obter as informações atuais da pessoa reconhecida
            with estado_interface_lock:
                nome_atual = nome_pessoa
                score_atual = score
                nivel_atual = nivel_acesso

            # Exibir as informações da pessoa identificada
            if nome_atual:
                put_text(frame, nome_atual, score_atual, nivel_atual)

            # Redimensionar e exibir o vídeo
            frame_resized = cv2.resize(
                frame, (display_width, display_height)
            )

            cv2.imshow("Camera", frame_resized)

            # Encerrar a execução ao pressionar ESC
            if cv2.waitKey(5) == 27:
                break

    finally:
        # Encerrar a câmera e fechar as janelas
        webcam.release()
        cv2.destroyAllWindows()


if __name__ == "__main__":
    executar_loop_camera()
