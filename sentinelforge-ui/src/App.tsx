import React from "react";
import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import { Dashboard } from "./pages/Dashboard";
import { IocDetailPage } from "./pages/IocDetailPage";
import { ShareableIocView } from "./pages/ShareableIocView";
import { AlertTimelinePage } from "./pages/AlertTimelinePage";
import { AlertsPage } from "./pages/AlertsPage";
import "./App.css";

function App() {
  return (
    <div className="dark">
      <div className="min-h-screen bg-background text-foreground">
        <BrowserRouter>
          <Routes>
            <Route path="/" element={<Dashboard />} />
            <Route path="/threat-intel/:iocId" element={<IocDetailPage />} />
            <Route path="/ioc/:iocId" element={<IocDetailPage />} />
            <Route path="/share/ioc/:iocValue" element={<ShareableIocView />} />
            <Route path="/alerts" element={<AlertsPage />} />
            <Route path="/alerts/timeline" element={<AlertTimelinePage />} />
            <Route path="*" element={<Navigate to="/" replace />} />
          </Routes>
        </BrowserRouter>
      </div>
    </div>
  );
}

export default App;
