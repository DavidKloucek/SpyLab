from enum import Enum
from typing import List
import cv2
import numpy as np

# import mediapipe as mp
from deepface import DeepFace  # type: ignore
import mediapipe as mp  # type: ignore
import math

MODEL_DEFAULT = "ArcFace"
DETECTOR_BACKEND = "mtcnn"

img_path = "static/img/babishokej.jpeg"

faces_data = DeepFace.represent(img_path=img_path, model_name=MODEL_DEFAULT, detector_backend=DETECTOR_BACKEND)

orig = cv2.imread(img_path)

mp_face_mesh = mp.solutions.face_mesh


def compute_yaw_pitch(face_landmarks, image_w, image_h):
    # Vezmeme důležité body (levé oko, pravé oko, nos)
    # Mediapipe indexy:
    # 33 - pravé oko vnější koutek
    # 263 - levé oko vnější koutek
    # 1 - špička nosu
    # 199 - střed čela

    lm = face_landmarks.landmark

    def get_coords(idx):
        pt = lm[idx]
        return np.array([pt.x * image_w, pt.y * image_h])

    left_eye = get_coords(263)
    right_eye = get_coords(33)
    nose_tip = get_coords(1)
    forehead = get_coords(199)

    # Yaw – úhel mezi očima
    dx = left_eye[0] - right_eye[0]
    dy = left_eye[1] - right_eye[1]
    yaw = math.degrees(math.atan2(dy, dx))

    # Pitch – úhel mezi nosem a čelem
    dx = nose_tip[0] - forehead[0]
    dy = nose_tip[1] - forehead[1]
    pitch = math.degrees(math.atan2(dy, dx))

    return yaw, pitch


def is_facing_forward(face_img, yaw_thresh=20, pitch_thresh=20):
    image_rgb = cv2.cvtColor(face_img, cv2.COLOR_BGR2RGB)
    h, w = image_rgb.shape[:2]

    with mp_face_mesh.FaceMesh(static_image_mode=True, max_num_faces=1, refine_landmarks=False) as face_mesh:
        result = face_mesh.process(image_rgb)

        if not result.multi_face_landmarks:
            exit()
            return False  # žádný obličej rozpoznán

        face_landmarks = result.multi_face_landmarks[0]
        yaw, pitch = compute_yaw_pitch(face_landmarks, w, h)

        # Volitelné ladění:
        print(f"Yaw: {round(yaw)}, Pitch: {round(pitch)}")

        return abs(yaw) < yaw_thresh and abs(pitch) < pitch_thresh


def compute_blur_score(image):
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    laplacian_var = cv2.Laplacian(gray, cv2.CV_64F).var()
    return laplacian_var


def compute_brightness_contrast_score(image):
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    hist = cv2.calcHist([gray], [0], None, [256], [0, 256])
    hist_norm = hist.ravel() / hist.sum()

    brightness = np.sum(hist_norm * np.arange(256))
    contrast = gray.std()

    return brightness, contrast


class ViewMode(Enum):
    ID = 1
    BRIGHTNESS = 2
    CONFIDENCE = 3
    CONTRAST = 4
    BLUR = 5


modes: List[ViewMode] = [
    ViewMode.ID,
    ViewMode.CONFIDENCE,
    ViewMode.BRIGHTNESS,
    ViewMode.CONTRAST,
    ViewMode.BLUR,
]
mode_index = 0
mode = modes[mode_index]

first_iter = True

while True:
    key = cv2.waitKey(500 * 1)
    print(f"Key pressed: {key}")

    if key == 27:
        break
    elif key == 2:
        mode_index = (mode_index - 1) % len(modes)
        mode = modes[mode_index]
    elif key == 3:
        mode_index = (mode_index + 1) % len(modes)
        mode = modes[mode_index]
    elif not first_iter:
        continue

    first_iter = False

    print(mode)

    id = 1

    img = orig.copy()

    cv2.putText(
        img,
        f"Mode: {mode.name}",
        (10, 30),
        cv2.FONT_HERSHEY_SIMPLEX,
        1,
        (0, 255, 255),
        2,
    )

    for data in faces_data:
        x = data["facial_area"]["x"]
        y = data["facial_area"]["y"]
        w = data["facial_area"]["w"]
        h = data["facial_area"]["h"]

        conf_p = float(data["face_confidence"]) * 100

        face_crop = img[y : y + h, x : x + w]

        brightness, contrast = compute_brightness_contrast_score(face_crop)
        blur = compute_blur_score(face_crop)

        img = cv2.rectangle(img, (x, y), (x + w, y + h), (0, 255, 0), thickness=2)
        # img = cv2.putText(img, f"{id}", (int(x+(w/2)-len(str(id))), y-20), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)

        s = f"{id}"
        if mode == ViewMode.BLUR:
            s = f"{round(blur)}"
        if mode == ViewMode.CONFIDENCE:
            s = f"{round(conf_p)}%"
        if mode == ViewMode.BRIGHTNESS:
            s = f"{round(brightness)}"
        if mode == ViewMode.CONTRAST:
            s = f"{round(contrast)}"

        # s = f"{round(conf_p)}%, {round(blur)}, {round(brightness)}, {round(contrast)}"
        ff = is_facing_forward(face_crop)
        print(f"ff {id} / {len(faces_data)}")
        img = cv2.putText(
            img,
            f"{s}; {ff}",
            (int(x + (w / 2) - len(str(s))), y - 20),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.6,
            (0, 255, 0),
            2,
        )

        # s = f"c: {round(conf_p)} bl: {round(blur)} br: {round(brightness)} ct: {round(contrast)}"
        # img = cv2.putText(img, s, (x, y-5), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)

        print(
            f"#{id} | conf: {round(conf_p)}% | blur: {round(blur)} | brightness: {round(brightness)} | contrast: {round(contrast)} | {x}, {y}, {w}, {h}"
        )

        id += 1

        cv2.imshow("Preview", img)


cv2.destroyAllWindows()

print("ok")
