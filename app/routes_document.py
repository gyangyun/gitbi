"""
Routes for managing document templates
"""
from starlette.exceptions import HTTPException
from starlette.responses import PlainTextResponse, FileResponse, RedirectResponse
import repo
import utils
import mammoth
import os
import urllib.parse
from datetime import datetime
from starlette.datastructures import UploadFile
from docx import Document
from bs4 import BeautifulSoup
import re
import mimetypes


def get_document_type(filename):
    """
    获取文档类型
    """
    ext = os.path.splitext(filename)[1].lower()
    if ext == '.md':
        return "Markdown文档"
    elif ext == '.docx':
        return "Word文档 (.docx)"
    else:
        return "文本文档 (.txt)"


async def document_route(request):
    """
    Endpoint for document routing - for backward compatibility
    """
    download = request.query_params.get("download", "").lower() == "true"
    if download:
        return await document_download_route(request)
    else:
        return await document_view_route(request)


async def document_view_route(request):
    """
    Endpoint for viewing document in HTML format
    """
    try:
        file_name = request.path_params.get("file")
        state = request.path_params.get("state", "file")

        print(f"Document view request: file={file_name}, state={state}")

        # 获取文档
        documents = repo.list_documents(state)

        # 处理URL编码
        decoded_file_name = urllib.parse.unquote(file_name)
        if decoded_file_name != file_name and decoded_file_name in documents:
            file_name = decoded_file_name

        if file_name not in documents:
            raise RuntimeError(
                f"Document {file_name} not found in state {state}")

        document_path = repo.get_document_path(file_name)
        if not document_path:
            raise RuntimeError(f"Document {file_name} not found")

        # 获取文件修改时间
        last_modified = "Unknown"
        try:
            file_stats = os.stat(document_path)
            last_modified = datetime.fromtimestamp(
                file_stats.st_mtime).strftime('%Y-%m-%d %H:%M:%S')
        except Exception as e:
            print(f"Failed to get file stats: {e}")

        # 获取文档类型
        doc_type = get_document_type(file_name)
        html_content = ""

        # 根据文件类型处理内容
        try:
            if file_name.lower().endswith('.md'):
                # 对于Markdown文件，直接读取文本内容
                with open(document_path, "r", encoding="utf-8") as md_file:
                    html_content = md_file.read()
            elif file_name.lower().endswith('.docx'):
                # 对于DOCX文件，使用mammoth转换为HTML
                with open(document_path, "rb") as docx_file:
                    result = mammoth.convert_to_html(docx_file)
                    html_content = result.value
            else:
                # 对于TXT和其他文件，直接读取内容并添加简单的HTML格式
                with open(document_path, "r", encoding="utf-8") as txt_file:
                    content = txt_file.read()
                    html_content = f"<div>{content}</div>"

            print(f"Generated HTML content length: {len(html_content)}")
        except Exception as e:
            print(f"Error converting document to HTML: {e}")
            import traceback
            traceback.print_exc()
            raise HTTPException(
                status_code=500,
                detail=f"Failed to convert document to HTML: {str(e)}")

        # 构建下载URL
        download_url = f"/document/download/{urllib.parse.quote(file_name)}/{state}"

        # 获取文档名称（不含扩展名）
        document_name_without_ext = os.path.splitext(file_name)[0]

        # 渲染模板
        data = {
            **utils.common_context_args(request), "document_name":
            document_name_without_ext,
            "document_type": doc_type,
            "document_html": html_content,
            "last_modified": last_modified,
            "download_url": download_url
        }

        print("Rendering document_view.html template")
        response = utils.TEMPLATES.TemplateResponse(
            name='document_view.html',
            context=data,
            headers={
                "Content-Type": "text/html; charset=utf-8",
                "Content-Disposition": "inline"
            })
        return response

    except Exception as e:
        print(f"Document view error: {e}")
        import traceback
        traceback.print_exc()
        status_code = 404 if isinstance(e, RuntimeError) else 500
        raise HTTPException(status_code=status_code, detail=str(e))


async def document_save_route(request):
    """
    Endpoint for saving document template
    """
    try:
        form = await request.form()
        file_name = form.get('file_name', '')
        content = form.get('content', '')
        file = form.get('file')

        if not file_name:
            raise ValueError("文件名不能为空")

        user = utils.common_context_args(request).get("user")

        if file and isinstance(file, UploadFile):
            # 处理文件上传情况
            print(f"Saving uploaded document: {file_name}")

            # 确保文件有合适的扩展名
            if not (file_name.lower().endswith('.txt')
                    or file_name.lower().endswith('.md')
                    or file_name.lower().endswith('.docx')):
                # 从上传的文件名中获取扩展名
                original_ext = os.path.splitext(file.filename)[1].lower()
                if original_ext in ['.txt', '.md', '.docx']:
                    file_name += original_ext
                else:
                    file_name += '.txt'  # 默认为txt

            # 读取文件内容
            file_content = await file.read()

            # 保存文档
            repo.save_document(user=user,
                               file_name=file_name,
                               file_content=file_content)

            return PlainTextResponse(
                content='<div class="success-message">文档已上传成功！</div>',
                status_code=200)
        else:
            # 处理文本内容保存情况
            print(
                f"Saving document with content: {file_name}, content length: {len(content) if content else 0}"
            )

            # 确保文件名有正确的扩展名
            if selectedType := form.get('selected_type'):
                # 如果前端传递了选择的类型，使用该类型
                if not file_name.lower().endswith('.' + selectedType.lower()):
                    file_name += '.' + selectedType.lower()
            elif not (file_name.lower().endswith('.txt')
                      or file_name.lower().endswith('.md')
                      or file_name.lower().endswith('.docx')):
                # 如果没有扩展名，默认为.txt
                file_name += '.txt'

            # 转换为bytes
            content_bytes = content.encode('utf-8')
            repo.save_document(user=user,
                               file_name=file_name,
                               file_content=content_bytes)

            return PlainTextResponse(
                content='<div class="success-message">文档已保存成功！</div>',
                status_code=200)
    except Exception as e:
        print(f"Error saving document: {e}")
        import traceback
        traceback.print_exc()
        status_code = 500
        raise HTTPException(status_code=status_code, detail=str(e))


async def document_download_route(request):
    """
    Endpoint for downloading document file
    """
    try:
        file_name = request.path_params.get("file")
        state = request.path_params.get("state", "file")

        print(f"Document download request: file={file_name}, state={state}")

        # 获取文档
        documents = repo.list_documents(state)

        # 处理URL编码
        decoded_file_name = urllib.parse.unquote(file_name)
        if decoded_file_name != file_name and decoded_file_name in documents:
            file_name = decoded_file_name

        if file_name not in documents:
            raise RuntimeError(
                f"Document {file_name} not found in state {state}")

        document_path = repo.get_document_path(file_name)
        if not document_path:
            raise RuntimeError(f"Document {file_name} not found")

        # 确定适当的MIME类型
        content_type = mimetypes.guess_type(file_name)[0]
        if not content_type:
            if file_name.lower().endswith('.md'):
                content_type = 'text/markdown'
            elif file_name.lower().endswith('.docx'):
                content_type = 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
            else:
                content_type = 'text/plain'

        # 直接提供文件下载
        print(f"Downloading {file_name}")
        return FileResponse(path=document_path,
                            filename=file_name,
                            media_type=content_type)

    except Exception as e:
        print(f"Document download error: {e}")
        import traceback
        traceback.print_exc()
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
        return utils.TEMPLATES.TemplateResponse(name='document_new.html',
                                                context=data)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


async def document_delete_route(request):
    """
    Endpoint for deleting document template
    """
    try:
        user = utils.common_context_args(request).get("user")
        file_name = request.path_params.get("file")

        repo.delete_document(user=user, file_name=file_name)

        return PlainTextResponse(
            content='<div class="success-message">文档已删除成功！</div>',
            status_code=200)
    except Exception as e:
        status_code = 404 if isinstance(e, RuntimeError) else 500
        raise HTTPException(status_code=status_code, detail=str(e))
