import React, { createContext, useContext, useState, useEffect } from 'react';

const AuthContext = createContext();

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [isLoading, setIsLoading] = useState(true);

  // Check for existing session on app load
  useEffect(() => {
    const checkAuthStatus = async () => {
      try {
        // Try to make a request to a protected endpoint to verify if we have a valid session
        const response = await fetch(`${import.meta.env.VITE_API_BASE_URL || process.env.VITE_API_BASE_URL}/api/v1/threads/`, {
          method: 'GET',
          credentials: 'include',  // Include cookies to check for valid session
        });

        if (response.ok) {
          // If the request succeeded, we have a valid session
          // We can't get the user details directly from this response, so we'll just confirm authentication
          // We'll try to get user details from localStorage as fallback
          const storedUser = localStorage.getItem('recallogue_user');
          if (storedUser) {
            try {
              const parsedUser = JSON.parse(storedUser);
              setUser(parsedUser);
            } catch (error) {
              console.error('Error parsing stored user:', error);
              // We're authenticated but can't parse stored user, so we'll create a minimal user object
              setUser({ username: 'authenticated_user' }); // This will be updated once we have a proper user endpoint
            }
          } else {
            // We're authenticated but no user info stored, set a placeholder
            setUser({ username: 'authenticated_user' });
          }
        } else {
          // If the request failed, there's no valid session
          // Optionally check for locally stored user info as fallback
          const storedUser = localStorage.getItem('recallogue_user');
          if (storedUser) {
            try {
              const parsedUser = JSON.parse(storedUser);
              setUser(parsedUser);
            } catch (error) {
              console.error('Error parsing stored user:', error);
              localStorage.removeItem('recallogue_user');
            }
          }
        }
      } catch (error) {
        console.error('Error checking auth status:', error);
        console.warn('CORS or network error - this may be due to backend CORS configuration.');
        // Fallback to stored user if there's a network error
        const storedUser = localStorage.getItem('recallogue_user');
        if (storedUser) {
          try {
            const parsedUser = JSON.parse(storedUser);
            setUser(parsedUser);
          } catch (error) {
            console.error('Error parsing stored user:', error);
            localStorage.removeItem('recallogue_user');
          }
        }
      } finally {
        setIsLoading(false);
      }
    };

    checkAuthStatus();
  }, []);

  const login = (userData) => {
    setUser(userData);
    localStorage.setItem('recallogue_user', JSON.stringify(userData));
  };

  const logout = async () => {
    try {
      // Call the backend logout endpoint to clear the session cookie
      await fetch(`${import.meta.env.VITE_API_BASE_URL || process.env.VITE_API_BASE_URL}/api/v1/auth/logout`, {
        method: 'POST',
        credentials: 'include', // Include cookies in the request
      });
    } catch (error) {
      console.error('Logout API call failed:', error);
      // Even if the API call fails, still clear local state
    } finally {
      setUser(null);
      localStorage.removeItem('recallogue_user');
    }
  };

  const value = {
    user,
    login,
    logout,
    isLoading,
    isAuthenticated: !!user
  };

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  );
};