import React, { useState, useEffect, useCallback } from 'react';
import { useAuth } from './contexts/AuthContext';
import Split from 'react-split';
import axios from 'axios';
import Threads from './components/Threads';
import Chat from './components/Chat';
import DocumentManagement from './components/DocumentManagement';
import Settings from './components/Settings';
import LoadingIndicator from './components/LoadingIndicator';
import Header from './components/Header';
import './App.css';

function App() {
  const { isAuthenticated, isLoading } = useAuth();
  const [currentThread, setCurrentThread] = useState(null);
  const [currentThreadDetails, setCurrentThreadDetails] = useState(null);
  const [serverStatus, setServerStatus] = useState('loading');
  const [threadsVersion, setThreadsVersion] = useState(0);

  const forceThreadsRefetch = () => {
    setThreadsVersion(v => v + 1);
  };

  useEffect(() => {
    if (!isAuthenticated) return;

    // For now, we'll assume the server is ready if authentication is successful
    // In a real implementation, you would have a proper status endpoint
    setServerStatus('ready');

    // If you have a different endpoint to check server status, replace the above line with:
    /*
    const pollStatus = async () => {
      try {
        const response = await axios.get(`${import.meta.env.VITE_API_BASE_URL || process.env.VITE_API_BASE_URL}/api/v1/status`, {
          withCredentials: true  // Include cookies in the request
        });
        if (response.data.status === 'ready' || response.data.status === 'error') {
          setServerStatus(response.data.status);
        } else {
          setTimeout(pollStatus, 2000);
        }
      } catch (error) {
        console.error("Error polling server status:", error);
        setServerStatus('error');
      }
    };
    pollStatus();
    */
  }, [isAuthenticated]);

  const fetchThreadDetails = useCallback(async () => {
    if (!isAuthenticated) return;

    if (currentThread) {
      try {
        const response = await axios.get(`${import.meta.env.VITE_API_BASE_URL || process.env.VITE_API_BASE_URL}/api/v1/threads/${currentThread.id}/details`, {
          withCredentials: true  // Include cookies in the request
        });
        setCurrentThreadDetails(response.data);
      } catch (error) {
        console.error("Error fetching thread details:", error);
        setCurrentThreadDetails(null);
      }
    } else {
      setCurrentThreadDetails(null);
    }
  }, [currentThread, isAuthenticated]);

  useEffect(() => {
    if (isAuthenticated) {
      fetchThreadDetails();
    }
  }, [fetchThreadDetails, isAuthenticated]);

  if (isLoading) {
    return <div className="app-container">Loading...</div>;
  }

  if (!isAuthenticated) {
    return <div className="app-container">Please log in to access Recallogue</div>;
  }

  if (serverStatus === 'loading') {
    return <LoadingIndicator />;
  }

  if (serverStatus === 'error') {
    return <div className="app-container">Error connecting to the server. Please check the server logs.</div>;
  }

  return (
    <div className="main-app-container">
      <Header />
      <Split
        className="app-container"
        sizes={[15, 70, 15]}
        minSize={250}
        expandToMin={false}
        gutterSize={10}
        gutterAlign="center"
        snapOffset={30}
        dragInterval={1}
        direction="horizontal"
        cursor="col-resize"
      >
        <Split
          className="left-panel"
          direction="vertical"
          sizes={[60, 40]}
          minSize={100}
        >
          <Threads
            currentThread={currentThread}
            setCurrentThread={setCurrentThread}
            currentThreadDetails={currentThreadDetails}
            threadsVersion={threadsVersion}
          />
          <Settings disabled={serverStatus !== 'ready'} />
        </Split>
        <Chat
          currentThread={currentThreadDetails}
          onThreadUpdate={fetchThreadDetails}
          disabled={serverStatus !== 'ready'}
        />
        <DocumentManagement
          currentThread={currentThreadDetails}
          onThreadUpdate={fetchThreadDetails}
          onDocumentChange={forceThreadsRefetch}
        />
      </Split>
    </div>
  );
}

export default App;