import pytest
from contextlib import nullcontext as does_not_raise
from app.query import *

def test_execute():
    with pytest.raises(NameError):
        execute("baddb", "badquery", None)
    with pytest.raises(ValueError):
        execute("sqlite", "select badfunc();", None)
    with pytest.raises(Exception):
        execute("sqlite", "select badfunc();", "") # bad vega
    with pytest.raises(Exception):
        execute("sqlite", "select badfunc();", ";alert") # bad vega
    with does_not_raise():
        execute("sqlite", "select 1;", None)

def test_list_tables():
    assert list_tables("sqlite") == ["mytable", ]
    with pytest.raises(NameError):
        list_tables("baddb")
    with pytest.raises(NameError):
        list_tables("postgres")
