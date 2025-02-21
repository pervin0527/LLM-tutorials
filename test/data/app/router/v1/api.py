from fastapi import APIRouter
from app.router.v1.endpoint import crawler_worker, db_worker, vector_db_worker, backoffice_worker

culture_api_router_v1 = APIRouter()

culture_api_router_v1.include_router(crawler_worker.router, tags=['crawler_worker'])    
culture_api_router_v1.include_router(db_worker.router, tags=['db_worker'])    
culture_api_router_v1.include_router(vector_db_worker.router, tags=['vector_db_worker'])    
culture_api_router_v1.include_router(backoffice_worker.router, tags=['backoffice_worker'])    