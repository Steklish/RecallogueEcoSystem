import React from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';

const MessageList = ({ messages, onDeleteMessage, isThinking, isStreaming }) => {
  const handleDeleteMessage = (index) => {
    onDeleteMessage(index);
  };

  // Function to render tables properly within markdown
  const renderTable = (props) => {
    const { children } = props;
    return (
      <div className="table-container">
        <table>{children}</table>
      </div>
    );
  };

  return (
    <div className="message-list">
      {messages.map((message, index) => (
        <div key={message.id || index} className="message-container">
          <div className={`message ${message.sender === 'user' ? 'user' : 'bot'}`}>
            <ReactMarkdown
              children={message.text}
              remarkPlugins={[remarkGfm]}
              components={{
                table: renderTable,
                img: (props) => <img {...props} style={{ maxWidth: '100%' }} />,
                a: (props) => <a {...props} target="_blank" rel="noopener noreferrer" />,
                p: (props) => <p {...props} />,
                li: (props) => <li {...props} />,
              }}
            />
            {message.retrieved_docs && message.retrieved_docs.length > 0 && (
              <div className="retrieved-docs">
                <strong>Sources:</strong>
                <ul>
                  {message.retrieved_docs.map((doc, idx) => (
                    <li key={idx}>
                      <a href={doc.url} title={doc.title}>
                        {doc.title}
                      </a>
                    </li>
                  ))}
                </ul>
              </div>
            )}
          </div>
          {message.sender !== 'user' && (
            <button
              className="delete-message-btn icon-button"
              onClick={() => handleDeleteMessage(index)}
              title="Delete message"
            >
              ×
            </button>
          )}
        </div>
      ))}
      {(isThinking || isStreaming) && (
        <div className="message bot">
          <em>{isThinking ? 'Thinking...' : 'Streaming response...'}</em>
        </div>
      )}
    </div>
  );
};

export default MessageList;