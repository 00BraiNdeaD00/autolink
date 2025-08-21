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
    f = tmp_path / "tags.md"

    # basic
    f.write_text("body\n[tags]:# (alpha)")
    new_tags = {"beta", "gamma"}
    combined = autolink.combine_tags(new_tags, f)
    assert combined == {"alpha", "beta", "gamma"}

    # doubled tags
    f.write_text("body\n[tags]:# (alpha)")
    new_tags = {"beta", "alpha"}
    combined = autolink.combine_tags(new_tags, f)
    assert combined == {"alpha", "beta"}

    # long and small tags
    f.write_text("body\n[tags]:# (alpha)")
    new_tags = {"beta", "alpha 2"}
    combined = autolink.combine_tags(new_tags, f)
    assert combined == {"alpha", "beta", "alpha 2"}
    f.write_text("body\n[tags]:# (alpha 2)")
    new_tags = {"beta", "alpha"}
    combined = autolink.combine_tags(new_tags, f)
    assert combined == {"alpha", "beta", "alpha 2"}

    # tempdir = tmp_path / "my_files"
    # tempdir.mkdir()
    # t1 = tempdir / "Hello.md"
    # t1.write_text("Hello World\nabcd\n[tags]:# (test, butter)")
    # t2 = tempdir / "Test_World.md"
    # t2.write_text(f"abc\n def\ntest\nwhy")
    # t3 = tempdir / "abc.md"
    # t3.write_text(f"abc\n def\ntest\nwhy\n[tags]:# ()")
    # t4 = tempdir / "defer.md"
    # t4.write_text(f"abc\n def\ntest\nwhy\n[tags]:# (hello, world,test)")
    # t5 = tempdir / "bernd.md"
    # t5.write_text(f"abc\n def\ntest\nwhy\n[tags]:# (car, ship wreck, )")
    # tags = {"hello", "world", "test"}
    # assert autolink.combine_tags(tags, t1) == {"hello", "world", "test", "butter"}
    # assert autolink.combine_tags(tags, t2) == {"hello", "world", "test"}
    # assert autolink.combine_tags(tags, t3) == {"hello", "world", "test"}
    # assert autolink.combine_tags(tags, t4) == {"hello", "world", "test"}
    # assert autolink.combine_tags(tags, t5) == {
    #     "hello",
    #     "world",
    #     "test",
    #     "ship wreck",
    #     "car",
    # }


def test_add_tags(tmp_path):

    # basic
    f = tmp_path / "tags.md"
    f.write_text("body\n")
    autolink.add_tags({"alpha", "beta"}, f)
    assert "alpha" in f.read_text()

    # Update with new tags
    autolink.add_tags({"alpha", "gamma"}, f)
    text = f.read_text()
    assert "gamma" in text
    assert "beta" in text  # existing tags are preserved

    # check for doubled tag-comment
    f.write_text(
        "Hello World\nabcd\n[tags]:# (bernd,brot,)\n[tags]:# (hello, world, test, )"
    )
    tags = {"butter"}
    autolink.add_tags(tags, f)
    assert autolink.check_tags({"bernd", "brot", "butter"}, f)


def test_add_links(tmp_path):
    f1 = tmp_path / "defs.md"
    f1.write_text("[tags]:# (hello world, world)\n# hello world\n## world")

    f2 = tmp_path / "doc.md"
    f2.write_text("[tags]:# (doc, )\nhello world is not just world")

    autolink.add_links({"hello world", "world"}, f2)
    text = f2.read_text()

    # Both should be linked, but not nested
    assert "[hello world][hello world]" in text
    assert "[world][world]" in text
    # Ensure definitions are appended
    assert "[hello world]:" in text
    assert "[world]:" in text


def test_get_tags_from_comment(tmp_path):
    f = tmp_path / "tags.md"
    f.write_text("body\n[tags]:# (alpha, beta, gamma)")
    tags = autolink.get_tags_from_comment(f)
    assert tags == {"alpha", "beta", "gamma"}

    # Empty tag list
    f.write_text("body\n[tags]:# ()")
    tags = autolink.get_tags_from_comment(f)
    assert tags == set()

    # Bad formating:
    f.write_text("body\n[tags]:# (alpha,beta,gamma)")
    tags = autolink.get_tags_from_comment(f)
    assert tags == {"alpha", "beta", "gamma"}


def test_check_tags(tmp_path):
    f = tmp_path / "tags.md"
    f.write_text("body\n[tags]:# (alpha, beta)")
    assert autolink.check_tags({"alpha", "beta"}, f)
    assert not autolink.check_tags({"alpha"}, f)
    assert not autolink.check_tags({"gamma"}, f)


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
