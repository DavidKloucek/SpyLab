from deepface import DeepFace  # type: ignore
from deepface.modules import verification  # type: ignore
import numpy as np
from app.helpers import normalize

models = ["Facenet", "Facenet512", "VGG-Face", "ArcFace"]

imgpath = "../static/img/"

img1 = imgpath + "xxx.jpg"
img2 = imgpath + "yyy.jpg"
images = [img1, img2]

for model in models:
    print(f"=== Model: {model}")
    x = {}
    i = 0

    repr1 = DeepFace.represent(img_path=img1, model_name=model)[0]
    repr2 = DeepFace.represent(img_path=img2, model_name=model)[0]
    verify_euc_l2 = DeepFace.verify(img1_path=img1, img2_path=img2, distance_metric="euclidean_l2")
    verify_euc = DeepFace.verify(img1_path=img1, img2_path=img2, distance_metric="euclidean")
    verify_cos = DeepFace.verify(img1_path=img1, img2_path=img2, distance_metric="cosine")

    embedding1 = np.array(repr1["embedding"])
    embedding2 = np.array(repr2["embedding"])
    embedding1_norm = embedding1 / np.linalg.norm(embedding1)
    embedding2_norm = embedding2 / np.linalg.norm(embedding2)

    cosine_similarity = np.dot(embedding1, embedding2) / (np.linalg.norm(embedding1) * np.linalg.norm(embedding2))
    cosine_similarity_norm = np.dot(embedding1_norm, embedding2_norm)

    euclidean_distance = np.linalg.norm(embedding1 - embedding2)

    d = np.linalg.norm(normalize(embedding1) - normalize(embedding2))

    x = verification.find_distance(embedding1, embedding2, "cosine")
    x2 = verification.find_distance(embedding1_norm, embedding2_norm, "cosine")

    r = 2
    print("Kosinová", round(verify_cos["distance"], r))
    print("cosine_similarity:", round(1 - cosine_similarity, r))
    print("cosine_similarity_norm:", round(1 - cosine_similarity_norm, r))
    # print("cosine_distance:", round(cosine_distance, r))
    # print("x:", round(x, r))
    # print("x2:", round(x2, r))

    print("Euklidovská custom:", round(euclidean_distance, r))
    print("Euklidovská + norm. custom:", round(d, r))
    print("Euklidovská", round(verify_euc["distance"], r))
    print("Euklidovská L2", round(verify_euc_l2["distance"], r))

    print("verified", verify_euc_l2["verified"])
    print("threshold", verify_euc_l2["threshold"])

    if 0:
        print("similarity_metric", verify_euc_l2["similarity_metric"])
        print("detector_backend", verify_euc_l2["detector_backend"])
        print("time", verify_euc_l2["time"])
    # print(json.dumps(verify, indent=4))

    print("")

    # break

"""
SELECT
    (dot_product(embedding1, embedding2)) / (norm(embedding1) * norm(embedding2)) AS cosine_similarity
FROM
    face_embeddings;
"""
