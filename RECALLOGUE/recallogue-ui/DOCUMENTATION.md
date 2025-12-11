# Recallogue UI - Architecture and Components Documentation

## Overview
Recallogue UI is a chat-based application with document management capabilities. The interface is organized in a three-panel layout with authentication protection.

## Main UI Principles

### 1. Layout Structure
- **Three-panel split layout** using react-split for resizable panels
- **Left Panel**: Threads list and Settings
- **Center Panel**: Chat interface
- **Right Panel**: Document management

### 2. Design System
- Dark theme with specific CSS variables for consistent styling
- Consistent color palette defined in CSS variables
- Responsive design with smooth transitions
- Custom scrollbars for better UX

### 3. Navigation Patterns
- Thread-based conversation system
- Document management alongside conversations
- Centralized settings panel

## Component Architecture

### Core Components

#### 1. App Component
- **Location**: `src/App.jsx`
- **Function**: Main entry point that manages authentication state
- **Props**: None
- **Logic**: Checks authentication and renders Login or MainApp accordingly

#### 2. MainApp Component
- **Location**: `src/MainApp.jsx`
- **Function**: Main application interface with three-panel layout
- **Props**: None
- **Logic**: Manages thread selection, server status, and coordinates between panels

#### 3. Header Component
- **Location**: `src/components/Header.jsx`
- **Function**: Displays user info and logout functionality
- **Props**: None (uses context)
- **Features**: User greeting, logout button

### Panel Components

#### 4. Threads Component
- **Location**: `src/components/Threads.jsx`
- **Function**: Displays list of conversation threads
- **Props**: 
  - `currentThread`: Currently selected thread
  - `setCurrentThread`: Function to set current thread
  - `currentThreadDetails`: Details of current thread
  - `threadsVersion`: Version for refresh control

#### 5. Chat Component
- **Location**: `src/components/Chat.jsx`
- **Function**: Main chat interface with message history
- **Props**:
  - `currentThread`: Thread being displayed
  - `onThreadUpdate`: Callback to refresh thread
  - `disabled`: Whether chat is disabled

#### 6. MessageList Component
- **Location**: `src/components/MessageList.jsx`
- **Function**: Displays messages in conversation thread
- **Props**:
  - `messages`: Array of messages to display
  - `onDeleteMessage`: Callback to delete specific message
  - `isThinking`: Flag for AI processing state
  - `isStreaming`: Flag for response streaming state

#### 7. ChatInput Component
- **Location**: `src/components/ChatInput.jsx`
- **Function**: Input area for sending messages
- **Props**:
  - `onSendMessage`: Callback to send message
  - `disabled`: Whether input is disabled

#### 8. DocumentManagement Component
- **Location**: `src/components/DocumentManagement.jsx`
- **Function**: Interface for managing documents
- **Props**:
  - `currentThread`: Current thread context
  - `onThreadUpdate`: Callback to refresh thread
  - `onDocumentChange`: Callback for document changes

#### 9. Settings Component
- **Location**: `src/components/Settings.jsx`
- **Function**: Application configuration panel
- **Props**:
  - `disabled`: Whether settings are disabled

### Authentication Components

#### 10. Login Component
- **Location**: `src/components/auth/Login.jsx`
- **Function**: User authentication interface
- **Props**: None (uses context)
- **Features**: 
  - Username/password fields
  - Password visibility toggle
  - Form validation
  - Error handling

#### 11. ProtectedRoute Component
- **Location**: `src/components/auth/ProtectedRoute.jsx`
- **Function**: Route protection wrapper
- **Props**: children components to render when authenticated

## Contexts

### 12. AuthContext
- **Location**: `src/contexts/AuthContext.jsx`
- **Function**: Manages authentication state across the application
- **Providers**: 
  - `AuthProvider`: Wraps the application
  - `useAuth`: Custom hook to access auth state
- **State**: 
  - `user`: Current user object
  - `isLoading`: Loading state during auth check
  - `isAuthenticated`: Authentication status

## Key Functions

### 1. Authentication Flow
```javascript
// Check auth status on app load
// Show login if not authenticated
// Protect main app with auth context
```

### 2. Thread Management
```javascript
// Fetch thread details from API
// Update thread history
// Handle thread selection
```

### 3. Message Handling
```javascript
// Send messages to backend
// Stream responses in real-time
// Display message history
// Handle message deletion
```

### 4. Document Management
```javascript
// Upload documents
// Associate with threads
// Manage document list
```

## Styling Principles

### 1. CSS Variables (src/App.css)
- `--background-color`: Main background (#1c1c1e)
- `--text-color`: Text color (#e1e1e0)
- `--primary-color`: Accent color (#a9967f)
- `--panel-background`: Panel backgrounds (#2a2a2c)

### 2. Component Classes
- Consistent naming pattern: `{component}-{element}`
- Example: `.chat-panel`, `.message-list`, `.thread-actions`

## API Integration

### 1. Environment Variables
- `VITE_API_BASE_URL`: Backend server address

### 2. API Endpoints Used
- `/api/status`: Server status check (currently disabled)
- `/api/threads/{id}/details`: Thread details
- `/api/threads/{id}/messages/{index}`: Delete messages
- `/api/threads/{id}/chat`: Send messages (streaming)

## Development Patterns

### 1. State Management
- React hooks for local component state
- Context API for global state (authentication)
- Props drilling for component communication

### 2. Error Handling
- Try/catch blocks for API calls
- Form validation with user feedback
- Loading states during async operations

### 3. Accessibility
- Semantic HTML elements
- Proper labeling
- Keyboard navigation support