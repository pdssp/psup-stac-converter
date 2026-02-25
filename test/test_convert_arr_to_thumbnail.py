import numpy as np
import pytest
from PIL import Image

from psup_stac_converter.utils.file_utils import convert_arr_to_thumbnail


@pytest.fixture
def sample_2d_grayscale():
    return np.random.rand(64, 64)  # 2D grayscale


@pytest.fixture
def sample_3d_rgb():
    return np.random.rand(64, 64, 3)  # 3D RGB


@pytest.fixture
def sample_1d_with_channels():
    return np.random.rand(32, 3)  # 1D w/ channel


@pytest.fixture
def sample_with_single_nan():
    data = np.random.rand(64, 64)
    data[0, 0] = np.nan
    return data


@pytest.fixture
def sample_all_nans():
    data = np.empty((64, 64))
    data[:] = np.nan
    return data


@pytest.fixture
def sample_with_single_inf():
    data = np.random.rand(64, 64)
    data[0, 0] = np.inf
    return data


def test_2d_grayscale_to_l(sample_2d_grayscale):
    img = convert_arr_to_thumbnail(sample_2d_grayscale, (32, 32), mode="L")
    assert isinstance(img, Image.Image)
    assert img.mode == "L"
    assert img.size == (32, 32)


def test_3d_rgb_to_rgb(sample_3d_rgb):
    img = convert_arr_to_thumbnail(sample_3d_rgb, (32, 32), mode="RGB")
    assert isinstance(img, Image.Image)
    assert img.mode == "RGB"
    assert img.size == (32, 32)


def test_1d_with_channels_to_rgb(sample_1d_with_channels):
    img = convert_arr_to_thumbnail(sample_1d_with_channels, (320, 10), mode="RGB")
    assert isinstance(img, Image.Image)
    assert img.mode == "RGB"
    assert img.size == (320, 10)


def test_with_cmap():
    data = np.random.rand(64, 64)
    img = convert_arr_to_thumbnail(data, (32, 32), mode="RGB", cmap="viridis")
    assert isinstance(img, Image.Image)
    assert img.mode == "RGB"
    assert img.size == (32, 32)


def test_with_nan_raises_error(sample_with_single_nan):
    img = convert_arr_to_thumbnail(sample_with_single_nan, (32, 32), mode="L")
    assert isinstance(img, Image.Image)
    assert img.mode == "L"
    assert img.size == (32, 32)


def test_with_all_nan_raises_error(sample_all_nans):
    with pytest.raises(ValueError, match="NaN"):
        convert_arr_to_thumbnail(sample_all_nans, (32, 32), mode="L")


def test_with_inf_raises_error(sample_with_single_inf):
    img = convert_arr_to_thumbnail(sample_with_single_inf, (32, 32), mode="L")
    assert isinstance(img, Image.Image)
    assert img.mode == "L"
    assert img.size == (32, 32)


def test_output_mode_rgba():
    data = np.random.rand(64, 64)
    img = convert_arr_to_thumbnail(data, (32, 32), mode="RGBA", cmap="plasma")
    assert isinstance(img, Image.Image)
    assert img.mode == "RGBA"
    assert img.size == (32, 32)


def test_edge_case_empty_array():
    with pytest.raises(ValueError):
        convert_arr_to_thumbnail(np.array([]), (32, 32), mode="L")


def test_edge_case_single_pixel():
    data = np.random.rand(1, 1, 3)
    img = convert_arr_to_thumbnail(data, (10, 10), mode="RGB")
    assert isinstance(img, Image.Image)
    assert img.mode == "RGB"
    assert img.size == (10, 10)
