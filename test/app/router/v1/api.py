from fastapi import APIRouter
from app.router.v1.endpoint import crawler, db, vector_db, backoffice

culture_api_router_v1 = APIRouter()
culture_api_router_v1.include_router(crawler.router, tags=['crawler'])
culture_api_router_v1.include_router(db.router, tags=['db'])
culture_api_router_v1.include_router(vector_db.router, tags=['vector_db'])

culture_api_router_v1.include_router(backoffice.router, tags=['backoffice'])