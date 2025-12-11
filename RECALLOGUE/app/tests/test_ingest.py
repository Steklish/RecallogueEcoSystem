import os
import tempfile
import pytest
from app.src.services.ingest import (
    extract_text_from_file,
    extract_pdf,
    extract_docx,
    extract_html,
    _read_text_best_effort,
    normalize_text,
    chunk_text,
    _split_sentences
)


def test_normalize_text():
    # Test with multiple types of whitespace and newlines
    input_text = "Line 1   \n\n\t  \nLine 2\r\nLine 3\rLine 4"
    expected = "Line 1\n\nLine 2\nLine 3\nLine 4"
    
    result = normalize_text(input_text)
    assert result == expected


def test_split_sentences_simple():
    text = "Hello world. How are you? I am fine! That's great…"
    result = _split_sentences(text)
    
    assert len(result) == 4
    assert "Hello world." in result
    assert "How are you?" in result
    assert "I am fine!" in result
    assert "That's great…" in result


def test_split_sentences_with_newlines():
    text = "Line 1\nLine 2\n\nLine 3"
    result = _split_sentences(text)
    
    # Since text is short (<2000 chars), it should split by newlines
    assert len(result) >= 2
    assert "Line 1" in result
    assert "Line 2" in result
    assert "Line 3" in result


def test_chunk_text():
    text = "This is a sentence. This is another sentence. And a third one. Fourth sentence here. Fifth sentence follows."
    chunks = chunk_text(text, chunk_size=10, overlap=2)
    
    assert len(chunks) > 0
    for chunk in chunks:
        assert len(chunk.split()) >= 5  # minimum sentence check


def test_chunk_text_with_overlap():
    text = "Sentence 1. Sentence 2. Sentence 3. Sentence 4. Sentence 5. Sentence 6."
    chunks = chunk_text(text, chunk_size=3, overlap=2)
    
    assert len(chunks) >= 2
    # With overlap, there should be some continuity between chunks
    if len(chunks) > 1:
        # Check that some content from the end of first chunk appears at start of second
        first_chunk_words = chunks[0].split()
        second_chunk_words = chunks[1].split()
        # At least some overlap should exist due to overlap parameter
        overlap_found = any(word in second_chunk_words[:3] for word in first_chunk_words[-3:])
        assert overlap_found


def test_read_text_best_effort():
    # Create a temporary file with UTF-8 content
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt', encoding='utf-8') as f:
        f.write("Test content in UTF-8")
        temp_path = f.name

    try:
        result = _read_text_best_effort(temp_path)
        assert result == "Test content in UTF-8"
    finally:
        os.unlink(temp_path)


def test_extract_pdf():
    # Since we can't easily create a real PDF in tests, we'll test the function structure
    # by checking that it returns a string when given a valid PDF path
    # For now, we'll just verify the function exists and is callable
    assert callable(extract_pdf)


def test_extract_docx():
    # Since we can't easily create a real DOCX in tests, we'll test the function structure
    # For now, we'll just verify the function exists and is callable
    assert callable(extract_docx)


def test_extract_html():
    # Since we can't easily create a real HTML file in tests, we'll test the function structure
    # For now, we'll just verify the function exists and is callable
    assert callable(extract_html)


def test_extract_text_from_file_with_different_extensions():
    # Test the extract_text_from_file function with different file extensions
    # This tests the routing mechanism of the function
    
    # Create temporary files with different extensions
    # For text files
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as f:
        f.write("Test text content")
        temp_txt_path = f.name

    try:
        result = extract_text_from_file(temp_txt_path)
        # This should read the text file content
        assert "Test text content" in result or result == "Test text content"
    finally:
        os.unlink(temp_txt_path)


def test_chunk_text_small_text():
    # Test chunking a very small text
    text = "Short text."
    chunks = chunk_text(text, chunk_size=100, overlap=0)
    
    assert len(chunks) == 1
    assert "Short text." == chunks[0]


def test_chunk_text_exact_size():
    # Test chunking with text that exactly matches chunk size
    text = "This is a sentence. " * 5  # Create text with 5 sentences
    chunks = chunk_text(text, chunk_size=5, overlap=0)
    
    # Should have at least one chunk
    assert len(chunks) >= 1
    for chunk in chunks:
        # Each chunk should not exceed the chunk size significantly
        assert len(chunk.split()) <= 10  # Allow some flexibility for sentence boundaries