import React from 'react';
import { Box, Typography, Container, CssBaseline, ThemeProvider, createTheme } from '@mui/material';
import './App.css';

// Create a theme
const theme = createTheme({
  palette: {
    primary: {
      main: '#1976d2',
    },
    secondary: {
      main: '#dc004e',
    },
  },
});

function App() {
  return (
    <ThemeProvider theme={theme}>
      <CssBaseline />
      <Container maxWidth="lg">
        <Box sx={{ my: 4 }}>
          <Typography variant="h4" component="h1" gutterBottom>
            SentinelForge Dashboard
          </Typography>
          <Typography variant="body1">
            Welcome to SentinelForge - your threat intelligence platform.
            This is a newly restored dashboard. Please reinstall dependencies with npm install.
          </Typography>
        </Box>
      </Container>
    </ThemeProvider>
  );
}

export default App; 