from rpod.gpu import format_available_gpu_counts, format_price


def test_format_available_gpu_counts():
    assert format_available_gpu_counts([1, 2, 4]) == "1, 2, 4"
    assert format_available_gpu_counts([]) == ""
    assert format_available_gpu_counts(None) == ""


def test_format_price():
    assert format_price(0.163) == "$0.163/hr"
    assert format_price(None) == ""
