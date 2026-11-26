import os
import sys

from bar_cadenza.app.paths import resource_root


def test_resource_root_from_source_finds_bundled_files_regardless_of_cwd(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    root = resource_root()
    assert (root / "assets/fonts/NanumGothic-Regular.ttf").is_file()
    assert (root / "content/locales/ko.json").is_file()
    assert os.getcwd() != str(root)


def test_resource_root_uses_pyinstaller_bundle_when_frozen(tmp_path, monkeypatch):
    monkeypatch.setattr(sys, "_MEIPASS", str(tmp_path), raising=False)
    assert resource_root() == tmp_path
