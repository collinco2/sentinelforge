# SentinelForge UI

This is the modern React-based user interface for SentinelForge, providing a comprehensive security operations dashboard.

## CI/CD Status
- Latest React UI workflow tests: All dependencies and build processes verified
- Node.js environment: Compatible with CI/CD pipeline

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