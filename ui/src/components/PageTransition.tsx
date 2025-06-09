import React, { useEffect, useState } from "react";
import { useLocation } from "react-router-dom";
import { cn } from "@/lib/utils";

interface PageTransitionProps {
  children: React.ReactNode;
  className?: string;
}

export function PageTransition({ children, className }: PageTransitionProps) {
  const location = useLocation();
  const [isTransitioning, setIsTransitioning] = useState(false);
  const [displayLocation, setDisplayLocation] = useState(location);

  useEffect(() => {
    if (location !== displayLocation) {
      setIsTransitioning(true);

      // Start exit animation
      const exitTimer = setTimeout(() => {
        setDisplayLocation(location);

        // Start enter animation
        const enterTimer = setTimeout(() => {
          setIsTransitioning(false);
        }, 50);

        return () => clearTimeout(enterTimer);
      }, 150);

      return () => clearTimeout(exitTimer);
    }
  }, [location, displayLocation]);

  return (
    <div
      className={cn(
        "transition-all duration-200 ease-in-out",
        isTransitioning
          ? "opacity-0 transform translate-y-2"
          : "opacity-100 transform translate-y-0",
        className,
      )}
    >
      {children}
    </div>
  );
}
