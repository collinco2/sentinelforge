#!/bin/bash
set -e

echo "===== Cleaning Python cache ====="
python scripts/clean_pycache.py

echo "===== Running Python tests ====="
make test-ci

echo "===== Rebuilding React dependencies ====="
cd sentinelforge-ui
rm -rf node_modules package-lock.json
npm install --legacy-peer-deps

echo "===== Testing React application ====="
npm test

echo "===== All tests passed successfully! ====="
echo "You can now run: git push origin main"
echo "And trigger a manual CI run at: https://github.com/collinco2/sentinelforge/actions" 