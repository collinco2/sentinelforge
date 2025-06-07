import React, { useState } from "react";
import { AlertDetailModal } from "./AlertDetailModal";
import { Button } from "./ui/button";

// Example usage of AlertDetailModal component
export function AlertDetailModalExample() {
  const [isModalOpen, setIsModalOpen] = useState(false);

  // Example alert data
  const exampleAlert = {
    id: "alert-12345",
    name: "Suspicious Network Activity Detected",
    description:
      "Multiple failed login attempts detected from external IP address. This may indicate a brute force attack attempt.",
    severity: "high",
    timestamp: 1703123456,
    formatted_time: "2023-12-21 10:30:56",
    threat_type: "Brute Force Attack",
    confidence: 85,
    source: "Network Monitor",
  };

  return (
    <div className="p-6">
      <h2 className="text-xl font-bold mb-4">AlertDetailModal Example</h2>

      <Button
        onClick={() => setIsModalOpen(true)}
        className="bg-blue-600 hover:bg-blue-700"
      >
        Open Alert Details
      </Button>

      <AlertDetailModal
        alert={exampleAlert}
        isOpen={isModalOpen}
        onClose={() => setIsModalOpen(false)}
      />

      <div className="mt-6 p-4 bg-gray-100 rounded-lg">
        <h3 className="font-semibold mb-2">Usage:</h3>
        <pre className="text-sm bg-gray-800 text-green-400 p-3 rounded overflow-x-auto">
          {`import { AlertDetailModal } from "./AlertDetailModal";

// In your component:
const [isModalOpen, setIsModalOpen] = useState(false);
const [selectedAlert, setSelectedAlert] = useState(null);

// To open the modal:
const handleAlertClick = (alert) => {
  setSelectedAlert(alert);
  setIsModalOpen(true);
};

// In your JSX:
<AlertDetailModal
  alert={selectedAlert}
  isOpen={isModalOpen}
  onClose={() => setIsModalOpen(false)}
/>`}
        </pre>
      </div>
    </div>
  );
}
