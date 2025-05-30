"""
Main app file
"""
from starlette.applications import Starlette
from starlette.exceptions import HTTPException
from starlette.routing import Mount, Route
from starlette.staticfiles import StaticFiles
import auth
import routes_dashboard, routes_execute, routes_listing, routes_query, routes_document
import utils


# Error types
# 404 RuntimeError file not accessible
# 500 NameError variables not set
# 500 ValueError bad query
async def server_error(request, exc):
    data = {
        "request": request,
        "path": dict(request).get("path"),
        "code": exc.status_code,
        "message": exc.detail
    }
    return utils.TEMPLATES.TemplateResponse(name='partial_error.html',
                                            context=data,
                                            status_code=exc.status_code)


routes = [
    # routes execute
    Route('/execute/{db:str}',
          endpoint=routes_execute.execute_route,
          methods=("POST", ),
          name="execute_route"),
    Route('/report/{db:str}/{file:str}/{state:str}/{format:str}',
          endpoint=routes_execute.report_route,
          name="report_route"),
    # routes_listing
    Route("/",
          endpoint=routes_listing.home_default_route,
          name="home_default_route"),
    Route("/home/{state:str}",
          endpoint=routes_listing.home_route,
          name="home_route"),
    Route("/resources/{state:str}",
          endpoint=routes_listing.resources_route,
          name="resources_route"),
    Route("/dbdetails/{db:str}",
          endpoint=routes_listing.db_details_route,
          name="db_details_route"),
    # routes query
    Route('/query/delete/{db:str}/{file:str}',
          endpoint=routes_query.delete_route,
          name="query_delete_route"),
    Route('/query/save/{db:str}',
          endpoint=routes_query.save_route,
          methods=("POST", ),
          name="query_save_route"),
    Route('/query/{db:str}',
          endpoint=routes_query.query_route,
          name="query_route"),
    Route('/query/{db:str}/{file:str}/{state:str}',
          endpoint=routes_query.saved_query_route,
          name="saved_query_route"),
    # routes dashboard
    Route('/dashboard/delete/{file:str}',
          endpoint=routes_dashboard.delete_route,
          name="dashboard_delete_route"),
    Route('/dashboard/save',
          endpoint=routes_dashboard.save_route,
          methods=("POST", ),
          name="dashboard_save_route"),
    Route('/dashboard/{file:str}/{state:str}',
          endpoint=routes_dashboard.dashboard_route,
          name="dashboard_route"),
    Route('/dashboard/new',
          endpoint=routes_dashboard.new_route,
          name="dashboard_new_route"),
    # routes document
    Route('/document/save',
          endpoint=routes_document.document_save_route,
          methods=("POST", ),
          name="document_save_route"),
    Route('/document/delete/{file:str}',
          endpoint=routes_document.document_delete_route,
          methods=("POST", ),
          name="document_delete_route"),
    Route('/document/new',
          endpoint=routes_document.document_new_route,
          name="document_new_route"),
    Route('/document/{file:str}/{state:str}',
          endpoint=routes_document.document_route,
          name="document_route"),
    Route('/document/view/{file:str}/{state:str}',
          endpoint=routes_document.document_view_route,
          name="document_view_route"),
    Route('/document/download/{file:str}/{state:str}',
          endpoint=routes_document.document_download_route,
          name="document_download_route"),
    # static
    Mount('/static',
          app=StaticFiles(directory=utils.STATIC_DIR),
          name="static"),
]

exception_handlers = {
    HTTPException: server_error,
}

middleware = []
if auth.AUTH is not None:
    middleware.append(auth.AUTH)

app = Starlette(debug=True,
                routes=routes,
                exception_handlers=exception_handlers,
                middleware=middleware)
