"""
Functions to interact with config repository
"""
from collections import OrderedDict
from datetime import datetime
import json
import logging
from markdown import markdown
import os
from pathlib import Path
from pygit2 import Repository, Signature
import utils
from config import config
import glob

# 从配置文件获取仓库目录
DIR = config.get_repo_dir()
REPO = Repository(DIR)
VALID_DB_TYPES = (
    "sqlite",
    "postgres",
    "clickhouse",
    "duckdb",
)
VALID_QUERY_EXTENSIONS = (
    ".sql",
    ".prql",
)
VALID_DASHBOARD_EXTENSIONS = (".json", )
DASHBOARDS_DIR = "_dashboards"
DASHBOARDS_FULL_PATH = os.path.join(DIR, DASHBOARDS_DIR)
if not os.path.exists(DASHBOARDS_FULL_PATH):
    os.makedirs(DASHBOARDS_FULL_PATH)
# 添加Document常量
DOCUMENTS_DIR = "_documents"
DOCUMENTS_FULL_PATH = os.path.join(DIR, DOCUMENTS_DIR)
if not os.path.exists(DOCUMENTS_FULL_PATH):
    os.makedirs(DOCUMENTS_FULL_PATH)
QUERIES_EXCLUDE = (
    ".git",
    DASHBOARDS_DIR,
    DOCUMENTS_DIR,
)
SCHEDULE_KEYS = (
    "cron",
    "db",
    "file",
    "type",
    "format",
    "to",
)


def get_db_params(db):
    """
    Reads database configuration from config file
    """
    try:
        db_type, conn_str = config.get_db_config(db)
        if db_type not in VALID_DB_TYPES:
            raise ValueError(f"DB type {db_type} not supported")
        return db_type, conn_str
    except Exception as e:
        raise ValueError(f"Failed to get database config for {db}: {str(e)}")


def get_email_params():
    """
    Reads email configuration from config file
    """
    email_config = config.get_email_config()
    if not email_config:
        return None, None, None, None
    return (email_config.get('smtp_user'), email_config.get('smtp_pass'),
            email_config.get('smtp_url'), email_config.get('smtp_email'))


def get_auth():
    """
    Get authentication configuration from config file
    """
    users = config.get_auth_config()
    if not users:
        return tuple()
    return tuple(users)


def get_query(state, db, file):
    """
    Gets query content from the repo
    """
    assert Path(file).suffix in VALID_QUERY_EXTENSIONS, "Bad query extension"
    lang = utils.get_lang(file)
    query_path = os.path.join(db, file)
    query_str = _get_file_content(state, query_path)
    return query_str, lang


def get_query_viz(state, db, file):
    """
    Gets saved viz for given query
    """
    try:
        viz_path = os.path.join(db, f"{file}.json")
        viz_str = _get_file_content(state, viz_path)
    except:
        viz_str = "null"  # this is read by JS
    return viz_str


def get_query_template(state, db, file):
    """
    Gets saved template for given query
    """
    try:
        template_path = os.path.join(db, f"{file}.txt")
        template_str = _get_file_content(state, template_path)
    except:
        template_str = ""  # 如果没有模板文件则返回空字符串
    return template_str


def get_dashboard(state, file):
    """
    Get dashboard content from repo
    """
    assert Path(
        file).suffix in VALID_DASHBOARD_EXTENSIONS, "Bad dashboard extension"
    path = os.path.join(DASHBOARDS_DIR, file)
    raw_dashboard = _get_file_content(state, path)
    return json.loads(raw_dashboard)


def get_readme(state):
    """
    Gets readme content from the repo
    """
    try:
        readme = _get_file_content(state, "README.md")
        readme = markdown(readme)
    except Exception as e:
        # It is OK for README to be missing, fallback present in template
        logging.warning(f"Readme not specified: {str(e)}")
        readme = None
    return readme


def list_sources(state):
    """
    Lists all available sources (db + queries)
    """
    try:
        match state:
            case 'file':
                db_dirs = {
                    db_dir
                    for db_dir in os.scandir(DIR)
                    if db_dir.is_dir() and db_dir.name not in QUERIES_EXCLUDE
                }
                sources = {
                    db_dir.name: _list_file_names(db_dir)
                    for db_dir in db_dirs
                }
            case hash:
                commit = REPO.revparse_single(hash)
                sources = dict()
                for path in (
                        Path(el)
                        for el in _get_tree_objects_generator(commit.tree)):
                    if len(
                            path.parts
                    ) == 2:  #files in 1st-level folder, all other ignored
                        db = str(path.parent)
                        query = str(path.name)
                        if db not in QUERIES_EXCLUDE:
                            try:
                                sources[db].add(query)
                            except:
                                sources[db] = set((query, ))
        sources = OrderedDict(
            (db, _filter_extension(queries, VALID_QUERY_EXTENSIONS))
            for db, queries in sorted(sources.items()))
    except Exception as e:
        raise RuntimeError(
            f"Sources at state {state} cannot be listed: {str(e)}")
    else:
        return sources


def list_dashboards(state):
    """
    List dasboards in repo
    """
    try:
        match state:
            case 'file':
                dashboards = _list_file_names(DASHBOARDS_FULL_PATH)
            case hash:
                commit = REPO.revparse_single(hash)
                repo_paths = (
                    Path(el)
                    for el in _get_tree_objects_generator(commit.tree))
                dashboards = tuple(path.name for path in repo_paths
                                   if (len(path.parts) == 2
                                       and str(path.parent) == DASHBOARDS_DIR))
        dashboards = _filter_extension(dashboards, VALID_DASHBOARD_EXTENSIONS)
    except Exception as e:
        raise RuntimeError(
            f"Dashboards at state {state} cannot be listed: {str(e)}")
    else:
        return dashboards


def list_commits():
    """
    Function lists all commits present in current branch of the repo
    """
    headers = ("commit_hash", "author", "date", "message")
    commits = [
        (
            "file",
            "N/A",
            "now",
            "N/A",
        ),
    ]
    for entry in REPO.walk(REPO.head.target):
        commit = _format_commit(entry)
        commits.append(commit)
    return headers, commits


def _format_commit(entry):
    """
    Format commit tuple
    """
    commit = (
        str(entry.id),
        str(entry.author),
        datetime.fromtimestamp(
            entry.commit_time).astimezone().strftime("%Y-%m-%d %H:%M:%S %Z"),
        entry.message.replace("\n", ""),
    )
    return commit


def save_dashboard(user, file, queries):
    """
    Save dashboard config into repo
    """
    path_obj = Path(file)
    assert file == path_obj.name, "Path passed"
    assert (path_obj.suffix in VALID_DASHBOARD_EXTENSIONS
            ), f"Extension not in {str(VALID_DASHBOARD_EXTENSIONS)}"
    path = f"{DASHBOARDS_DIR}/{file}"
    assert _write_file_content(path, queries), "Writing query content failed"
    _commit(user, "save", (path, ))
    return True


def delete_dashboard(user, file):
    """
    Delete dashboard config
    """
    path = f"{DASHBOARDS_DIR}/{file}"
    assert _remove_file(path), f"Cannot remove {path}"
    _commit(user, "delete", (path, ))
    return True


def save_query(user, db, file, query, viz, template):
    """
    Save query into repo
    file refers to query file name
    """
    path_obj = Path(file)
    assert file == path_obj.name, "Path passed"
    assert (path_obj.suffix in VALID_QUERY_EXTENSIONS
            ), f"Extension not in {str(VALID_QUERY_EXTENSIONS)}"

    query_path = f"{db}/{file}"
    viz_path = f"{query_path}.json"
    template_path = f"{query_path}.txt"

    to_commit = [
        query_path,
        viz_path,
    ]

    assert _write_file_content(query_path,
                               query), "Writing query content failed"
    assert _write_file_content(viz_path, viz), "Writing viz content failed"

    # 只有在有模板内容时才保存模板文件
    if template.strip():
        assert _write_file_content(template_path,
                                   template), "Writing template content failed"
        to_commit.append(template_path)
    else:
        # 如果模板为空且文件存在，则删除文件
        try:
            _remove_file(template_path)
            to_commit.append(template_path)  # 添加到提交列表以记录删除操作
        except:
            pass  # 如果文件不存在则忽略

    _commit(user, "save", to_commit)
    print('--------------保存文件----------------')
    print('query:', query)
    print('viz:', viz)
    print('template:', template)
    print('to_commit:', to_commit)
    print('-------------------------------------')
    return True


def delete_query(user, db, file):
    """
    Delete query from the repo
    """
    query_path = f"{db}/{file}"
    viz_path = f"{query_path}.json"
    template_path = f"{query_path}.txt"
    to_commit = [
        query_path,
    ]
    assert _remove_file(query_path), f"Cannot remove {query_path}"
    try:
        _remove_file(viz_path)
    except:
        pass
    else:
        to_commit.append(viz_path)

    # 尝试删除模板文件
    try:
        _remove_file(template_path)
    except:
        pass
    else:
        to_commit.append(template_path)

    #TODO: if fails error not caught, not recoverable in Gitbi, one needs to checkout manually
    _commit(user, "delete", to_commit)
    return True


def _list_file_names(dir):
    """
    List file names in given directory
    """
    return tuple(el.name for el in os.scandir(dir) if el.is_file())


def _filter_extension(files, valid_ext):
    """
    Filter file list based on extension
    """
    return tuple(sorted(f for f in files if Path(f).suffix in valid_ext))


def _write_file_content(path, content):
    """
    Change file contents on disk
    """
    full_path = os.path.join(DIR, path)
    with open(full_path, "w") as f:
        f.write(content)
    return True


def _remove_file(path):
    """
    Remove file from disk
    """
    full_path = os.path.join(DIR, path)
    assert os.path.exists(full_path), f"no file {path}"
    os.remove(full_path)
    return True


def _get_file_content(state, path):
    """
    Read file content from git or filesystem
    """
    try:
        match state:
            case 'file':
                # 检查是否是文档路径
                if not path.startswith(DOCUMENTS_DIR):
                    full_path = os.path.join(DIR, path)
                else:
                    # 对于文档，直接使用完整路径
                    full_path = os.path.join(DIR, path)

                with open(full_path, "r", encoding="utf-8") as f:
                    content = f.read()
            case hash:
                commit = REPO.revparse_single(hash)
                blob = commit.tree / path
                content = blob.data.decode("UTF-8")
    except Exception as e:
        # Common error for atual no file, permission, repo error etc.
        raise RuntimeError(
            f"File {path} at state {state} cannot be accessed: {str(e)}")
    else:
        return content


def _get_tree_objects_generator(tree, prefix=""):
    """
    List files from given state of the repo
    """
    for obj in tree:
        if obj.type_str == "blob":
            yield os.path.join(prefix, obj.name)
        elif obj.type_str == "tree":
            new_prefix = os.path.join(prefix, obj.name)
            for entry in _get_tree_objects_generator(obj, new_prefix):
                yield entry


def _commit(user, operation, files):
    """
    Commit given file to repo
    """
    assert files, "empty list passed"
    files_msg = ", ".join(files)
    index = REPO.index
    for file in files:
        match operation:
            case "save":
                index.add(file)
            case "delete":
                index.remove(file)
            case operation:
                raise ValueError(f"Bad operation: {operation}")
    index.write()
    author = Signature(name=(user or "Gitbi (no auth)"),
                       email="gitbi@gitbi.gitbi")
    REPO.create_commit(
        REPO.head.name,  # reference_name
        author,  # author
        author,  # committer
        f"[gitbi] {operation} {files_msg}",  # message
        index.write_tree(),  # tree
        [
            REPO.head.target,
        ]  # parents
    )
    return True


# 添加文档模板相关函数
def _get_files_dir(state=None):
    """
    根据state获取文件目录
    """
    if state is None or state == 'file':
        # 本地文件模式
        return DOCUMENTS_FULL_PATH
    else:
        # Git模式
        try:
            commit = REPO.revparse_single(state)
            return os.path.join(GIT_DIR, DOCUMENTS_DIR)
        except Exception as e:
            print_error(f"无法获取文件目录: {e}")
            return DOCUMENTS_FULL_PATH


def list_documents(state=None):
    """
    List all documents in repo
    """
    try:
        if state is None or state == 'file':
            # 本地文件模式
            if not os.path.exists(DOCUMENTS_FULL_PATH):
                os.makedirs(DOCUMENTS_FULL_PATH)
            documents_pattern = os.path.join(DOCUMENTS_FULL_PATH, "*")
            docs = sorted(glob.glob(documents_pattern))
            # 筛选出所有文档类型文件: .txt, .md, .docx
            docs = [
                os.path.basename(f) for f in docs
                if os.path.isfile(f) and (f.endswith('.txt') or f.endswith(
                    '.md') or f.endswith('.docx'))
            ]
            return docs
        else:
            # 从Git仓库中读取
            try:
                commit = REPO.revparse_single(state)
                documents = []
                for path in (
                        Path(el)
                        for el in _get_tree_objects_generator(commit.tree)):
                    if len(path.parts) == 2 and str(
                            path.parent) == DOCUMENTS_DIR and (
                                path.name.endswith('.txt')
                                or path.name.endswith('.md')
                                or path.name.endswith('.docx')):
                        documents.append(path.name)
                return sorted(documents)
            except Exception as e:
                print_error(f"从Git获取文档失败: {e}")
                return []
    except Exception as e:
        print_error(f"Could not list documents: {e}")
        return []


def save_document(user, file_name, file_content):
    """
    保存文档到仓库
    user: 用户名
    file_name: 文件名（可以是.txt、.md或.docx）
    file_content: 文件内容（二进制）
    """
    # 检查文件名是否有扩展名，如果没有则添加默认扩展名.txt
    if not (file_name.endswith('.txt') or file_name.endswith('.md')
            or file_name.endswith('.docx')):
        file_name = f"{file_name}.txt"

    document_path = f"{DOCUMENTS_DIR}/{file_name}"

    # 确保_documents目录存在
    os.makedirs(DOCUMENTS_FULL_PATH, exist_ok=True)

    # 写入文件
    with open(os.path.join(DIR, document_path), 'wb') as f:
        f.write(file_content)

    # 提交到Git
    _commit(user, "save", [document_path])
    return True


def delete_document(user, file_name):
    """
    删除文档模板
    user: 用户名
    file_name: 文件名
    """
    # 确保文件名格式正确
    if not file_name.endswith('.docx'):
        file_name = f"{file_name}.docx"

    document_path = f"{DOCUMENTS_DIR}/{file_name}"

    # 删除文件
    try:
        assert _remove_file(document_path), f"Cannot remove {document_path}"
    except:
        return False

    # 提交到Git
    _commit(user, "delete", [document_path])
    return True


def get_document_path(file_name):
    """
    获取文档模板的完整路径
    """
    try:
        # 构建文档路径
        document_path = os.path.join(DOCUMENTS_DIR, file_name)
        full_path = os.path.join(DIR, document_path)

        # 尝试直接查找
        if os.path.exists(full_path):
            return document_path

        # 如果没找到，尝试列出所有文件，进行不区分大小写的比较
        try:
            import urllib.parse
            decoded_name = urllib.parse.unquote(file_name)

            # 如果解码后的文件名不同，尝试使用解码后的名称
            if decoded_name != file_name:
                alt_path = os.path.join(DOCUMENTS_DIR, decoded_name)
                full_alt_path = os.path.join(DIR, alt_path)
                if os.path.exists(full_alt_path):
                    return alt_path

            # 尝试不区分大小写匹配
            all_files = os.listdir(os.path.join(DIR, DOCUMENTS_DIR))
            lower_name = file_name.lower()
            for f in all_files:
                if f.lower() == lower_name:
                    return os.path.join(DOCUMENTS_DIR, f)
        except Exception as e:
            print(f"Error in alternative file lookup: {str(e)}")
            # 忽略备选查找中的错误

        # 没有找到匹配的文件
        return None
    except Exception as e:
        print(f"Error in get_document_path: {str(e)}")
        return None


def _read_env_var(key):
    """
    Read variable, also attempt to take from file
    """
    try:
        value = os.environ[key]
    except:
        try:
            file_key = f"{key}_FILE"
            value_file = os.environ[file_key]
            value = _get_file_content('file', value_file)
        except Exception as e:
            raise NameError(
                f"Neither {key} nor valid {file_key} was set: {str(e)}")
    return value
