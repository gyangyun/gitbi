"""
Routes for managing document templates
"""
from starlette.exceptions import HTTPException
from starlette.responses import PlainTextResponse, FileResponse
import repo
import utils
from starlette.datastructures import UploadFile


async def document_route(request):
    """
    Endpoint for viewing document template
    """
    try:
        file_name = request.path_params.get("file")
        state = request.path_params.get("state", "file")  # 默认为 "file" 状态

        # 从指定的 state 获取文档
        documents = repo.list_documents(state)
        if file_name not in documents:
            raise RuntimeError(
                f"Document {file_name} not found in state {state}")

        document_path = repo.get_document_path(file_name)
        if not document_path:
            raise RuntimeError(f"Document {file_name} not found")

        return FileResponse(
            path=document_path,
            filename=file_name,
            media_type=
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        )
    except Exception as e:
        status_code = 404 if isinstance(e, RuntimeError) else 500
        raise HTTPException(status_code=status_code, detail=str(e))


async def document_new_route(request):
    """
    Endpoint for new document template page
    """
    try:
        data = {
            **utils.common_context_args(request),
            "documents":
            repo.list_documents(),
        }
        response = utils.TEMPLATES.TemplateResponse(name='document.html',
                                                    context=data)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    else:
        return response


async def document_save_route(request):
    """
    Endpoint for saving document template
    """
    try:
        form = await request.form()
        file = form['file']
        file_name = form.get('file_name', '')

        if not file_name:
            # 如果没有提供文件名，使用上传文件的名称
            file_name = file.filename

        # 确保文件名以.docx结尾
        if not file_name.endswith('.docx'):
            file_name = f"{file_name}.docx"

        # 读取文件内容
        content = await file.read()

        # 保存文档
        user = utils.common_context_args(request).get("user")
        repo.save_document(user=user,
                           file_name=file_name,
                           file_content=content)

        # 返回成功信息
        response = PlainTextResponse(
            content=
            '<div class="success-message">Document has been uploaded successfully!</div>',
            status_code=200)
    except Exception as e:
        status_code = 500
        raise HTTPException(status_code=status_code, detail=str(e))
    else:
        return response


async def document_delete_route(request):
    """
    Endpoint for deleting document template
    """
    try:
        user = utils.common_context_args(request).get("user")
        file_name = request.path_params.get("file")

        # 删除文档
        repo.delete_document(user=user, file_name=file_name)

        # 返回成功信息
        response = PlainTextResponse(
            content=
            '<div class="success-message">Document has been deleted successfully!</div>',
            status_code=200)
    except Exception as e:
        status_code = 404 if isinstance(e, RuntimeError) else 500
        raise HTTPException(status_code=status_code, detail=str(e))
    else:
        return response
