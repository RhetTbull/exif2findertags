""" Test exif2findertags CLI"""

import pathlib
from shutil import copyfile

import exif2findertags
import osxmetadata
import pytest
from click.testing import CliRunner

TEST_IMAGE = "tests/apples.jpeg"


# @pytest.fixture(scope="module")
# def test_image(tmp_path):
#     """copy test image to temp file"""
#     return copyfile(
#         TEST_IMAGE,
#         str(tmp_path.name / pathlib.Path(TEST_IMAGE).name),
#     )


@pytest.fixture(scope="session")
def tmp_image(tmpdir_factory):
    tmpdir = tmpdir_factory.mktemp("data")
    assert pathlib.Path(tmpdir).is_dir()
    tmpfile = copyfile(
        TEST_IMAGE,
        tmpdir / pathlib.Path(TEST_IMAGE).name,
    )
    return tmpfile


def test_tag(tmp_image):
    """test --tag"""
    from exif2findertags.cli import cli

    runner = CliRunner()
    result = runner.invoke(
        cli,
        ["--tag", "Keywords", "--verbose", str(tmp_image)],
    )
    assert result.exit_code == 0
    md = osxmetadata.OSXMetaData(str(tmp_image))
    tags = [t.name for t in md.tags]
    assert sorted(tags) == ["Keywords: Fruit", "Keywords: Travel"]

    # reset tags for next test
    md.tags = []


def test_tag_value(tmp_image):
    """test --tag-value"""
    from exif2findertags.cli import cli

    runner = CliRunner()
    result = runner.invoke(
        cli,
        ["--tag-value", "Keywords", "--verbose", str(tmp_image)],
    )
    assert result.exit_code == 0
    md = osxmetadata.OSXMetaData(str(tmp_image))
    tags = [t.name for t in md.tags]
    assert sorted(tags) == ["Fruit", "Travel"]

    # reset tags for next test
    md.tags = []


def test_all_tags(tmp_image):
    """test --all-tags"""
    from exif2findertags.cli import cli

    runner = CliRunner()
    result = runner.invoke(
        cli,
        ["--all-tags", "--verbose", str(tmp_image)],
    )
    assert result.exit_code == 0

    # spot check a few tags
    md = osxmetadata.OSXMetaData(str(tmp_image))
    tags = [t.name for t in md.tags]
    for t in [
        "Keywords: Fruit",
        "Keywords: Travel",
        "Flash: 24",
        "Make: Apple",
    ]:
        assert t in tags

    # reset tags for next test
    md.tags = []


def test_all_tags_group(tmp_image):
    """test --group"""
    from exif2findertags.cli import cli

    runner = CliRunner()
    result = runner.invoke(
        cli,
        ["--all-tags", "--group", "--verbose", str(tmp_image)],
    )
    assert result.exit_code == 0

    # spot check a few tags
    md = osxmetadata.OSXMetaData(str(tmp_image))
    tags = [t.name for t in md.tags]
    for t in [
        "IPTC:Keywords: Fruit",
        "IPTC:Keywords: Travel",
        "EXIF:Flash: 24",
        "EXIF:Make: Apple",
    ]:
        assert t in tags

    # reset tags for next test
    md.tags = []
