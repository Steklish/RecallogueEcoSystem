import os
import tempfile
import pytest
from unittest.mock import Mock, patch
from app.src.services.chroma_client import ChromaClient
from app.src.services.ai_backends.embedding_client import EmbeddingClient


def test_chroma_client_initialization():
    # Mock the embedding client
    mock_embedding_client = Mock(spec=EmbeddingClient)
    
    # Test initialization
    with patch('chromadb.PersistentClient') as mock_persistent_client:
        mock_client_instance = Mock()
        mock_persistent_client.return_value = mock_client_instance
        
        # Create a collection mock
        mock_collection = Mock()
        mock_documents_collection = Mock()
        
        # Configure the client to return our mock collections
        mock_client_instance.get_or_create_collection.side_effect = [mock_collection, mock_documents_collection]
        
        chroma_client = ChromaClient(embedding_client=mock_embedding_client, path=tempfile.mkdtemp())
        
        # Verify that collections were created
        assert mock_client_instance.get_or_create_collection.call_count == 2
        assert chroma_client.collection == mock_collection
        assert chroma_client.documents_collection == mock_documents_collection


def test_store_chunks():
    mock_embedding_client = Mock(spec=EmbeddingClient)
    
    with patch('chromadb.PersistentClient') as mock_persistent_client:
        mock_client_instance = Mock()
        mock_persistent_client.return_value = mock_client_instance
        
        mock_collection = Mock()
        mock_documents_collection = Mock()
        mock_client_instance.get_or_create_collection.side_effect = [mock_collection, mock_documents_collection]
        
        chroma_client = ChromaClient(embedding_client=mock_embedding_client, path=tempfile.mkdtemp())
        
        # Test storing chunks
        chunks = ["chunk1", "chunk2", "chunk3"]
        embeddings = [[1.0, 2.0], [3.0, 4.0], [5.0, 6.0]]
        metadatas = [{"doc_id": "1"}, {"doc_id": "2"}, {"doc_id": "3"}]
        
        result_ids = chroma_client.store_chunks(chunks, embeddings, metadatas)
        
        # Verify that the add method was called on the collection
        assert mock_collection.add.called
        args, kwargs = mock_collection.add.call_args
        assert len(kwargs['ids']) == 3
        assert kwargs['documents'] == chunks
        assert kwargs['embeddings'] == embeddings
        assert kwargs['metadatas'] == metadatas
        assert len(result_ids) == 3


def test_delete_chunks():
    mock_embedding_client = Mock(spec=EmbeddingClient)
    
    with patch('chromadb.PersistentClient') as mock_persistent_client:
        mock_client_instance = Mock()
        mock_persistent_client.return_value = mock_client_instance
        
        mock_collection = Mock()
        mock_documents_collection = Mock()
        mock_client_instance.get_or_create_collection.side_effect = [mock_collection, mock_documents_collection]
        
        chroma_client = ChromaClient(embedding_client=mock_embedding_client, path=tempfile.mkdtemp())
        
        # Test deleting chunks
        chunk_ids = ["id1", "id2", "id3"]
        chroma_client.delete_chunks(chunk_ids)
        
        # Verify that the delete method was called on the collection
        assert mock_collection.delete.called
        args, kwargs = mock_collection.delete.call_args
        assert kwargs['ids'] == chunk_ids


def test_get_collection_count():
    mock_embedding_client = Mock(spec=EmbeddingClient)
    
    with patch('chromadb.PersistentClient') as mock_persistent_client:
        mock_client_instance = Mock()
        mock_persistent_client.return_value = mock_client_instance
        
        mock_collection = Mock()
        mock_documents_collection = Mock()
        mock_client_instance.get_or_create_collection.side_effect = [mock_collection, mock_documents_collection]
        
        # Set up count return value
        mock_collection.count.return_value = 42
        
        chroma_client = ChromaClient(embedding_client=mock_embedding_client, path=tempfile.mkdtemp())
        
        # Test getting collection count
        count = chroma_client.get_collection_count()
        
        # Verify that the count method was called on the collection
        assert mock_collection.count.called
        assert count == 42


def test_add_document():
    mock_embedding_client = Mock(spec=EmbeddingClient)
    mock_embedding_client.embed_text.return_value = [1.0, 2.0, 3.0]  # Mock embedding
    
    with patch('chromadb.PersistentClient') as mock_persistent_client:
        mock_client_instance = Mock()
        mock_persistent_client.return_value = mock_client_instance
        
        mock_collection = Mock()
        mock_documents_collection = Mock()
        mock_client_instance.get_or_create_collection.side_effect = [mock_collection, mock_documents_collection]
        
        chroma_client = ChromaClient(embedding_client=mock_embedding_client, path=tempfile.mkdtemp())
        
        # Test adding a document
        doc_id = "doc123"
        doc_name = "test_document"
        metadata = {"type": "pdf", "size": 1024}
        
        chroma_client.add_document(doc_id, doc_name, metadata)
        
        # Verify that embed_text was called
        assert mock_embedding_client.embed_text.called
        assert mock_embedding_client.embed_text.call_args[0][0] == doc_name
        
        # Verify that the documents collection add was called
        assert mock_documents_collection.add.called
        args, kwargs = mock_documents_collection.add.call_args
        assert kwargs['ids'] == [doc_id]
        assert kwargs['documents'] == [doc_name]
        assert kwargs['metadatas'] == [metadata]


def test_get_all_documents():
    mock_embedding_client = Mock(spec=EmbeddingClient)
    
    with patch('chromadb.PersistentClient') as mock_persistent_client:
        mock_client_instance = Mock()
        mock_persistent_client.return_value = mock_client_instance
        
        mock_collection = Mock()
        mock_documents_collection = Mock()
        mock_client_instance.get_or_create_collection.side_effect = [mock_collection, mock_documents_collection]

        # Mock the list_collections method to return a list of collections
        mock_collection_obj = Mock()
        mock_collection_obj.name = "rag_collection"
        mock_client_instance.list_collections.return_value = [mock_collection_obj]
        
        # Mock the get method to return test data
        mock_documents_collection.get.return_value = {
            'ids': ['doc1', 'doc2'],
            'metadatas': [
                {'name': 'doc1.pdf', 'type': 'pdf', 'size': 1024, 'uploadedAt': '2023-01-01'},
                {'name': 'doc2.docx', 'type': 'docx', 'size': 2048, 'uploadedAt': '2023-01-02'}
            ]
        }
        
        chroma_client = ChromaClient(embedding_client=mock_embedding_client, path=tempfile.mkdtemp())
        
        # Test getting all documents
        documents = chroma_client.get_all_documents()
        
        # Verify that the get method was called on the documents collection
        assert mock_documents_collection.get.called
        assert len(documents) == 2
        assert documents[0]['name'] == 'doc1.pdf'
        assert documents[1]['name'] == 'doc2.docx'


def test_get_document():
    mock_embedding_client = Mock(spec=EmbeddingClient)
    
    with patch('chromadb.PersistentClient') as mock_persistent_client:
        mock_client_instance = Mock()
        mock_persistent_client.return_value = mock_client_instance
        
        mock_collection = Mock()
        mock_documents_collection = Mock()
        mock_client_instance.get_or_create_collection.side_effect = [mock_collection, mock_documents_collection]
        
        # Mock the get method to return test data
        mock_documents_collection.get.return_value = {
            'ids': ['doc1'],
            'metadatas': [{'name': 'doc1.pdf', 'type': 'pdf', 'size': 1024, 'uploadedAt': '2023-01-01'}]
        }
        
        chroma_client = ChromaClient(embedding_client=mock_embedding_client, path=tempfile.mkdtemp())
        
        # Test getting a specific document
        document = chroma_client.get_document('doc1')
        
        # Verify that the get method was called with correct ID
        assert mock_documents_collection.get.called
        assert document is not None
        assert document['name'] == 'doc1.pdf'


def test_get_document_by_name():
    mock_embedding_client = Mock(spec=EmbeddingClient)
    
    with patch('chromadb.PersistentClient') as mock_persistent_client:
        mock_client_instance = Mock()
        mock_persistent_client.return_value = mock_client_instance
        
        mock_collection = Mock()
        mock_documents_collection = Mock()
        mock_client_instance.get_or_create_collection.side_effect = [mock_collection, mock_documents_collection]
        
        # Mock the get method to return test data filtered by name
        mock_documents_collection.get.return_value = {
            'ids': ['doc1'],
            'metadatas': [{'name': 'specific_doc.pdf', 'type': 'pdf', 'size': 1024, 'uploadedAt': '2023-01-01'}]
        }
        
        chroma_client = ChromaClient(embedding_client=mock_embedding_client, path=tempfile.mkdtemp())
        
        # Test getting a document by name
        document = chroma_client.get_document_by_name('specific_doc.pdf')
        
        # Verify that the get method was called with correct filter
        assert mock_documents_collection.get.called
        call_args = mock_documents_collection.get.call_args
        assert call_args[1].get('where') == {"name": "specific_doc.pdf"}
        assert document is not None
        assert document['name'] == 'specific_doc.pdf'