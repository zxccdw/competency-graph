from typing import List, Optional
from fastapi import APIRouter, HTTPException, Depends, Query
from dependency_injector.wiring import inject, Provider

from app.models.graph import CompetencyNode, GraphPart
from app.models.user import User
from app.dao.competency_dao import CompetencyDAO
from app.dependencies.request_context import RequestContext

router = APIRouter()


async def _get_user_context(
    request_context: RequestContext = Depends(Provider["request_context"])
) -> User:
    """Получить контекст текущего пользователя"""
    try:
        return request_context.current_user
    except AssertionError:
        raise HTTPException(status_code=401, detail="User not authenticated")


@router.get("/competencies/graph/{node_id}", response_model=GraphPart)
@inject
async def get_graph_part(
    node_id: str,
    depth: int = Query(2, ge=1, le=5, description="Глубина обхода графа"),
    limit: int = Query(50, ge=1, le=100, description="Количество узлов на странице"),
    offset: int = Query(0, ge=0, description="Смещение для пагинации"),
    user: User = Depends(_get_user_context),
    competency_dao: Provider[CompetencyDAO] = Depends()
) -> GraphPart:
    """
    Получить часть графа компетенций, начиная с указанного узла.
    Поддерживает пагинацию и ограничение глубины обхода.
    """
    try:
        return await competency_dao().get_graph_part(
            start_from=node_id,
            depth=depth,
            limit=limit,
            offset=offset
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/competencies/{node_id}/ancestors", response_model=List[CompetencyNode])
@inject
async def get_ancestors(
    node_id: str,
    limit: int = Query(50, ge=1, le=100, description="Количество узлов на странице"),
    offset: int = Query(0, ge=0, description="Смещение для пагинации"),
    user: User = Depends(_get_user_context),
    competency_dao: Provider[CompetencyDAO] = Depends()
) -> List[CompetencyNode]:
    """
    Получить всех предков компетенции.
    Поддерживает пагинацию результатов.
    """
    try:
        return await competency_dao().get_ancestors(
            competency_id=node_id,
            limit=limit,
            offset=offset
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/competencies/{node_id}/descendants", response_model=List[CompetencyNode])
@inject
async def get_descendants(
    node_id: str,
    limit: int = Query(50, ge=1, le=100, description="Количество узлов на странице"),
    offset: int = Query(0, ge=0, description="Смещение для пагинации"),
    user: User = Depends(_get_user_context),
    competency_dao: Provider[CompetencyDAO] = Depends()
) -> List[CompetencyNode]:
    """
    Получить всех потомков компетенции.
    Поддерживает пагинацию результатов.
    """
    try:
        return await competency_dao().get_descendants(
            competency_id=node_id,
            limit=limit,
            offset=offset
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/competencies/path", response_model=List[CompetencyNode])
@inject
async def find_path(
    start_id: str = Query(..., description="ID начальной компетенции"),
    end_id: str = Query(..., description="ID конечной компетенции"),
    user: User = Depends(_get_user_context),
    competency_dao: Provider[CompetencyDAO] = Depends()
) -> List[CompetencyNode]:
    """Найти путь между двумя компетенциями в графе"""
    try:
        return await competency_dao().find_path(
            start_id=start_id,
            end_id=end_id
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
