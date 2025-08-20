import pytest
import os

import autolink


def test_get_tags_from_name(tmp_path):
    tempdir = tmp_path / "my_files"
    tempdir.mkdir()
    t1 = tempdir / "Hello.md"
    t1.write_text("Hello World")
    t2 = tempdir / "Test_World.md"
    t2.write_text("Hello World")
    tags = autolink.get_tags_from_name(tempdir)
    assert tags == {"hello", "world", "test"}


def test_get_tags_from_headers(tmp_path):
    tempdir = tmp_path / "my_files"
    tempdir.mkdir()
    t1 = tempdir / "Hello.md"
    t1.write_text("# Hello\nText\n# World")
    t2 = tempdir / "Test_World.md"
    t2.write_text("Hello World\n## Test")
    tags = autolink.get_tags_from_name(tempdir)
    assert tags == {"hello", "world", "test"}


def test_check_direct_links(tmp_path):
    tempdir = tmp_path / "my_files"
    tempdir.mkdir()
    t1 = tempdir / "hello.md"
    t1.write_text("Hello World, world")
    t2 = tempdir / "Test_World.md"
    t2.write_text(f"[Hello](./myfiles/Hello.md) World")
    with open(t1) as f:
        print(f.read())
    tags = {"hello", "world", "test"}
    assert autolink.check_direct_links(tags, t1) == False
    assert autolink.check_direct_links(tags, t2) == True
    # assert False


def test_combine_tags(tmp_path):
    tempdir = tmp_path / "my_files"
    tempdir.mkdir()
    t1 = tempdir / "Hello.md"
    t1.write_text("Hello World\nabcd\n[tags]:# (test, butter)")
    t2 = tempdir / "Test_World.md"
    t2.write_text(f"abc\n def\ntest\nwhy")
    t3 = tempdir / "abc.md"
    t3.write_text(f"abc\n def\ntest\nwhy\n[tags]:# ()")
    t4 = tempdir / "defer.md"
    t4.write_text(f"abc\n def\ntest\nwhy\n[tags]:# (hello, world,test)")
    t5 = tempdir / "bernd.md"
    t5.write_text(f"abc\n def\ntest\nwhy\n[tags]:# (car, ship wreck, )")
    tags = {"hello", "world", "test"}
    assert autolink.combine_tags(tags, t1) == {"hello", "world", "test", "butter"}
    assert autolink.combine_tags(tags, t2) == {"hello", "world", "test"}
    assert autolink.combine_tags(tags, t3) == {"hello", "world", "test"}
    assert autolink.combine_tags(tags, t4) == {"hello", "world", "test"}
    assert autolink.combine_tags(tags, t5) == {
        "hello",
        "world",
        "test",
        "ship wreck",
        "car",
    }


def test_add_tags(tmp_path):
    tempdir = tmp_path / "my_files"
    tempdir.mkdir()
    t1 = tempdir / "Hello.md"
    t1.write_text("Hello World\nabcd\n[tags]:# (test, butter)")
    tags = {"hello", "world", "test"}
    autolink.add_tags(tags, t1)
    with open(t1) as f:
        print(f.read(), "(after)")
    print()
    assert autolink.check_tags({"hello", "world", "test", "butter"}, t1)

    t2 = tempdir / "World.md"
    t2.write_text("Hello World\nabcd\n")
    tags = {"hello", "world", "test"}
    autolink.add_tags(tags, t2)
    with open(t2) as f:
        print(f.read(), "(after)")
    print()
    assert autolink.check_tags({"hello", "world", "test"}, t2)

    t3 = tempdir / "Bernd.md"
    t3.write_text(
        "Hello World\nabcd\n[tags]:# (bernd,brot,)\n[tags]:# (hello, world, test, )"
    )
    tags = {"butter"}
    autolink.add_tags(tags, t3)
    with open(t3) as f:
        print(f.read(), "(after)")
    print()
    assert autolink.check_tags({"bernd", "brot", "butter"}, t3)
