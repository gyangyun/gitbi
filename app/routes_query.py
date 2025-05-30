"""
Routes for displaying and saving queries
"""
from starlette.exceptions import HTTPException
from starlette.responses import PlainTextResponse
import repo
import utils


async def delete_route(request):
    """
    Delete query from repository
    """
    try:
        user = utils.common_context_args(request).get("user")
        repo.delete_query(user=user, **request.path_params)
        redirect_url = request.app.url_path_for("home_route", state="HEAD")
        headers = {"HX-Redirect": redirect_url}
        response = PlainTextResponse(content="OK",
                                     headers=headers,
                                     status_code=200)
    except Exception as e:
        status_code = 404 if isinstance(e, RuntimeError) else 500
        raise HTTPException(status_code=status_code, detail=str(e))
    else:
        return response


async def save_route(request):
    """
    Save query to repository
    """
    try:
        form = await request.form()
        data = utils.parse_query_data(request, form)
        repo.save_query(
            user=utils.common_context_args(request).get("user"),
            db=request.path_params["db"],
            file=data["file"],
            query=data["query"],
            viz=data["viz"],
            template=data["template"],
        )
        response = PlainTextResponse(
            content='<div class="success-message">查询已保存成功！</div>',
            status_code=200)
    except Exception as e:
        status_code = 404 if isinstance(e, RuntimeError) else 500
        raise HTTPException(status_code=status_code, detail=str(e))
    else:
        return response


async def query_route(request):
    """
    Endpoint for empty query
    """
    try:
        db = request.path_params.get("db")
        if db not in repo.list_sources("file").keys():
            raise RuntimeError(f"db {db} not present in repo")
        request.state.query_data = {
            "query": request.query_params.get('query') or "",
            "viz": "null",
            "file": "__empty__",
            **request.path_params,  # db
        }
    except RuntimeError as e:
        raise HTTPException(status_code=404, detail=str(e))
    else:
        return await _query(request)


async def saved_query_route(request):
    """
    Endpoint for saved query
    """
    try:
        query_str, _lang = repo.get_query(**request.path_params)
        viz_str = repo.get_query_viz(**request.path_params)
        template_str = repo.get_query_template(**request.path_params)
        print('---------------读取文件-----------------')
        print('query_str', query_str)
        print('viz_str', viz_str)
        print('template_str', template_str)
        print('---------------------------------------')
        request.state.query_data = {
            "query": query_str,
            "viz": viz_str,
            "template": template_str,
            **request.path_params,  # db, file, state
        }
    except RuntimeError as e:
        raise HTTPException(status_code=404, detail=str(e))
    else:
        return await _query(request)


async def _query(request):
    """
    Common logic for query endpoint
    Called by:
    - query
    - saved query
    """
    data = {
        **utils.common_context_args(request),
        **request.state.query_data,
        "echart_id": f"echart-{utils.random_id()}",
    }
    return utils.TEMPLATES.TemplateResponse(name='query.html', context=data)
