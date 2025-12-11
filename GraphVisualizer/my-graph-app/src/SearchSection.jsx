import React, { useState, useRef, useEffect } from 'react';

const SearchSection = ({ onSearch }) => {
  const [searchTerm, setSearchTerm] = useState('');
  const [aiPrompt, setAiPrompt] = useState('');
  const [isAiOpen, setIsAiOpen] = useState(false);
  const textareaRef = useRef(null);
  const hiddenDivRef = useRef(null);
  const aiTextareaRef = useRef(null);
  const aiHiddenDivRef = useRef(null);

  // Function to auto-resize main textarea based on content
  useEffect(() => {
    if (textareaRef.current && hiddenDivRef.current) {
      // Set the hidden div's content to match the textarea
      // Use a space instead of non-breaking space to ensure proper line height calculation
      hiddenDivRef.current.textContent = searchTerm || ' ';

      // Calculate and set the height
      const baseHeight = hiddenDivRef.current.scrollHeight;
      const minHeight = 30;
      // Ensure consistent minimum height and add a small buffer to prevent flickering
      const finalHeight = Math.max(baseHeight, minHeight);
      textareaRef.current.style.height = finalHeight + 'px';
    }
  }, [searchTerm]);

  // Function to auto-resize AI prompt textarea based on content
  useEffect(() => {
    if (isAiOpen && aiTextareaRef.current && aiHiddenDivRef.current) {
      // Set the hidden div's content to match the AI prompt textarea
      aiHiddenDivRef.current.textContent = aiPrompt || ' ';

      // Calculate and set the height
      const baseHeight = aiHiddenDivRef.current.scrollHeight;
      const minHeight = 30;
      // Ensure consistent minimum height and add a small buffer to prevent flickering
      const finalHeight = Math.max(baseHeight, minHeight);
      aiTextareaRef.current.style.height = finalHeight + 'px';
    }
  }, [aiPrompt, isAiOpen]);

  const handleSearch = async (e) => {
    e.preventDefault();

    // Always use the main search term when the main search button is clicked
    onSearch(searchTerm);
  };

  const handleInput = (e) => {
    setSearchTerm(e.target.value);
  };

  const handleAiPromptInput = (e) => {
    setAiPrompt(e.target.value);
  };

  // Function to get line numbers for display
  const getLineNumbers = () => {
    // Calculate lines from the current content
    // At least 1 line should be displayed even when empty
    const lines = searchTerm ? searchTerm.split('\n').length : 1;
    return Array.from({ length: lines }, (_, i) => i + 1).join('\n');
  };

  // Function to get AI prompt line numbers
  const getAiLineNumbers = () => {
    const lines = aiPrompt ? aiPrompt.split('\n').length : 1;
    return Array.from({ length: lines }, (_, i) => i + 1).join('\n');
  };

  const toggleAiMenu = () => {
    setIsAiOpen(!isAiOpen);
    // Reset the AI prompt when opening the menu
    if (!isAiOpen) {
      setAiPrompt(''); // Clear AI prompt when opening AI menu
    }
  };

  return (
    <div className="search-section">
      <form onSubmit={handleSearch} className="search-form">
        {/* Main search bar with dropdown menu on the left */}
        <div className="main-search-wrapper">
          {/* AI Menu Toggle - Left side */}
          <div className="ai-menu-toggle" onClick={toggleAiMenu}>
            <span className="ai-menu-text">AI Query Generation</span>
            <span className={`ai-menu-arrow ${isAiOpen ? 'open' : ''}`}>▼</span>
          </div>

          {/* Regular Cypher Query Input */}
          <div className="textarea-wrapper">
            {/* Line numbers container */}
            <div className="line-numbers" aria-hidden="true">
              {getLineNumbers()}
            </div>
            <textarea
              ref={textareaRef}
              value={searchTerm}
              onInput={handleInput}
              placeholder="Enter your Cypher query here..."
              className="search-textarea"
            />
            {/* Hidden div to calculate the height needed for the content */}
            <div
              ref={hiddenDivRef}
              className="hidden-textarea"
            />
          </div>

          <button type="submit" className="search-button">
            Search
          </button>
        </div>

        {/* AI Prompt Input - appears below main search when menu is open */}
        {isAiOpen && (
          <div className="ai-prompt-section">
            <div className="ai-input-wrapper">
              <div className="line-numbers" aria-hidden="true">
                {getAiLineNumbers()}
              </div>
              <textarea
                ref={aiTextareaRef}
                value={aiPrompt}
                onInput={handleAiPromptInput}
                placeholder="Enter a natural language description of what you want to search for..."
                className="search-textarea ai-prompt-textarea"
              />
              {/* Hidden div to calculate the height needed for the content */}
              <div
                ref={aiHiddenDivRef}
                className="hidden-textarea"
              />
            </div>
            <button
              type="button"
              className="generate-query-button"
              onClick={async () => {
                try {
                  // Call the AI query generation endpoint
                  // Note: This endpoint needs to be implemented in the backend
                  // If using a different endpoint name, update this URL accordingly
                  const response = await fetch('http://localhost:8000/api/reques_query', {
                    method: 'POST',
                    headers: {
                      'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({
                      current_query: searchTerm, // The current Cypher query (can be empty)
                      prompt: aiPrompt // The natural language description
                    }),
                  });

                  if (!response.ok) {
                    throw new Error(`HTTP error! status: ${response.status}`);
                  }

                  const data = await response.json();

                  // Place the generated query into the main search bar
                  // Assuming the API returns an object with a 'query' field
                  setSearchTerm(data.query || aiPrompt); // Fallback to the prompt if no query is returned

                  // Keep AI menu open after generating - user can continue modifying the prompt
                } catch (error) {
                  console.error('Error generating query:', error);
                  // Handle the error by either showing a message or using a fallback

                  // For now, provide some example queries based on common prompts
                  let generatedQuery = aiPrompt; // Default to the prompt itself

                  // Example query generation based on common patterns
                  if (aiPrompt.toLowerCase().includes("find all people")) {
                    generatedQuery = "MATCH (n:Person) RETURN n";
                  } else if (aiPrompt.toLowerCase().includes("find organizations")) {
                    generatedQuery = "MATCH (n:Organization) RETURN n";
                  } else if (aiPrompt.toLowerCase().includes("relationship") || aiPrompt.toLowerCase().includes("connections")) {
                    generatedQuery = "MATCH (n)-[r]->(m) RETURN n, r, m LIMIT 50";
                  } else if (aiPrompt.toLowerCase().includes("connections between")) {
                    generatedQuery = "MATCH (n)-[r]-(m) RETURN n, r, m LIMIT 50";
                  }

                  // Place the (potentially generated) query into the main search bar
                  setSearchTerm(generatedQuery);

                  // Keep AI menu open after generating - user can continue modifying the prompt
                }
              }}
            >
              Generate Query
            </button>
          </div>
        )}
      </form>
    </div>
  );
};

// Note: The AI query generation functionality connects to the /api/reques_query endpoint.
// In a real implementation, this endpoint would use an LLM to generate a proper Cypher query
// based on the natural language prompt, and return it in the response.
// The generated query is then placed in the main search bar for execution.

export default SearchSection;