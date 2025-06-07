import { useEffect } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';

/**
 * This component fixes issues with direct navigation to routes
 * when using a proxy configuration that might interfere with client-side routing
 */
export const NavigationFix = () => {
  const location = useLocation();
  const navigate = useNavigate();

  useEffect(() => {
    // If we get a proxy error in the URL, try to recover
    if (location.pathname.includes('Error occurred while trying to proxy')) {
      // Extract the original intended URL path
      const match = location.pathname.match(/proxy: localhost:3000(\/[^\\s]+)/i);
      if (match && match[1]) {
        const intendedPath = match[1];
        console.log('Recovering navigation to:', intendedPath);
        // Navigate to the intended path
        navigate(intendedPath);
      } else {
        // If we can't recover, go to home
        navigate('/');
      }
    }
  }, [location.pathname, navigate]);

  return null;
}; 