from deepface import DeepFace
import cv2
import os
import tempfile

'''
# principais bibliotecas
deepface
ultralytics
dlib
facenet-pytorch
mediapipe
'''

#os.environ["CUDA_VISIBLE_DEVICES"] = "-1" # desabilitar para utilizar a cpu no lugar da gpu
#DeepFace.stream(db_path="databaseTeste") # teste utilizando a função do proprio deepface

def draw_rounded_retangle(img, top_left, bottom_right, color, radius=10, thickness=-1):
    x1, y1 = top_left
    x2, y2 = bottom_right

    #desenha um retangulo com bordas arredondadas
    cv2.rectangle(img, (x1 + radius, y1), (x2 - radius, y2), color, thickness) # linha superior
    cv2.rectangle(img, (x1, y1 + radius), (x2, y2 - radius), color, thickness) #coluna lateral

    # desenha os cantos arredondados
    cv2.ellipse(img, (x1 + radius, y1 + radius), (radius, radius), 180, 0, 90, color, thickness)
    cv2.ellipse(img, (x2 - radius, y1 + radius), (radius, radius), 270, 0, 90, color, thickness)
    cv2.ellipse(img, (x1 + radius, y2 - radius), (radius, radius), 90, 0, 90, color, thickness)
    cv2.ellipse(img, (x2 - radius, y2 - radius), (radius, radius), 0, 0, 90, color, thickness)

def put_text(frame, name, score):
    text_id = f"ID: {name}"
    text_score = f"Conf: {score:2f}"
    texts = [text_id, text_score]
    font = cv2.FONT_HERSHEY_SIMPLEX
    font_scale = 1
    thickness = 2
    bg_color = (0, 165, 0)
    x_puttext, y_puttext = 20,frame.shape[0] - 100

    # Background
    text_sizes = [cv2.getTextSize(text, font, font_scale, thickness)[0] for text in texts]
    max_text_width = max(width for width, text in text_sizes) + 10
    text_height = sum(height for _, height in text_sizes) + (len(texts) - 1) * 10 + 10

    draw_rounded_retangle(frame,
                          (x_puttext, y_puttext - 10),
                          (x_puttext + max_text_width, y_puttext + text_height),
                          bg_color, radius=10)

    y_offset = 0
    for text in texts:
        cv2.putText(frame, text, (x_puttext + 5,y_puttext + y_offset + 25), font, font_scale, (0, 165, 255), thickness)
        y_offset += text_sizes[0][1] + 10

# abrir camera (640x480)
webcam = cv2.VideoCapture(0)
webcam.set(cv2.CAP_PROP_FRAME_WIDTH, 640) #define a resolução
webcam.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

# definir tamanhos desejados para exibição
display_width, display_height = 320, 240

cv2.namedWindow("Camera", cv2.WINDOW_AUTOSIZE)

while webcam.isOpened():
    # ler as informacoes da webcam
    verificador, frame = webcam.read() # a funcao do opencv retorna um verificador e outra o frame que foi capturado
    if not verificador:     #Se o verificador falhar encerra o programa
        print("Falha ao capturar o video")
        break

    # salvar a imagem temporariamente para o DeepFace
    with tempfile.NamedTemporaryFile(delete=False, suffix='.jpg') as temp_file:
        temp_file_path = temp_file.name
        cv2.imwrite(temp_file_path, frame)

    # usar o caminho do arquivo temporario no DeepFace
    results = DeepFace.find(img_path=temp_file_path, db_path="database", detector_backend="opencv",   # variavel resposta para salvar no bancode dados
                                enforce_detection=False)
    os.remove(temp_file_path)

    # verifica se há resultados
    if results and not results[0].empty:
        # obtem o caminho da imagem mais proxima encontrada
        first_match_path = results[0].iloc[0]["identity"]
        print(f"results: {results}")

        # extrai apenas o nome do arquivo sem o caminho
        nome_pessoa = first_match_path.split("/")[-1].split("\\")[-1].split(".")[0]
        score = results[0].iloc[0]["distance"]

        put_text(frame, nome_pessoa, score)

        print("Pessoa encontrada:", nome_pessoa)

    else:
        print("nenhuma correspondecia encontrada")

    # redimencionar a imagem para exibição
    frame_resized = cv2.resize(frame, (display_width, display_height))

    # exibir a imagem redimencionada
    cv2.imshow("camera", frame_resized)

    if cv2.waitKey(5) == 27:
        break

# encerra a webcam ao finalizar o programa
webcam.release()
cv2.destroyAllWindows()
