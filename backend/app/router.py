from wireup import Injected
from typing import Any, List
from fastapi import APIRouter, File, Form, HTTPException, Response, UploadFile
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from app import face_repository, face_service
from app.dashboard_service import DashboardService, DashStats
from app.face_service import AnalyzeBox, FaceItem, FaceSimilarItem, NoFaceFound
from fastapi import Request
from app.face_service import FaceService
from app.face_repository import FaceRepository

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
async def detail_image(request: Request,
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
async def read_random(request: Request,
                      response: Response,
                      face_service: Injected[FaceService],
                      search: str = '',
                      limit: int = 20,) -> List[FaceItemResponse]:
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
async def find_similar_id(request: Request,
                          face_service: Injected[FaceService],
                          id: int,
                          model: str,
                          metric: str = 'cosine',) -> List[FaceSimilarItemResponse]:
    res = await face_service.find_similar_by_face_id(id=id, model=model, metric=metric, limit=50)

    return [
        FaceSimilarItemResponse(
            **item.model_dump(),
            preview_url=f"{str(request.base_url)}preview/{item.preview_path}",
            source_url=f"{str(request.base_url)}source_img/{item.source_filepath}")
        for item in res
    ]


@router.post("/similar-to-image")
async def find_similar_image(request: Request,
                             image: UploadFile,
                             face_service: Injected[FaceService],
                             x: int = Form(...),
                             y: int = Form(...),
                             w: int = Form(...),
                             h: int = Form(...),) -> List[FaceSimilarItemResponse]:
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


@router.get("/di-test")
async def di_test(
    face_repository: Injected[FaceRepository],
    face_service: Injected[FaceService],
):
    return JSONResponse(content={
        "face_repository": id(face_repository),
        "face_service": id(face_service),
    })


@router.get("/list-test")
async def list_test(request: Request,
                    response: Response,
                    face_service: Injected[FaceService],
                    search: str = '',
                    _start: int = 0,
                    _end: int = 20) -> List[Any]:
    res = [
        {
            "model": f"Model {i}-{i*i}",
            "id": i
        }
        for i in range(100) if i >= _start and i <= _end
    ]
    total_count = len(res)
    response.headers["X-Total-Count"] = str(total_count)
    response.headers["Access-Control-Expose-Headers"] = "X-Total-Count"
    return res
