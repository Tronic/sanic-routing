from unittest.mock import Mock

import pytest
from sanic_routing import BaseRouter
from sanic_routing.exceptions import NotFound


@pytest.fixture
def handler():
    def handler(**kwargs):
        return list(kwargs.values())[0]

    return handler


class Router(BaseRouter):
    def get(self, path, method, extra=None):
        return self.resolve(path=path, method=method, extra=extra)


def test_alpha_does_cast(handler):
    router = Router()

    router.add("/<alphaonly:alpha>", handler)
    router.finalize()

    _, handler, params = router.get("/foobar", "BASE")
    retval = handler(**params)

    assert isinstance(retval, str)
    assert retval == "foobar"


def test_alpha_does_not_cast(handler):
    router = Router()

    router.add("/<alphaonly:alpha>", handler)
    router.finalize()

    with pytest.raises(NotFound):
        router.get("/notfound123", "BASE")


def test_correct_alpha_v_string(handler):
    router = Router()

    router.add("/<alphaonly:alpha>", handler, methods=["alpha"])
    router.add("/<anystring:str>", handler, methods=["str"])
    router.finalize()

    _, handler, params = router.get("/foobar", "alpha")
    retval = handler(**params)

    assert isinstance(retval, str)
    assert retval == "foobar"

    _, handler, params = router.get("/foobar123", "str")
    retval = handler(**params)

    assert isinstance(retval, str)
    assert retval == "foobar123"


def test_use_string_raises_deprecation_warning(handler):
    router = Router()

    with pytest.warns(DeprecationWarning) as record:
        router.add("/<foo:string>", handler)

    assert len(record) == 1
    assert record[0].message.args[0] == (
        "Use of 'string' as a path parameter type is deprected, and will be "
        "removed in Sanic v21.12. Instead, use <foo:str>."
    )


def test_use_number_raises_deprecation_warning(handler):
    router = Router()

    with pytest.warns(DeprecationWarning) as record:
        router.add("/<foo:number>", handler)

    assert len(record) == 1
    assert record[0].message.args[0] == (
        "Use of 'number' as a path parameter type is deprected, and will be "
        "removed in Sanic v21.12. Instead, use <foo:float>."
    )


@pytest.mark.parametrize(
    "value", ("foo-bar", "foobar", "foo-bar-thing123", "foobar123", "123")
)
def test_slug_does_cast(handler, value):
    router = Router()

    router.add("/<slug:slug>", handler)
    router.finalize()

    _, handler, params = router.get(f"/{value}", "BASE")
    retval = handler(**params)

    assert isinstance(retval, str)
    assert retval == value


@pytest.mark.parametrize("value", ("-aaa", "FooBar", "Foo-Bar"))
def test_slug_does_not_cast(handler, value):
    router = Router()

    router.add("/<slug:slug>", handler)
    router.finalize()

    with pytest.raises(NotFound):
        router.get(f"/{value}", "BASE")


def test_correct_slug_v_string(handler):
    router = Router()

    router.add("/<slug:slug>", handler, methods=["slug"])
    router.add("/<anystring:str>", handler, methods=["str"])
    router.finalize()

    _, handler, params = router.get("/foo-bar", "slug")
    retval = handler(**params)

    assert isinstance(retval, str)
    assert retval == "foo-bar"

    _, handler, params = router.get("/FooBar", "str")
    retval = handler(**params)

    assert isinstance(retval, str)
    assert retval == "FooBar"


@pytest.mark.parametrize(
    "value,matches",
    (
        ("foo", True),
        ("FooBar", True),
        ("with123456789", True),
        ("", False),
    ),
)
def test_nonempty_string(handler, value, matches):
    def test(path):
        nonlocal handler
        router = Router()

        router.add(path, handler)
        router.finalize()

        if matches:
            _, handler, params = router.get(f"/{value}", "BASE")
            retval = handler(**params)

            assert isinstance(retval, str)
            assert retval == value
        else:
            with pytest.raises(NotFound):
                router.get(f"/{value}", "BASE")

    for path in ("/<foo>", "/<foo:str>"):
        test(path)


@pytest.mark.parametrize(
    "value",
    (
        "foo",
        "FooBar",
        "with123456789",
        "",
    ),
)
def test_empty_string(handler, value):
    router = Router()

    router.add("/<foo:strorempty>", handler)
    router.finalize()

    _, handler, params = router.get(f"/{value}", "BASE")
    retval = handler(**params)

    assert isinstance(retval, str)
    assert retval == value


def test_nonempty_hierarchy():
    handler1 = Mock()
    handler2 = Mock()
    router = Router()

    router.add("/one/<foo>", handler1)
    router.add("/one/<foo>/<bar>", handler2)
    router.finalize()

    _, handler, params = router.get("/one/two/", "BASE")
    expected = {"foo": "two"}
    handler(**params)

    assert params == expected
    handler1.assert_called_once_with(**expected)
    handler2.assert_not_called()

    handler1.reset_mock()
    handler2.reset_mock()

    _, handler, params = router.get("/one/two/three/", "BASE")
    expected = {"foo": "two", "bar": "three"}
    handler(**params)

    assert params == expected
    handler1.assert_not_called()
    handler2.assert_called_once_with(**expected)


def test_empty_hierarchy():
    handler1 = Mock()
    handler2 = Mock()
    router = Router()

    router.add("/one/<foo>", handler1)
    router.add("/one/<foo>/<bar:strorempty>", handler2)
    router.finalize()

    _, handler, params = router.get("/one/two/", "BASE")
    expected = {"foo": "two", "bar": ""}
    handler(**params)

    assert params == expected
    handler1.assert_not_called()
    handler2.assert_called_once_with(**expected)
