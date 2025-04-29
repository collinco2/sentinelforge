# Git Hooks for SentinelForge

These hook scripts help ensure code quality by running tests and checks before certain Git operations.

## Available Hooks

- **pre-push**: Runs formatting checks, linter, and critical tests before pushing to the remote repository
  
## Installation

To install the hooks, run the following commands from the project root:

```bash
# Make the hook scripts executable
chmod +x .github/hooks/*

# Link or copy the hooks to your local .git/hooks directory
cp .github/hooks/pre-push .git/hooks/
```

## Using the Hooks

Once installed, the hooks will run automatically when you perform the corresponding Git operation.

For example, when you run `git push`, the pre-push hook will:
1. Check code formatting with ruff
2. Run the linter
3. Run critical tests

If any checks fail, the push will be aborted, and you'll need to fix the issues before pushing again.

## Bypassing Hooks

In case you need to bypass a hook in an emergency situation:

```bash
git push --no-verify
```

**Note**: This should only be used in exceptional circumstances. It's always better to fix the issues. 