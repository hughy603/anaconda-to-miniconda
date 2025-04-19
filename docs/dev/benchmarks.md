# Performance Benchmarking

This project includes automated performance benchmarking to track code efficiency over time and detect performance regressions.

## Setup

Before running benchmarks for the first time, you need to initialize the `gh-pages` branch where benchmark results will be stored:

1. Go to GitHub Actions tab in your repository
1. Select the "Initialize gh-pages Branch" workflow
1. Click "Run workflow"
1. Type "yes" in the confirmation field and click "Run workflow"
1. Wait for the workflow to complete successfully

This is a one-time setup that creates the necessary structure for storing benchmark results.

## How Benchmarks Work

The benchmark workflow:

1. Runs automatically on:

   - Pull requests to `master` or `develop` branches
   - Pushes to `master` or `develop` branches
   - Weekly schedule (Monday at midnight UTC)
   - Manual triggers via workflow_dispatch

1. Uses pytest-benchmark to measure performance metrics:

   - Execution time (mean, min, max)
   - Standard deviation
   - Rounds per second

1. Stores results in the `gh-pages` branch:

   - Results are saved in the `dev/bench` directory
   - Historical data is preserved for trend analysis
   - Visualizations are automatically generated

## Adding Custom Benchmarks

Benchmarks are stored in the `tests/benchmarks/` directory. To add a new benchmark:

1. Create a new file in `tests/benchmarks/` with a name starting with `test_`
1. Write benchmark functions using the pytest-benchmark fixture:

```python
def test_my_function(benchmark):
    # Setup code here (not benchmarked)
    result = benchmark(lambda: my_function_to_test())
    # Assertions here (not benchmarked)
    assert result is not None
```

## Viewing Results

Benchmark results are published to GitHub Pages:

- URL: `https://yourusername.github.io/conda-forge-converter/dev/bench/`
- The page shows performance trends over time
- You can filter by specific benchmark tests
- Charts visualize performance changes between commits

## Performance Regression Alerts

The benchmark workflow is configured to detect performance regressions:

- Alert threshold: 200% (performance twice as slow as before)
- Alerts are posted as comments on pull requests
- The workflow will not fail on alerts (configurable via `fail-on-alert` parameter)
- Alerts mention the configured user(s) for notification

## Troubleshooting

If you encounter issues with the benchmark workflow:

1. **Missing gh-pages branch**: Run the "Initialize gh-pages Branch" workflow
1. **No benchmark tests found**: The workflow will create a sample benchmark test automatically
1. **Benchmark fails to run**: Check the workflow logs for specific error messages
1. **Results not appearing**: Verify that the `auto-push` parameter is set to `true` in the workflow

## Local Benchmark Testing

You can run benchmarks locally to test performance before pushing changes:

```bash
# Install pytest-benchmark
pip install pytest-benchmark

# Run all benchmarks
python -m pytest tests/benchmarks/

# Run specific benchmark
python -m pytest tests/benchmarks/test_specific.py

# Generate JSON output
python -m pytest tests/benchmarks/ --benchmark-json=benchmark-results.json
```

Local benchmark results are not automatically published to the gh-pages branch.
