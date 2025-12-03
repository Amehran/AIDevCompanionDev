import pytest
from unittest.mock import patch, MagicMock
import sys
import os

# Import the module to test
# Since tools/search_memory.py is a script, we might need to import it carefully
# or refactor it to be importable. It has a 'if __name__ == "__main__":' block, so it is importable.
# Mock dependencies BEFORE importing the module
sys.modules["pinecone"] = MagicMock()
sys.modules["langchain_google_genai"] = MagicMock()
sys.modules["langchain_community"] = MagicMock()

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from tools import search_memory

class TestSearchMemory:
    @patch.dict(os.environ, {}, clear=True)
    def test_search_no_api_key(self, capsys):
        """Test that search handles missing API key gracefully."""
        # Ensure PINECONE_API_KEY is NOT set
        search_memory.search("test query")
        
        captured = capsys.readouterr()
        assert "Error: PINECONE_API_KEY environment variable not set." in captured.out

    @patch.dict(os.environ, {"PINECONE_API_KEY": "fake-key", "GOOGLE_API_KEY": "fake-google-key"})
    def test_search_success(self, capsys):
        """Test successful search flow with mocked dependencies."""
        # Get the mocks that were injected
        mock_pinecone_module = sys.modules["pinecone"]
        mock_langchain_module = sys.modules["langchain_google_genai"]
        
        # Configure Pinecone mock
        mock_pinecone_cls = mock_pinecone_module.Pinecone
        mock_index = MagicMock()
        mock_pinecone_instance = mock_pinecone_cls.return_value
        mock_pinecone_instance.Index.return_value = mock_index
        
        # Configure Embeddings mock
        mock_embeddings_cls = mock_langchain_module.GoogleGenerativeAIEmbeddings
        mock_embeddings_instance = mock_embeddings_cls.return_value
        mock_embeddings_instance.embed_query.return_value = [0.1, 0.2, 0.3]
        
        # Mock Query Results
        mock_index.query.return_value = {
            'matches': [
                {
                    'score': 0.95,
                    'metadata': {'source': 'test_file.py', 'text': 'def test_func(): pass'}
                }
            ]
        }
        
        # Run search
        search_memory.search("test query")
        
        # Verify interactions
        mock_pinecone_cls.assert_called_with(api_key="fake-key")
        mock_index.query.assert_called()
        
        # Verify output
        captured = capsys.readouterr()
        assert "Search Results for: 'test query'" in captured.out
        assert "Source: test_file.py" in captured.out
