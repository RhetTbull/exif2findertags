"""Test PhotoTemplate """

import pathlib
from os import getcwd

import pytest
from exif2findertags.phototemplate import PhotoTemplate, RenderOptions

TEST_IMAGE = "tests/apples.jpeg"

TEMPLATES = {
    "{EXIF:Make}": ["Apple"],
    "{Make}": ["Apple"],
    "Keyword={IPTC:Keywords}": ["Keyword=Travel", "Keyword=Fruit"],
    "{created}": ["2021-08-22T11:43:56.359000-04:00"],
    "{created.year}": ["2021"],
    "{modified.month}": ["August"],
    "Foo={XMP:Foo}": [],
}


def test_phototemplate_1():
    """Test PhotoTemplate"""
    test_image = pathlib.Path(getcwd()) / TEST_IMAGE
    t = PhotoTemplate(test_image)
    options = RenderOptions()

    for template, value in TEMPLATES.items():
        rendered, _ = t.render(template, options)
        assert sorted(rendered) == sorted(value)


def test_phototemplate_tag():
    """Test PhotoTemplate with {GROUP} {TAG} format"""
    test_image = pathlib.Path(getcwd()) / TEST_IMAGE
    t = PhotoTemplate(test_image)
    options = RenderOptions(tag="EXIF:Make")
    rendered, _ = t.render("{GROUP} - {TAG} = {VALUE}", options)
    assert rendered == ["EXIF - Make = Apple"]


def test_phototemplate_tag_filter():
    """Test PhotoTemplate with {GROUP} {TAG} format and filters"""
    test_image = pathlib.Path(getcwd()) / TEST_IMAGE
    t = PhotoTemplate(test_image)
    options = RenderOptions(tag="EXIF:Make")
    rendered, _ = t.render("{GROUP|lower} - {TAG|lower} = {VALUE|upper}", options)
    assert rendered == ["exif - make = APPLE"]
