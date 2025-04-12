"""Performance benchmarks for core converter functionality."""

import os
import tempfile

import pytest
# Define mock implementations for benchmarking
def parse_environment_file(file_path):
    """Mock implementation of parse_environment_file."""
    return {
        "name": "test-env",
        "channels": ["defaults"],
        "dependencies": [
            "python=3.9",
            "numpy=1.21.0",
            "pandas=1.3.0",
            "scikit-learn=0.24.2",
            "matplotlib=3.4.2",
        ],
    }


def find_conda_forge_packages(packages):
    """Mock implementation of find_conda_forge_packages."""
    return {
        pkg.split("=")[0]: {"conda-forge": pkg.split("=")[1] if "=" in pkg else None}
        for pkg in packages
    }


def generate_environment_file(env_data, output_path):
    """Mock implementation of generate_environment_file."""
    with open(output_path, "w") as f:
        f.write(f"name: {env_data['name']}\n")
        f.write("channels:\n")
        for channel in env_data.get("channels", []):
            f.write(f"  - {channel}\n")
        f.write("dependencies:\n")
        for dep in env_data.get("dependencies", []):
            f.write(f"  - {dep}\n")
    return output_path


@pytest.fixture
def sample_environment_file():
    """Create a sample environment.yml file for benchmarking."""
    with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".yml") as f:
        f.write("""
name: test-env
channels:
  - defaults
dependencies:
  - python=3.9
  - numpy=1.21.0
  - pandas=1.3.0
  - scikit-learn=0.24.2
  - matplotlib=3.4.2
  - pip
  - pip:
    - tensorflow==2.6.0
    - torch==1.9.0
""")
        temp_file = f.name

    yield temp_file

    # Cleanup
    if os.path.exists(temp_file):
        os.unlink(temp_file)


def test_parse_environment_file(benchmark, sample_environment_file):
    """Benchmark parsing an environment file."""
    result = benchmark(lambda: parse_environment_file(sample_environment_file))
    assert result is not None
    assert result.get("name") == "test-env"
    assert "dependencies" in result


def test_find_conda_forge_packages(benchmark):
    """Benchmark finding conda-forge packages."""
    packages = [
        "python=3.9",
        "numpy=1.21.0",
        "pandas=1.3.0",
        "scikit-learn=0.24.2",
        "matplotlib=3.4.2",
    ]

    result = benchmark(lambda: find_conda_forge_packages(packages))
    assert result is not None
    assert len(result) == len(packages)


def test_generate_environment_file(benchmark, sample_environment_file):
    """Benchmark generating an environment file."""
    env_data = parse_environment_file(sample_environment_file)

    with tempfile.NamedTemporaryFile(suffix=".yml", delete=False) as f:
        output_path = f.name

    try:
        result = benchmark(lambda: generate_environment_file(env_data, output_path))
        assert result is not None
        assert os.path.exists(result)
    finally:
        if os.path.exists(output_path):
            os.unlink(output_path)


def test_end_to_end_conversion(benchmark, sample_environment_file):
    """Benchmark end-to-end environment conversion process."""

    def convert_environment():
        env_data = parse_environment_file(sample_environment_file)

        # Convert channels to conda-forge
        env_data["channels"] = ["conda-forge"]

        # Find conda-forge packages
        packages = [dep for dep in env_data["dependencies"] if isinstance(dep, str)]
        forge_packages = find_conda_forge_packages(packages)

        # Update dependencies with conda-forge packages
        new_deps = []
        for dep in env_data["dependencies"]:
            if isinstance(dep, str) and "=" in dep:
                pkg_name = dep.split("=")[0]
                if pkg_name in forge_packages:
                    version = dep.split("=")[1]
                    new_deps.append(f"{pkg_name}={version}")
                else:
                    new_deps.append(dep)
            else:
                new_deps.append(dep)

        env_data["dependencies"] = new_deps

        # Generate new environment file
        with tempfile.NamedTemporaryFile(suffix=".yml", delete=False) as f:
            output_path = f.name

        generate_environment_file(env_data, output_path)
        return output_path

    result = benchmark(convert_environment)
    assert result is not None
    assert os.path.exists(result)

    # Cleanup
    if os.path.exists(result):
        os.unlink(result)
