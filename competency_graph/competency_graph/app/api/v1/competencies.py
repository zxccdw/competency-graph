from typing import List
from fastapi import APIRouter, HTTPException, Query, Body

from models.graph import GraphResponse, RDFNode, OntologyNode

from dao.competency_dao import CompetencyDAO



router = APIRouter()


#тест 
@router.post("/competencies/test")
async def test_endpoint(data: dict = Body(...)):
    print(">>> ЗАШЛО В ЭНДПОИНТ test_endpoint")
    return {"echo": data}


# Получить граф из БД
@router.get("/competencies/graph", response_model=GraphResponse)
async def get_graph() -> dict:
    print("Зашли в get_graph")
    try:
        return await CompetencyDAO.get_graph_from_db()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Сохранить граф в БД 1 версия
@router.post("/competencies/graph")
async def save_graph(graph_data: dict = Body(...)) -> dict:
    print("Зашли в save_graph")
    try:
        await CompetencyDAO.save_graph_to_db(graph_data)
        return {"status": "success"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))



@router.get("/competencies/graph/{node_id}", response_model=GraphResponse)
async def get_graph_part(
    node_id: str,
    depth: int = Query(2, ge=1, le=5),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
) -> dict:
    """
    Получает часть графа в формате:
    {
        "nodes": [{"id": "...", "label": "...", "type": "..."}],
        "links": [{"source": "...", "target": "...", "predicate": "..."}]
    }
    """
    try:
        return await CompetencyDAO.get_graph_part(
            start_from=node_id,
            depth=depth,
            limit=limit,
            offset=offset
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))



@router.post("/competencies/graph/from_json")
async def get_graph_from_json(
    graph_data: dict = Body(...),
    start_from: str = Query(...),
    depth: int = Query(2)
):
    return await CompetencyDAO.get_graph_part_from_json(
        graph_data=graph_data,
        start_from=start_from,
        depth=depth
    )


@router.get("/competencies/{node_id}/ancestors", response_model=List[OntologyNode])
async def get_ancestors(
    node_id: str,
    limit: int = Query(50, ge=1, le=100, description="Количество узлов на странице"),
    offset: int = Query(0, ge=0, description="Смещение для пагинации"),
) -> List[OntologyNode]:
    """
    Получить всех предков компетенции.
    Поддерживает пагинацию результатов.
    """
    try:
        return await CompetencyDAO.get_ancestors(
            competency_id=node_id,
            limit=limit,
            offset=offset
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/competencies/{node_id}/descendants", response_model=List[OntologyNode])
async def get_descendants(
    node_id: str,
    limit: int = Query(50, ge=1, le=100, description="Количество узлов на странице"),
    offset: int = Query(0, ge=0, description="Смещение для пагинации"),
) -> List[OntologyNode]:
    """
    Получить всех потомков компетенции.
    Поддерживает пагинацию результатов.
    """
    try:
        return await CompetencyDAO.get_descendants(
            competency_id=node_id,
            limit=limit,
            offset=offset
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/competencies/{node_id}/version")
async def check_node_version(
    node_id: str,
) -> dict:
    """
    Проверка версии узла перед изменением.
    Временная заглушка, всегда возвращает успешный ответ.
    """
    return {"status": "ok"}


@router.get("/competencies/path", response_model=List[OntologyNode])
async def find_path(
    start_id: str = Query(..., description="ID начальной компетенции"),
    end_id: str = Query(..., description="ID конечной компетенции"),
) -> List[OntologyNode]:
    """Найти путь между двумя компетенциями в графе"""
    try:
        return await CompetencyDAO.find_path(
            start_id=start_id,
            end_id=end_id
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
