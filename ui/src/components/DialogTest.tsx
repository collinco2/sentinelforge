import React, { useState } from "react";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "./ui/dialog";
import { Button } from "./ui/button";

export const DialogTest: React.FC = () => {
  const [isOpen, setIsOpen] = useState(false);

  console.log("🔍 DialogTest: Component rendered, isOpen:", isOpen);

  return (
    <div className="p-4 space-y-4">
      <h2 className="text-xl font-bold">Dialog Test Component</h2>
      
      {/* Test 1: Basic Dialog with DialogTrigger */}
      <div className="space-y-2">
        <h3 className="font-semibold">Test 1: DialogTrigger (like API Key component)</h3>
        <Dialog>
          <DialogTrigger asChild>
            <Button 
              onClick={() => console.log("🔍 DialogTest: DialogTrigger button clicked")}
            >
              Open Dialog (DialogTrigger)
            </Button>
          </DialogTrigger>
          <DialogContent 
            style={{ 
              backgroundColor: 'red', 
              border: '3px solid yellow',
              zIndex: 9999 
            }}
          >
            <DialogHeader>
              <DialogTitle>Test Dialog via DialogTrigger</DialogTitle>
            </DialogHeader>
            <div className="p-4">
              <p>This dialog was opened via DialogTrigger (like the API Key modal)</p>
            </div>
          </DialogContent>
        </Dialog>
      </div>

      {/* Test 2: Controlled Dialog */}
      <div className="space-y-2">
        <h3 className="font-semibold">Test 2: Controlled Dialog</h3>
        <Button 
          onClick={() => {
            console.log("🔍 DialogTest: Manual open button clicked");
            setIsOpen(true);
          }}
        >
          Open Dialog (Manual Control)
        </Button>
        <Dialog open={isOpen} onOpenChange={setIsOpen}>
          <DialogContent 
            style={{ 
              backgroundColor: 'blue', 
              border: '3px solid white',
              zIndex: 9999 
            }}
          >
            <DialogHeader>
              <DialogTitle>Test Dialog via State Control</DialogTitle>
            </DialogHeader>
            <div className="p-4">
              <p>This dialog was opened via state control</p>
              <Button onClick={() => setIsOpen(false)}>Close</Button>
            </div>
          </DialogContent>
        </Dialog>
      </div>

      {/* Test 3: Simple state display */}
      <div className="space-y-2">
        <h3 className="font-semibold">Test 3: State Debug</h3>
        <p>Current isOpen state: {isOpen ? "true" : "false"}</p>
        <Button onClick={() => setIsOpen(!isOpen)}>
          Toggle State (Current: {isOpen ? "true" : "false"})
        </Button>
      </div>
    </div>
  );
};
