import pytest
from models.category import Category


def test_category_creates_with_valid_fields():
    cat = Category(id="c1", name="Dairy", color="#ffffff")
    assert cat.id == "c1"
    assert cat.name == "Dairy"
    assert cat.color == "#ffffff"


def test_category_empty_id_raises():
    with pytest.raises(ValueError, match="id"):
        Category(id="", name="Dairy", color="#fff")


def test_category_whitespace_id_raises():
    with pytest.raises(ValueError, match="id"):
        Category(id="   ", name="Dairy", color="#fff")


def test_category_empty_name_raises():
    with pytest.raises(ValueError, match="name"):
        Category(id="c1", name="", color="#fff")


def test_category_whitespace_name_raises():
    with pytest.raises(ValueError, match="name"):
        Category(id="c1", name="  ", color="#fff")


def test_category_empty_color_raises():
    with pytest.raises(ValueError, match="color"):
        Category(id="c1", name="Dairy", color="")


def test_category_whitespace_color_raises():
    with pytest.raises(ValueError, match="color"):
        Category(id="c1", name="Dairy", color="  ")


def test_category_equality_by_fields():
    c1 = Category(id="c1", name="Dairy", color="#fff")
    c2 = Category(id="c1", name="Dairy", color="#fff")
    assert c1 == c2


def test_category_inequality_different_id():
    c1 = Category(id="c1", name="Dairy", color="#fff")
    c2 = Category(id="c2", name="Dairy", color="#fff")
    assert c1 != c2
