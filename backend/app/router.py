from typing import Literal

from fastapi import APIRouter, Depends, File, Form, HTTPException, Request, Response, UploadFile
from fastapi import status as statusList
from pydantic import BaseModel, EmailStr, NonNegativeInt
from wireup import Injected

from app import face_service
from app.app_config import ACCESS_TOKEN_COOKIE_NAME
from app.auth_service import AuthService, TokenPayload, fastapi_require_access_token
from app.dashboard_service import DashboardService, DashStats
from app.face_model_invoker import NoFaceFound
from app.face_service import AnalyzeBox, FaceItem, FaceService, FaceSimilarItem
from app.user_repository import UserRepository

"""
todo: refresh tokens
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
    faces: list[FaceItemResponse]


def append_pagination_headers(response: Response, total_count: int) -> None:
    response.headers["X-Total-Count"] = str(total_count)
    response.headers["Access-Control-Expose-Headers"] = "X-Total-Count"


@router.get("/detail", response_model=DetailData)
async def detail_image(
    request: Request,
    id: int,
    face_service: Injected[face_service.FaceService],
    jwt: TokenPayload = Depends(fastapi_require_access_token),
) -> DetailData:
    data = await face_service.get_by_id(id)

    data_resp = FaceItemResponse(
        **data.model_dump(),
        preview_url=f"{str(request.base_url)}preview/{data.preview_path}",
        source_url=f"{str(request.base_url)}source_img/{data.source_filepath}",
    )

    faces_resp = [
        FaceItemResponse(
            **item.model_dump(),
            preview_url=f"{str(request.base_url)}preview/{item.preview_path}",
            source_url=f"{str(request.base_url)}source_img/{item.source_filepath}",
        )
        for item in await face_service.get_photo_faces_by_filename(data.fn)
        if item.model == data.model
    ]

    return DetailData(data=data_resp, faces=faces_resp)


@router.get("/list", response_model=list[FaceItemResponse])
async def read_random(
    request: Request,
    response: Response,
    face_service: Injected[FaceService],
    search: str = "",
    limit: int = 20,
    jwt: TokenPayload = Depends(fastapi_require_access_token),
) -> list[FaceItemResponse]:
    res = await face_service.find_list(limit, search)
    return [
        FaceItemResponse(
            **item.model_dump(),
            preview_url=f"{str(request.base_url)}preview/{item.preview_path}",
            source_url=f"{str(request.base_url)}source_img/{item.source_filepath}",
        )
        for item in res
    ]


class Pagination(BaseModel):
    total: NonNegativeInt
    pageCount: NonNegativeInt


class Meta(BaseModel):
    pagination: Pagination


class FaceItemResponseContainer(BaseModel):
    data: list[FaceItemResponse]
    meta: Meta


class ImageData(BaseModel):
    name: str


class UploadImageResponse(BaseModel):
    preview_url: str
    source_url: str
    boxes: list[AnalyzeBox]


@router.post("/analyze", response_model=UploadImageResponse)
async def analyze_image(
    request: Request,
    face_service: Injected[FaceService],
    file: UploadFile = File(...),
    jwt: TokenPayload = Depends(fastapi_require_access_token),
) -> UploadImageResponse:
    try:
        data = await face_service.analyze_image(file)

        return UploadImageResponse(
            boxes=data,
            preview_url=f"{str(request.base_url)}preview/",
            source_url=f"{str(request.base_url)}source_img/",
        )
    except NoFaceFound:
        # todo
        raise HTTPException(status_code=500, detail="No face detected in the image")


@router.get("/similar-to-id", response_model=list[FaceSimilarItemResponse])
async def find_similar_id(
    request: Request,
    face_service: Injected[FaceService],
    id: int,
    model: str,
    metric: str = "cosine",
    jwt: TokenPayload = Depends(fastapi_require_access_token),
) -> list[FaceSimilarItemResponse]:
    res = await face_service.find_similar_by_face_id(id=id, model=model, metric=metric, limit=50, quality=None)

    return [
        FaceSimilarItemResponse(
            **item.model_dump(),
            preview_url=f"{str(request.base_url)}preview/{item.preview_path}",
            source_url=f"{str(request.base_url)}source_img/{item.source_filepath}",
        )
        for item in res
    ]


@router.post("/similar-to-image", response_model=list[FaceSimilarItemResponse])
async def find_similar_image(
    request: Request,
    response: Response,
    image: UploadFile,
    face_service: Injected[FaceService],
    x: int = Form(...),
    y: int = Form(...),
    w: int = Form(...),
    h: int = Form(...),
    quality: int | None = Form(None),
    jwt: TokenPayload = Depends(fastapi_require_access_token),
) -> list[FaceSimilarItemResponse]:
    res = await face_service.find_similar_by_image(file=image, x=x, y=y, w=w, h=h, limit=100, offset=0, quality=quality)

    append_pagination_headers(response, len(res))

    return [
        FaceSimilarItemResponse(
            **item.model_dump(),
            preview_url=f"{str(request.base_url)}preview/{item.preview_path}",
            source_url=f"{str(request.base_url)}source_img/{item.source_filepath}",
        )
        for item in res
    ]


@router.get("/dashboard", response_model=DashStats)
async def dashboard(
    dashboard_service: Injected[DashboardService],
    jwt: TokenPayload = Depends(fastapi_require_access_token),
) -> DashStats:
    data = await dashboard_service.get_stats()
    return data


class UserItem(BaseModel):
    id: int
    email: EmailStr


@router.get("/users", response_model=list[UserItem])
async def user_list(
    request: Request,
    response: Response,
    user_repo: Injected[UserRepository],
    _start: int = 0,
    _end: int = 20,
    jwt: TokenPayload = Depends(fastapi_require_access_token),
) -> list[UserItem]:
    data = await user_repo.find_all(_start, _end)
    res = [UserItem(id=u.id, email=u.email) for u in data]
    append_pagination_headers(response, len(res))
    return res


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class LoginResponse(BaseModel):
    token: str
    token_type: Literal["bearer"]


@router.post("/login", response_model=LoginResponse)
async def login(
    response: Response,
    request: LoginRequest,
    user_repo: Injected[UserRepository],
) -> LoginResponse:
    user = await user_repo.find_by_email(request.email)
    if not user or not AuthService.verify_password(request.password, user.password):
        raise HTTPException(status_code=401, detail="Invalid email or password")

    token = AuthService.create_access_token(user)

    response.set_cookie(
        key=ACCESS_TOKEN_COOKIE_NAME, value=token, httponly=True, secure=True, samesite="none", max_age=3600
    )

    return LoginResponse(token=token, token_type="bearer")


@router.post("/logout", status_code=statusList.HTTP_204_NO_CONTENT, response_class=Response)
def logout(response: Response) -> Response:
    response.delete_cookie(key=ACCESS_TOKEN_COOKIE_NAME, httponly=True, secure=True, samesite="none")
    return Response(status_code=statusList.HTTP_204_NO_CONTENT)


class MeDto(BaseModel):
    id: int
    email: EmailStr


@router.get("/me", response_model=MeDto)
async def get_me(
    user_repo: Injected[UserRepository],
    jwt: TokenPayload = Depends(fastapi_require_access_token),
) -> MeDto:
    user = await user_repo.get_by_id(jwt.sub)
    return MeDto(
        id=user.id,
        email=user.email,
    )
