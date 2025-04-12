#!/bin/bash
set -e

# Script to initialize the gh-pages branch for benchmark results
# This only needs to be run once to set up the branch

# Create and switch to a temporary branch
git checkout --orphan gh-pages-temp

# Remove all files from staging
git rm -rf --cached .

# Create necessary directories
mkdir -p dev/bench

# Create a basic index file
cat > index.html << EOF
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta http-equiv="refresh" content="0;url=./dev/bench/">
    <title>Benchmark Results</title>
</head>
<body>
    <p>Redirecting to <a href="./dev/bench/">benchmark results</a>...</p>
</body>
</html>
EOF

# Create a placeholder in the benchmark directory
cat > dev/bench/index.html << EOF
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Benchmark Results</title>
</head>
<body>
    <h1>Benchmark Results</h1>
    <p>No benchmark data available yet. Run the benchmark workflow to generate data.</p>
</body>
</html>
EOF

# Add and commit the files
git add index.html dev/bench/index.html
git commit -m "Initialize gh-pages branch for benchmark results"

# Rename the branch to gh-pages
git branch -m gh-pages

# Force push to create the gh-pages branch
git push -f origin gh-pages

# Switch back to the original branch
git checkout -
echo "gh-pages branch has been initialized successfully!"
