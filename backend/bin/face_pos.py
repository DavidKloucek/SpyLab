import cv2
import numpy as np
import mediapipe as mp  # type: ignore
# from deepface import DeepFace # type: ignore

mp_face_mesh = mp.solutions.face_mesh
face_mesh = mp_face_mesh.FaceMesh(static_image_mode=False, max_num_faces=1)


def get_head_pose(image):
    h, w, _ = image.shape
    img_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    results = face_mesh.process(img_rgb)

    if not results.multi_face_landmarks:
        return None

    face_landmarks = results.multi_face_landmarks[0].landmark

    # 2D body (pořadí: nos, levé oko, pravé oko, levý koutek úst, pravý koutek úst, brada)
    image_points = np.array(
        [
            (face_landmarks[1].x * w, face_landmarks[1].y * h),  # Nos
            (face_landmarks[33].x * w, face_landmarks[33].y * h),  # Levé oko
            (face_landmarks[263].x * w, face_landmarks[263].y * h),  # Pravé oko
            (face_landmarks[61].x * w, face_landmarks[61].y * h),  # Levý koutek úst
            (face_landmarks[291].x * w, face_landmarks[291].y * h),  # Pravý koutek úst
            (face_landmarks[152].x * w, face_landmarks[152].y * h),  # Brada
        ],
        dtype="double",
    )

    # Odpovídající 3D body (model obličeje v reálném světě, předpokládané souřadnice)
    model_points = np.array(
        [
            (0.0, 0.0, 0.0),  # Nos
            (-30.0, 20.0, -30.0),  # Levé oko
            (30.0, 20.0, -30.0),  # Pravé oko
            (-40.0, -20.0, -30.0),  # Levý koutek úst
            (40.0, -20.0, -30.0),  # Pravý koutek úst
            (0.0, -50.0, -20.0),  # Brada
        ],
        dtype="double",
    )

    focal_length = w
    camera_matrix = np.array([[focal_length, 0, w / 2], [0, focal_length, h / 2], [0, 0, 1]], dtype="double")

    _, rotation_vector, _ = cv2.solvePnP(model_points, image_points, camera_matrix, None)

    # Převod rotace na Eulerovy úhly
    rmat, _ = cv2.Rodrigues(rotation_vector)
    yaw, pitch, roll = cv2.decomposeProjectionMatrix(np.hstack((rmat, np.zeros((3, 1)))))[-1]

    return yaw[0], pitch[0], roll[0]


# Testovací kód pro video
cap = cv2.VideoCapture("./backend/bin/IMG_2205.MP4")
while cap.isOpened():
    ret, frame = cap.read()
    frame = cv2.rotate(frame, cv2.ROTATE_90_CLOCKWISE)
    if not ret:
        break

    angles = get_head_pose(frame)
    if angles:
        yaw, pitch, roll = angles
        cv2.putText(
            frame,
            f"Yaw: {yaw:.2f}, Pitch: {pitch:.2f}, Roll: {roll:.2f}",
            (50, 50),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.7,
            (0, 255, 0),
            2,
        )

    cv2.imshow("Head Pose", frame)
    if cv2.waitKey(100) & 0xFF == ord("q"):
        break

cap.release()
cv2.destroyAllWindows()
