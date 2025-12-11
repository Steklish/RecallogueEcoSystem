import pytest
from unittest.mock import Mock, patch, MagicMock
from app.src.services.ai_backends.embedding_client import EmbeddingClient


def test_embed_text_success():
    # Create an EmbeddingClient instance
    client = EmbeddingClient(base="http://test-server:8080")
    
    # Mock the requests.post method
    with patch('app.src.services.ai_backends.embedding_client.requests.post') as mock_post:
        # Create a mock response
        mock_response = Mock()
        mock_response.json.return_value = [{'embedding': [[1.0, 2.0, 3.0]]}]  # Mock embedding result
        mock_response.raise_for_status.return_value = None
        mock_post.return_value = mock_response
        
        # Test embedding text
        result = client.embed_text("test text")
        
        # Verify that requests.post was called correctly
        mock_post.assert_called_once_with(
            "http://test-server:8080/embedding",
            json={"content": "test text"},
            headers={"Content-Type": "application/json"},
        )
        
        # Verify the result
        assert result == [1.0, 2.0, 3.0]


def test_embed_text_error_handling():
    # Create an EmbeddingClient instance
    client = EmbeddingClient(base="http://test-server:8080")
    
    # Mock the requests.post method to raise an exception
    with patch('app.src.services.ai_backends.embedding_client.requests.post') as mock_post:
        mock_post.side_effect = Exception("Network error")
        
        # Test embedding text with error
        result = client.embed_text("test text")
        
        # Should return an empty list on error
        assert result == []


def test_embed_texts_success():
    # Create an EmbeddingClient instance
    client = EmbeddingClient(base="http://test-server:8080")
    
    # Mock the requests.post method
    with patch('app.src.services.ai_backends.embedding_client.requests.post') as mock_post:
        # Create a mock response for batch embedding
        mock_response = Mock()
        mock_response.json.return_value = [
            {'embedding': [[1.0, 2.0, 3.0]]},
            {'embedding': [[4.0, 5.0, 6.0]]}
        ]
        mock_response.raise_for_status.return_value = None
        mock_post.return_value = mock_response
        
        # Test embedding multiple texts
        texts = ["text1", "text2"]
        result = client.embed_texts(texts)
        
        # Verify that requests.post was called correctly
        mock_post.assert_called_once_with(
            "http://test-server:8080/embedding",
            json={"content": texts},
            headers={"Content-Type": "application/json"},
        )
        
        # Verify the result
        assert result == [[1.0, 2.0, 3.0], [4.0, 5.0, 6.0]]


def test_embed_texts_with_batching():
    # Create an EmbeddingClient instance with small batch size
    client = EmbeddingClient(base="http://test-server:8080")
    
    # Mock the requests.post method
    with patch('app.src.services.ai_backends.embedding_client.requests.post') as mock_post:
        # First call returns for first batch, second call for second batch
        responses = [
            Mock(json=lambda: [{'embedding': [[1.0, 2.0]]}, {'embedding': [[3.0, 4.0]]}], raise_for_status=lambda: None),
            Mock(json=lambda: [{'embedding': [[5.0, 6.0]]}], raise_for_status=lambda: None)
        ]
        mock_post.side_effect = responses
        
        # Test embedding multiple texts with small batch size
        texts = ["text1", "text2", "text3"]
        result = client.embed_texts(texts, batch_size=2)
        
        # Verify that requests.post was called twice (for 2 batches)
        assert mock_post.call_count == 2
        
        # Verify the results
        assert result == [[1.0, 2.0], [3.0, 4.0], [5.0, 6.0]]


def test_embed_texts_error_handling():
    # Create an EmbeddingClient instance
    client = EmbeddingClient(base="http://test-server:8080")
    
    # Mock the requests.post method to raise an exception
    with patch('app.src.services.ai_backends.embedding_client.requests.post') as mock_post:
        mock_post.side_effect = Exception("Network error")
        
        # Test embedding multiple texts with error
        texts = ["text1", "text2"]
        result = client.embed_texts(texts)
        
        # Should return a list of empty lists for each text
        assert result == [[], []]


def test_embed_texts_response_parsing_error():
    # Create an EmbeddingClient instance
    client = EmbeddingClient(base="http://test-server:8080")
    
    # Mock the requests.post method with invalid response
    with patch('app.src.services.ai_backends.embedding_client.requests.post') as mock_post:
        mock_response = Mock()
        mock_response.json.return_value = [{'invalid': 'structure'}]  # Missing 'embedding' key
        mock_response.raise_for_status.return_value = None
        mock_post.return_value = mock_response
        
        # Test embedding multiple texts with invalid response structure
        texts = ["text1", "text2"]
        result = client.embed_texts(texts)
        
        # Should return empty lists due to parsing error
        assert result == [[], []]


def test_initialization():
    # Test initialization with default base URL
    client = EmbeddingClient()
    
    # Base URL should be set
    assert client.base is not None


def test_initialization_with_custom_base():
    # Test initialization with custom base URL
    custom_base = "http://custom-server:9090"
    client = EmbeddingClient(base=custom_base)
    
    # Base URL should be set to custom value
    assert client.base == custom_base