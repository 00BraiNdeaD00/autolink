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
    t1 = tempdir / "a.md"
    t1.write_text("# Hello\nText\n# World")
    t2 = tempdir / "b.md"
    t2.write_text("Hello World\n## Test")
    tags = autolink.get_tags_from_headers(t1.read_text())
    tags.update(autolink.get_tags_from_headers(t2.read_text()))
    assert tags == {"Hello", "World", "Test"}


def test_add_tags():
    # basic
    s = "body\n"
    s = autolink.add_tags({"alpha", "beta"}, s)
    assert "alpha" in s

    # Update with new tags
    s = autolink.add_tags({"alpha", "gamma"}, s)
    assert "gamma" in s
    assert "beta" in s  # existing tags are preserved

    # check for doubled tag-comment
    s = "Hello World\nabcd\n[tags]:# (bernd,brot,)\n[tags]:# (hello, world, test, )"
    tags = {"butter"}
    s = autolink.add_tags(tags, s)
    assert autolink.get_tags_from_comment(s) == {"bernd", "brot", "butter"}


def test_add_links():
    ls = "[tags]:# (doc, hello world, world, )\n\n[doc](a.md#doc);\n\n[world](b.md#magic)\n\n[hello world](c.md#bernd)"
    s2 = "[tags]:# (doc, )\nhello world is not just world"
    s2 = autolink.add_links_from_list(s2, ls)

    # Both should be linked, but not nested
    assert "[hello world][hello world]" in s2
    assert "[world][world]" in s2
    # Ensure definitions are appended
    assert "[hello world]:" in s2
    assert "[world]:" in s2


def test_get_tags_from_comment(tmp_path):
    s = "body\n[tags]:# (alpha, beta, gamma)"
    tags = autolink.get_tags_from_comment(s)
    assert tags == {"alpha", "beta", "gamma"}

    # Empty tag list
    s = "body\n[tags]:# ()"
    tags = autolink.get_tags_from_comment(s)
    assert tags == set()

    # Bad formating:
    s = "body\n[tags]:# (alpha,beta,gamma)"
    tags = autolink.get_tags_from_comment(s)
    assert tags == {"alpha", "beta", "gamma"}


def test_get_origin(tmp_path):
    f1 = tmp_path / "alpha.md"
    f1.write_text("content\n[tags]:# (alpha)")
    f2 = tmp_path / "beta.md"
    f2.write_text("content\n[tags]:# (beta)")
    assert autolink.get_origin("beta", tmp_path).endswith("beta.md")
    assert autolink.get_origin("alpha", tmp_path).endswith("alpha.md")
    with pytest.raises(ValueError) as e:
        autolink.get_origin("gamma", tmp_path)
    assert str(e.value) == f"no tag: gamma was found in {tmp_path}"


def test_initialize_tagging(tmp_path):
    # ? Running initialize_tagging on an empty folder should not crash.
    autolink.initialize_tagging(tmp_path)
    assert list(tmp_path.iterdir()) == []

    # ? File with no headers should still get a [tags]:# entry (empty).
    f = tmp_path / "plain.md"
    f.write_text("Just some text, no headers here.")
    autolink.initialize_tagging(tmp_path)
    content = f.read_text().lower()
    assert "[tags]:" in content  # placeholder tags inserted

    # ? basic setup
    f1 = tmp_path / "a.md"
    f1.write_text("# Alpha\ncontent, beta")
    f2 = tmp_path / "b.md"
    f2.write_text("# Beta\ncontent with Alpha")

    autolink.initialize_tagging(tmp_path)

    text_a = f1.read_text().lower()
    text_b = f2.read_text().lower()

    # tags should have been added
    assert "[tags]:" in text_a
    assert "[tags]:" in text_b
    # "alpha" in b.md should be turned into a link
    assert "[alpha][alpha]" in text_b
    # definitions should be appended
    assert any(line.startswith("[alpha]:") for line in text_b.splitlines())
    assert any(line.startswith("[beta]:") for line in text_a.splitlines())

    # ? Ensure cross-links are added between multiple related files.
    f1.write_text("# Alpha")
    f2.write_text("# Beta\nAlpha appears here")
    f3 = tmp_path / "c.md"
    f3.write_text("# Gamma\nAlpha and Beta appear here")

    autolink.initialize_tagging(tmp_path)

    text3 = f3.read_text().lower()
    # should link both alpha and beta
    assert "[alpha][alpha]" in text3
    assert "[beta][beta]" in text3
    assert any(line.startswith("[alpha]:") for line in text3.splitlines())
    assert any(line.startswith("[beta]:") for line in text3.splitlines())

    # ? Words 'world' and 'hello world' should not conflict.
    f1.write_text("# Hello World\nSome text\n## World")
    f2.write_text("# Doc\nhello world and world")

    autolink.initialize_tagging(tmp_path)

    text1 = f1.read_text().lower()
    text2 = f2.read_text().lower()

    # both files should get tags
    assert "[tags]:" in text1
    assert "[tags]:" in text2
    # longer tag should not be destroyed by shorter one
    assert "[hello world][hello world]" in text2
    assert "[world][world]" in text2

    # ? Existing [tags]:# entry should be preserved and merged.
    f1.write_text("# Alpha\ncontent\n[tags]:# (custom)")
    f2.write_text("# Beta\nAlpha here is custom")

    autolink.initialize_tagging(tmp_path)

    # a.md should keep 'custom' and add 'alpha'
    content1 = f1.read_text().lower()
    assert "custom" in content1
    assert "alpha" in content1

    # b.md should link to alpha and custom
    content2 = f2.read_text().lower()
    assert "[alpha][alpha]" in content2
    assert any(line.startswith("[alpha]:") for line in content2.splitlines())
    assert "[custom][custom]" in content2
    assert any(line.startswith("[custom]:") for line in content2.splitlines())

    # ? Tags containing regex characters should still work safely.
    f1 = tmp_path / "c++.md"
    f1.write_text("# C++\nSome text")
    f2 = tmp_path / "doc.md"
    f2.write_text("# Doc\nC++ is mentioned here")

    autolink.initialize_tagging(tmp_path)

    text1 = f1.read_text().lower()
    text2 = f2.read_text().lower()

    # ensure escaped properly and replaced with links
    assert "[c++]" in text2
    assert any(line.startswith("[c++]") for line in text2.splitlines())
