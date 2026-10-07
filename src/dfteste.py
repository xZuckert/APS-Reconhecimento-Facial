from deepface import DeepFace


'''
deepface
ultralytics
dlib
facenet-pytorch
mediapipe
'''

models = [
    "VGG-Face",
    "Facenet",
    "Facenet512",
    "OpenFace",
    "DeepFace",
    "DeepID",
    "ArcFace",
    "Dlib",
    "SFace",
    "GhostFaceNet"
]

backend = [
    "opencv",
    "ssd",
    "dlib",
    "mtcnn",
    "fastmmtcnn",
    "retinaface",
    "mediapipe",
    "yolov8",
    "yunet",
    "centerface"
]

result = DeepFace.verify(
    img1_path="ImagensTeste/img5.jpg",
    img2_path="ImagensTeste/img3.jpg",
    model_name=models[0],
    enforce_detection=False,
    detector_backend=backend[0],
)

print(result)
