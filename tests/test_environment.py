import customtkinter
import PIL
import pytest


def test_libraries_importable():
    assert customtkinter.__name__ == "customtkinter"
    assert PIL.__name__ == "PIL"
