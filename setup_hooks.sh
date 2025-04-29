#!/bin/bash

# Setup script for Git hooks
echo "Setting up Git hooks for SentinelForge..."

# Make sure the hooks directory exists
mkdir -p .git/hooks

# Make hook scripts executable
chmod +x .github/hooks/*

# Copy hooks to Git hooks directory
cp .github/hooks/pre-push .git/hooks/

echo "Hooks installed successfully!"
echo "The following hooks are now active:"
echo "- pre-push: Runs before 'git push' to check formatting, linting, and critical tests"
echo ""
echo "To bypass hooks in exceptional circumstances, use: git push --no-verify"
echo "" 