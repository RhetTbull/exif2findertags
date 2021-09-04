""" Test exif2findertags CLI, requires exiftool to be installed (https://exiftool.org/)"""

import pathlib
from shutil import copyfile, which

import exif2findertags
import osxmetadata
import pytest
from click.testing import CliRunner

TEST_IMAGE = "tests/apples.jpeg"
TEST_VIDEO = "tests/Jellyfish.mov"


@pytest.fixture(scope="session")
def exiftool_path():
    """return path of exiftool, cache result"""
    exiftool_path = which("exiftool")
    if exiftool_path:
        return exiftool_path.rstrip()
    else:
        raise FileNotFoundError(
            "Could not find exiftool. Please download and install from "
            "https://exiftool.org/"
        )


@pytest.fixture(scope="session")
def tmp_image(tmpdir_factory):
    tmpdir = tmpdir_factory.mktemp("data")
    return copyfile(
        TEST_IMAGE,
        tmpdir / pathlib.Path(TEST_IMAGE).name,
    )


@pytest.fixture(scope="session")
def tmp_dir(tmpdir_factory):
    tmpdir = pathlib.Path(tmpdir_factory.mktemp("data"))
    dir1 = tmpdir / "photos"
    dir1.mkdir()
    dir2 = tmpdir / "videos"
    dir2.mkdir()

    copyfile(TEST_IMAGE, dir1 / pathlib.Path(TEST_IMAGE).name)
    copyfile(TEST_VIDEO, dir2 / pathlib.Path(TEST_VIDEO).name)

    return tmpdir


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


def test_tag_group(tmp_image):
    """test --tag-group"""
    from exif2findertags.cli import cli

    runner = CliRunner()
    result = runner.invoke(
        cli,
        ["--tag-group", "EXIF", "--verbose", str(tmp_image)],
    )
    assert result.exit_code == 0
    md = osxmetadata.OSXMetaData(str(tmp_image))
    tags = [t.name for t in md.tags]
    for t in ["Flash: 24", "Make: Apple"]:
        assert t in tags
    assert "Keywords: Fruit" not in tags

    # reset tags for next test
    md.tags = []


def test_tag_group_value(tmp_image):
    """test --tag-group --value"""
    from exif2findertags.cli import cli

    runner = CliRunner()
    result = runner.invoke(
        cli,
        ["--tag-group", "EXIF", "--verbose", "--value", str(tmp_image)],
    )
    assert result.exit_code == 0
    md = osxmetadata.OSXMetaData(str(tmp_image))
    tags = [t.name for t in md.tags]
    for t in ["24", "Apple"]:
        assert t in tags
    assert "Fruit" not in tags

    # reset tags for next test
    md.tags = []


def test_tag_match(tmp_image):
    """test --tag-match"""
    from exif2findertags.cli import cli

    runner = CliRunner()
    result = runner.invoke(
        cli,
        ["--tag-match", "Make", "--verbose", str(tmp_image)],
    )
    assert result.exit_code == 0
    md = osxmetadata.OSXMetaData(str(tmp_image))
    tags = [t.name for t in md.tags]
    for t in ["Make: Apple", "LensMake: Apple"]:
        assert t in tags

    # reset tags for next test
    md.tags = []


def test_walk(tmp_dir):
    """test --walk"""
    from exif2findertags.cli import cli

    file1 = str(tmp_dir / "photos" / pathlib.Path(TEST_IMAGE).name)
    file2 = str(tmp_dir / "videos" / pathlib.Path(TEST_VIDEO).name)

    runner = CliRunner()
    result = runner.invoke(
        cli,
        ["--tag", "Make", "--tag", "DisplayName", "--verbose", "--walk", str(tmp_dir)],
    )
    assert result.exit_code == 0

    md1 = osxmetadata.OSXMetaData(file1)
    tags = [t.name for t in md1.tags]
    assert "Make: Apple" in tags

    md2 = osxmetadata.OSXMetaData(file2)
    tags = [t.name for t in md2.tags]
    assert "DisplayName: Jellyfish" in tags

    # reset tags for next test
    md1.tags = []
    md2.tags = []


def test_verbose(tmp_image):
    """test --verbose"""
    from exif2findertags.cli import cli

    runner = CliRunner()
    result = runner.invoke(
        cli,
        ["--tag", "Keywords", "--verbose", str(tmp_image)],
    )
    assert result.exit_code == 0
    assert "Writing Finder tags" in result.output

    # reset tags for next test
    md = osxmetadata.OSXMetaData(str(tmp_image))
    md.tags = []


def test_exiftool_path(tmp_image, exiftool_path):
    """test --exif_tool_path"""
    from exif2findertags.cli import cli

    runner = CliRunner()
    result = runner.invoke(
        cli,
        [
            "--tag",
            "Keywords",
            "--verbose",
            "--exiftool-path",
            exiftool_path,
            str(tmp_image),
        ],
    )
    assert result.exit_code == 0
    md = osxmetadata.OSXMetaData(str(tmp_image))
    tags = [t.name for t in md.tags]
    assert sorted(tags) == ["Keywords: Fruit", "Keywords: Travel"]

    # reset tags for next test
    md.tags = []


def test_fc(tmp_image):
    """test --fc"""
    from exif2findertags.cli import cli

    runner = CliRunner()
    result = runner.invoke(
        cli,
        ["--fc", "Make", "--fc", "ISO", "--verbose", str(tmp_image)],
    )
    assert result.exit_code == 0
    md = osxmetadata.OSXMetaData(str(tmp_image))
    fc = md.findercomment
    assert fc == "Make: Apple\nISO: 20"

    # reset findercomment for next test
    md.findercomment = None


def test_fc_value(tmp_image):
    """test --fc-value"""
    from exif2findertags.cli import cli

    runner = CliRunner()
    result = runner.invoke(
        cli,
        [
            "--fc-value",
            "Make",
            "--fc-value",
            "ISO",
            "--verbose",
            str(tmp_image),
        ],
    )
    assert result.exit_code == 0
    md = osxmetadata.OSXMetaData(str(tmp_image))
    fc = md.findercomment
    assert fc == "Apple\n20"

    # reset findercomment for next test
    md.findercomment = None


def test_dry_run(tmp_image):
    """test --dry-run"""
    from exif2findertags.cli import cli

    runner = CliRunner()
    result = runner.invoke(
        cli,
        [
            "--tag",
            "Make",
            "--fc",
            "ISO",
            "--verbose",
            "--dry-run",
            str(tmp_image),
        ],
    )
    assert result.exit_code == 0
    md = osxmetadata.OSXMetaData(str(tmp_image))
    fc = md.findercomment
    assert not fc
    tags = md.tags
    assert not tags


def test_tag_format(tmp_image):
    """test --tag-format"""
    from exif2findertags.cli import cli

    runner = CliRunner()
    result = runner.invoke(
        cli,
        [
            "--tag",
            "Keywords",
            "--tag-format",
            "{TAG}={VALUE}",
            "--verbose",
            str(tmp_image),
        ],
    )
    assert result.exit_code == 0
    md = osxmetadata.OSXMetaData(str(tmp_image))
    tags = [t.name for t in md.tags]
    assert sorted(tags) == ["Keywords=Fruit", "Keywords=Travel"]

    # reset tags for next test
    md.tags = []


def test_tag_format_group(tmp_image):
    """test --tag-format"""
    from exif2findertags.cli import cli

    runner = CliRunner()
    result = runner.invoke(
        cli,
        [
            "--tag",
            "IPTC:Keywords",
            "--tag-format",
            "{GROUP}:{TAG}={VALUE}",
            "--verbose",
            str(tmp_image),
        ],
    )
    assert result.exit_code == 0
    md = osxmetadata.OSXMetaData(str(tmp_image))
    tags = [t.name for t in md.tags]
    assert sorted(tags) == ["IPTC:Keywords=Fruit", "IPTC:Keywords=Travel"]

    # reset tags for next test
    md.tags = []


def test_fc_format(tmp_image):
    """test --fc-format"""
    from exif2findertags.cli import cli

    runner = CliRunner()
    result = runner.invoke(
        cli,
        [
            "--fc",
            "Make",
            "--fc",
            "ISO",
            "--fc-format",
            "{TAG}={VALUE}",
            "--verbose",
            str(tmp_image),
        ],
    )
    assert result.exit_code == 0
    md = osxmetadata.OSXMetaData(str(tmp_image))
    fc = md.findercomment
    assert fc == "Make=Apple\nISO=20"

    # reset findercomment for next test
    md.findercomment = None


def test_fc_format_filter(tmp_image):
    """test --fc-format with a filter"""
    from exif2findertags.cli import cli

    runner = CliRunner()
    result = runner.invoke(
        cli,
        [
            "--fc",
            "Make",
            "--fc",
            "ISO",
            "--fc-format",
            "{TAG|lower}={VALUE|upper}",
            "--verbose",
            str(tmp_image),
        ],
    )
    assert result.exit_code == 0
    md = osxmetadata.OSXMetaData(str(tmp_image))
    fc = md.findercomment
    assert fc == "make=APPLE\niso=20"

    # reset findercomment for next test
    md.findercomment = None
