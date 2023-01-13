"""
Functions to interact with config repository
"""
import os
import re
from pathlib import Path
from pygit2 import Repository

DIR = os.environ["GITBI_REPO_DIR"]
REPO = Repository(DIR)

def get_query(state, db, query):
    """
    Gets query content from the repo
    """
    try:
        query_path = os.path.join(db, query)
        query = _get_file_content(state, query_path)
    except:
        raise FileNotFoundError("Query not found")
    return query

def get_readme(state):
    """
    Gets readme content from the repo
    """
    return _get_file_content(state, "README.md")

def list_sources(state):
    """
    Lists all available sources (db + queries)
    """
    # TODO no ifloop solution, tuples not list ?
    match state:
        case 'file':
            db_dirs = {db_dir for db_dir in os.scandir(DIR) if db_dir.is_dir() and db_dir.name != ".git"}
            sources = {db_dir.name: set(el.name for el in os.scandir(db_dir) if el.is_file()) for db_dir in db_dirs}
        case hash:
            commit = REPO.revparse_single(hash)
            sources = dict()
            for path in (Path(el) for el in _get_tree_objects_generator(commit.tree)):
                if len(path.parts) == 2:
                    db = str(path.parent)
                    query = str(path.name)
                    try:
                        sources[db].add(query)
                    except:
                        sources[db] = set((query, ))
    return sources

def _get_file_content(state, path):
    """
    Read file content from git or filesystem
    """
    match state:
        case 'file':
            with open(os.path.join(DIR, path), "r") as f:
                content = f.read()
        case hash:
            commit = REPO.revparse_single(hash)
            blob = commit.tree / path
            content = blob.data.decode("UTF-8")
    assert re.sub(r"\s", "", content), "File is empty"
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

# TODO list all commits
# commits = tuple(commit for commit in REPO.walk(REPO.head.target))
