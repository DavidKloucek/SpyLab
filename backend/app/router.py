from wireup import Injected
from typing import Any, List
from fastapi import APIRouter, Depends, File, Form, HTTPException, Response, UploadFile
from pydantic import BaseModel
from app import face_service
from app.auth_service import AuthService, oauth2_scheme
from app.dashboard_service import DashboardService, DashStats
from app.face_service import AnalyzeBox, FaceItem, FaceSimilarItem, NoFaceFound
from fastapi import Request
from app.face_service import FaceService
from app.user_repository import UserRepository

"""
todo: verify password
todo: refresh tokens
todo: protect routes
"""

router = APIRouter()


class FaceSimilarItemResponse(FaceSimilarItem):
    preview_url: str
    source_url: str


class FaceItemResponse(FaceItem):
    preview_url: str
    source_url: str


class DetailData(BaseModel):
    data: FaceItemResponse
    faces: List[FaceItemResponse]


@router.get("/detail")
async def detail_image(
    request: Request,
    id: int,
    face_service: Injected[face_service.FaceService],
) -> DetailData:

    data = await face_service.get_by_id(id)

    data_resp = FaceItemResponse(
        **data.model_dump(),
        preview_url=f"{str(request.base_url)}preview/{data.preview_path}",
        source_url=f"{str(request.base_url)}source_img/{data.source_filepath}")

    faces_resp = [
        FaceItemResponse(
            **item.model_dump(),
            preview_url=f"{str(request.base_url)}preview/{item.preview_path}",
            source_url=f"{str(request.base_url)}source_img/{item.source_filepath}"
        )
        for item in await face_service.get_photo_faces_by_filename(data.fn) if item.model == data.model
    ]

    return DetailData(data=data_resp, faces=faces_resp)


@router.get("/list")
async def read_random(
    request: Request,
    response: Response,
    face_service: Injected[FaceService],
    search: str = '',
    limit: int = 20,
) -> List[FaceItemResponse]:

    res = await face_service.find_list(limit, search)
    return [
        FaceItemResponse(
            **item.model_dump(),
            preview_url=f"{str(request.base_url)}preview/{item.preview_path}",
            source_url=f"{str(request.base_url)}source_img/{item.source_filepath}")
        for item in res
    ]


class Pagination(BaseModel):
    total: int
    pageCount: int


class Meta(BaseModel):
    pagination: Pagination


class FaceItemResponseContainer(BaseModel):
    data: List[FaceItemResponse]
    meta: Meta


class ImageData(BaseModel):
    name: str


class UploadImageResponse(BaseModel):
    preview_url: str
    source_url: str
    boxes: List[AnalyzeBox]


@router.post("/analyze")
async def analyze_image(
    request: Request,
    face_service: Injected[FaceService],
    file: UploadFile = File(...),
) -> UploadImageResponse:

    try:
        data = await face_service.analyze_image(file)

        return UploadImageResponse(
            boxes=data,
            preview_url=f"{str(request.base_url)}preview/",
            source_url=f"{str(request.base_url)}source_img/")
    except NoFaceFound as e:
        # todo
        raise HTTPException(
            status_code=500, detail="No face detected in the image")


@router.get("/similar-to-id")
async def find_similar_id(
    request: Request,
    face_service: Injected[FaceService],
    id: int,
    model: str,
    metric: str = 'cosine',
) -> List[FaceSimilarItemResponse]:

    res = await face_service.find_similar_by_face_id(id=id, model=model, metric=metric, limit=50)

    return [
        FaceSimilarItemResponse(
            **item.model_dump(),
            preview_url=f"{str(request.base_url)}preview/{item.preview_path}",
            source_url=f"{str(request.base_url)}source_img/{item.source_filepath}")
        for item in res
    ]


@router.post("/similar-to-image")
async def find_similar_image(
    request: Request,
    image: UploadFile,
    face_service: Injected[FaceService],
    x: int = Form(...),
    y: int = Form(...),
    w: int = Form(...),
    h: int = Form(...),
) -> List[FaceSimilarItemResponse]:
    res = await face_service.find_similar_by_image(file=image, x=x, y=y, w=w, h=h, limit=100)

    return [
        FaceSimilarItemResponse(
            **item.model_dump(),
            preview_url=f"{str(request.base_url)}preview/{item.preview_path}",
            source_url=f"{str(request.base_url)}source_img/{item.source_filepath}")
        for item in res
    ]


@router.get("/dashboard")
async def dashboard(
    dashboard_service: Injected[DashboardService],
) -> DashStats:
    data = await dashboard_service.get_stats()
    return data


class UserItem(BaseModel):
    id: int
    email: str


@router.get("/users")
async def user_list(
    request: Request,
    response: Response,
    user_repo: Injected[UserRepository],
    _start: int = 0,
    _end: int = 20
) -> List[Any]:

    data = await user_repo.find_all(_start, _end)
    res = [
        UserItem(id=u.id, email=u.email)
        for u in data
    ]

    total_count = len(res)
    response.headers["X-Total-Count"] = str(total_count)
    response.headers["Access-Control-Expose-Headers"] = "X-Total-Count"
    return res


class LoginRequest(BaseModel):
    email: str
    password: str


@router.post("/login")
async def login(
    request: LoginRequest,
    user_repo: Injected[UserRepository],
    auth: Injected[AuthService],
):

    user = await user_repo.find_by_email(request.email)
    if not user:
        raise HTTPException(
            status_code=401, detail="Invalid email or password")

    token = auth.create_access_token(user)
    return {"token": token, "token_type": "bearer"}


class MeDto(BaseModel):
    id: int
    email: str


@router.get("/me")
async def get_me(
    user_repo: Injected[UserRepository],
    auth: Injected[AuthService],
    token: str = Depends(oauth2_scheme)
) -> MeDto:
    jwt = auth.decode_access_token(token)
    user = await user_repo.get_by_id(jwt.sub)
    return MeDto(
        id=user.id,
        email=user.email,
    )
