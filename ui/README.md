# SentinelForge UI

This is a restored version of the SentinelForge UI dashboard. The original directory was missing or deleted, so this is a fresh setup to get the project back up and running.

## Getting Started

1. Install dependencies:
   ```
   npm install
   ```

2. Start the development server:
   ```
   npm start
   ```

3. The app will run on port 3006 by default:
   ```
   PORT=3006 npm start
   ```

## Project Structure

- `/src` - Source code
  - `/components` - Reusable React components
  - `/pages` - Page components
  - `/services` - API services and utilities

## Connecting to Backend

The UI expects an API server running at http://localhost:5056. Make sure the backend is running:

```
cd /Users/Collins/sentinelforge
python api_server.py
```

## Original File Recovery

If you find the original `sentinelforge-ui` directory or files, those can be copied back to replace this temporary solution.

## Next Steps

1. Rebuild any missing components
2. Restore any custom styling and business logic
3. Make sure all API integrations are working properly 