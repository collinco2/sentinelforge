import React from 'react';
import { Dashboard } from "./pages/Dashboard";
import './App.css';

function App() {
  return (
    <div className="dark">
      <div className="min-h-screen bg-background text-foreground">
        <Dashboard />
      </div>
    </div>
  );
}

export default App; 