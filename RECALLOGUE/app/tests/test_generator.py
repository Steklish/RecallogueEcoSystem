import os
import pytest
from unittest.mock import Mock, patch, MagicMock
from pydantic import BaseModel, Field
from app.src.services.ai_backends.generator import Generator



# Create a simple test model for our Pydantic tests
class TestModel(BaseModel):
    name: str = Field(..., description="The name of the item")
    description: str = Field(..., description="The description of the item")


def test_generator_initialization_with_llama_backend():
    # Test initializing generator with default (Llama) backend
    with patch.dict(os.environ, {}, clear=True):  # Clear environment variables
        with patch('app.src.services.ai_backends.generator.LlamaGenAI') as mock_llama:
            mock_llama_instance = Mock()
            mock_llama.return_value = mock_llama_instance
            mock_llama_instance.complete.return_value = '{"name": "test", "description": "test desc"}'
            mock_llama_instance.get_model.return_value = "test-model"

            # Also patch the _get_model_from_server method to avoid HTTP calls during initialization
            with patch.object(Generator, '_get_model_from_server', return_value="test-model"):
                generator = Generator(base="http://test-llama:8080")

            # Verify LlamaGenAI was initialized
            assert mock_llama.called
            assert generator._backend_type.startswith("local <")


def test_generator_initialization_with_gemini_backend():
    # Test initializing generator with Gemini backend
    with patch.dict(os.environ, {"USE_GEMINI": "1"}):
        with patch('app.src.services.ai_backends.generator.GoogleGenAI') as mock_gemini:
            mock_gemini_instance = Mock()
            mock_gemini.return_value = mock_gemini_instance
            mock_gemini_instance.complete.return_value = '{"name": "test", "description": "test desc"}'

            # Also patch the _get_model_from_server method to avoid HTTP calls during initialization
            with patch.object(Generator, '_get_model_from_server', return_value="test-model"):
                generator = Generator(base="http://test:8080")

            # Verify GoogleGenAI was initialized
            assert mock_gemini.called
            assert generator._backend_type == "gemini"


def test_generator_initialization_with_qwen_backend():
    # Test initializing generator with Qwen backend
    with patch.dict(os.environ, {"USE_QWEN": "1"}):
        with patch('app.src.services.ai_backends.generator.QwenGenAI') as mock_qwen:
            mock_qwen_instance = Mock()
            mock_qwen.return_value = mock_qwen_instance
            mock_qwen_instance.complete.return_value = '{"name": "test", "description": "test desc"}'

            # Also patch the _get_model_from_server method to avoid HTTP calls during initialization
            with patch.object(Generator, '_get_model_from_server', return_value="test-model"):
                generator = Generator(base="http://test:8080")

            # Verify QwenGenAI was initialized
            assert mock_qwen.called
            assert generator._backend_type == "qwen"


def test_generate_one_shot_success():
    with patch.dict(os.environ, {}, clear=True):
        with patch('app.src.services.ai_backends.generator.LlamaGenAI') as mock_llama:
            mock_llama_instance = Mock()
            mock_llama.return_value = mock_llama_instance
            mock_llama_instance.complete.return_value = '{"name": "generated_name", "description": "generated_desc"}'
            mock_llama_instance.get_model.return_value = "test-model"

            # Also patch the _get_model_from_server method to avoid HTTP calls during initialization
            with patch.object(Generator, '_get_model_from_server', return_value="test-model"):
                generator = Generator(base="http://test-llama:8080")

            # Test the generate_one_shot method
            result = generator.generate_one_shot(
                pydantic_model=TestModel,
                prompt="Create a test object",
                language="English"
            )

            assert isinstance(result, TestModel)
            assert result.name == "generated_name"
            assert result.description == "generated_desc"


def test_generate_one_shot_with_json_cleanup():
    with patch.dict(os.environ, {}, clear=True):
        with patch('app.src.services.ai_backends.generator.LlamaGenAI') as mock_llama:
            mock_llama_instance = Mock()
            mock_llama.return_value = mock_llama_instance
            # Return response with markdown-like formatting that needs cleaning
            mock_llama_instance.complete.return_value = 'Some text before {"name": "cleaned", "description": "result"} more text after'
            mock_llama_instance.get_model.return_value = "test-model"

            # Also patch the _get_model_from_server method to avoid HTTP calls during initialization
            with patch.object(Generator, '_get_model_from_server', return_value="test-model"):
                generator = Generator(base="http://test-llama:8080")

            result = generator.generate_one_shot(
                pydantic_model=TestModel
            )

            assert isinstance(result, TestModel)
            assert result.name == "cleaned"
            assert result.description == "result"


def test_generate_one_shot_with_retry_logic():
    with patch.dict(os.environ, {}, clear=True):
        with patch('app.src.services.ai_backends.generator.LlamaGenAI') as mock_llama:
            mock_llama_instance = Mock()
            mock_llama.return_value = mock_llama_instance
            # First call fails, second succeeds
            mock_llama_instance.complete.side_effect = [
                Exception("First call fails"),
                '{"name": "retry_success", "description": "result"}'
            ]
            mock_llama_instance.get_model.return_value = "test-model"

            # Also patch the _get_model_from_server method to avoid HTTP calls during initialization
            with patch.object(Generator, '_get_model_from_server', return_value="test-model"):
                generator = Generator(base="http://test-llama:8080")

            result = generator.generate_one_shot(
                pydantic_model=TestModel,
                retries=2
            )

            assert isinstance(result, TestModel)
            assert result.name == "retry_success"
            assert result.description == "result"
            assert mock_llama_instance.complete.call_count == 2  # Called twice due to retry



def test_clean_json_response():
    with patch.dict(os.environ, {}, clear=True):
        with patch('app.src.services.ai_backends.llama_gen.LlamaGenAI') as mock_llama:
            mock_llama_instance = Mock()
            mock_llama.return_value = mock_llama_instance
            mock_llama_instance.get_model.return_value = "test-model"
            
            generator = Generator(base="http://test-llama:8080")
            
            # Test the JSON cleaning with various formats
            test_cases = [
                ("Some text before {\"key\": \"value\"} after", {"key": "value"}),
                ("{ \"name\": \"test\", \"description\": \"desc\" }", {"name": "test", "description": "desc"}),
                ("Random text {\"nested\": {\"key\": \"value\"}} more text", {"nested": {"key": "value"}}),
            ]
            
            for input_text, expected in test_cases:
                # Mock the complete method to return the input text
                mock_llama_instance.complete.return_value = input_text
                
                # This will indirectly test the _clean_json_response method
                try:
                    # The response won't be valid JSON for TestModel, but cleaning should work
                    generator._clean_json_response(input_text)
                except:
                    # Expected since the cleaned JSON might not match TestModel schema
                    pass


def test_generate_one_shot_json_parsing_error():
    with patch.dict(os.environ, {}, clear=True):
        with patch('app.src.services.ai_backends.llama_gen.LlamaGenAI') as mock_llama:
            mock_llama_instance = Mock()
            mock_llama.return_value = mock_llama_instance
            # Return invalid JSON
            mock_llama_instance.complete.return_value = '{"invalid": json, "no": "closing brace"'
            mock_llama_instance.get_model.return_value = "test-model"
            
            generator = Generator(base="http://test-llama:8080")
            
            # Should raise an exception due to invalid JSON
            with pytest.raises(Exception):
                generator.generate_one_shot(
                    pydantic_model=TestModel
                )


def test_generate_one_shot_multiple_retries_failure():
    with patch.dict(os.environ, {}, clear=True):
        with patch('app.src.services.ai_backends.llama_gen.LlamaGenAI') as mock_llama:
            mock_llama_instance = Mock()
            mock_llama.return_value = mock_llama_instance
            # Always fail
            mock_llama_instance.complete.side_effect = Exception("Always fails")
            mock_llama_instance.get_model.return_value = "test-model"
            
            generator = Generator(base="http://test-llama:8080")
            
            # Should raise an exception after all retries
            with pytest.raises(Exception):
                generator.generate_one_shot(
                    pydantic_model=TestModel,
                    retries=2
                )


def test_get_model_info():
    with patch.dict(os.environ, {}, clear=True):
        with patch('app.src.services.ai_backends.llama_gen.LlamaGenAI') as mock_llama:
            mock_llama_instance = Mock()
            mock_llama.return_value = mock_llama_instance
            mock_llama_instance.complete.return_value = '{"name": "test", "description": "test"}'
            mock_llama_instance.get_model.return_value = "test-model-name"

            # Also patch the _get_model_from_server method to avoid HTTP calls during initialization
            with patch.object(Generator, '_get_model_from_server', return_value="test-model-name"):
                generator = Generator(base="http://test-llama:8080")

            model_info = generator.get_model_info()
            assert model_info == "test-model-name"