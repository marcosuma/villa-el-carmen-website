from datetime import date

import pytest

from sitebuild.build import build, load_all

BUILD_DATE = date(2026, 10, 5)


@pytest.fixture(scope="session")
def loaded():
    return load_all()


@pytest.fixture(scope="session")
def site(loaded):
    return loaded[0]


@pytest.fixture(scope="session")
def pages(loaded):
    return loaded[2]


@pytest.fixture(scope="session")
def built_site(tmp_path_factory):
    root = tmp_path_factory.mktemp("site")
    build(root=root, today=BUILD_DATE)
    return root
