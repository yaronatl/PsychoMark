import cv2
import pytest

from psychomark.calibration import calibrate
from psychomark.demo import make_layout, render_blank, render_filled
from psychomark.engine import Engine


@pytest.fixture(scope="session", autouse=True)
def bounded_threads():
    cv2.setNumThreads(2)


@pytest.fixture(scope="session")
def sheet(tmp_path_factory):
    root = tmp_path_factory.mktemp("sheet")
    layout = make_layout()
    blank = render_blank(layout)
    filled, truth = render_filled(blank, layout)
    template_path = root / "template.json"
    calibrate(blank, layout, template_path)
    return {"root": root, "layout": layout, "blank": blank, "filled": filled, "truth": truth,
            "template_path": template_path, "engine": Engine.from_file(template_path)}
