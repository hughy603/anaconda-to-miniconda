"""Basic performance benchmarks for the conda-forge-converter package."""

from conda_forge_converter import __version__


def test_version_access(benchmark):
    """Benchmark accessing the version (baseline benchmark)."""
    result = benchmark(lambda: __version__)
    assert result is not None


def test_string_operations(benchmark):
    """Benchmark basic string operations."""

    def string_ops():
        text = "conda-forge-converter"
        return text.upper() + "_" + text.lower()

    result = benchmark(string_ops)
    assert "CONDA-FORGE-CONVERTER_conda-forge-converter" == result


def test_list_comprehension(benchmark):
    """Benchmark list comprehension performance."""

    def list_comp():
        return [i * i for i in range(1000)]

    result = benchmark(list_comp)
    assert len(result) == 1000
    assert result[0] == 0
    assert result[999] == 999 * 999


def test_dict_operations(benchmark):
    """Benchmark dictionary operations."""

    def dict_ops():
        d = {}
        for i in range(100):
            d[f"key_{i}"] = i * 10
        return d

    result = benchmark(dict_ops)
    assert len(result) == 100
    assert result["key_0"] == 0
    assert result["key_99"] == 990
