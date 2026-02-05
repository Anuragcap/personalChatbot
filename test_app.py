import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import app
import tempfile

class Token:
    def __init__(self, token): 
        self.token = token

def test_api_requires_token():
    """Test that API mode requires authentication"""
    hf_token = os.environ.get("HF_TOKEN")
    assert hf_token, "HF_TOKEN not set in environment"

    gen = app.respond(
        message="Hi",
        history=[],
        system_message="test",
        max_tokens=8,
        temperature=0.2,
        top_p=0.9,
        hf_token=Token(hf_token),
        use_local_model=False,
        uploaded_file=None,
    )
    first = next(gen)
    assert "please log in" not in first.lower()
    assert isinstance(first, str)
    assert len(first) > 0

def test_file_context_extraction():
    """Test that file content is properly extracted"""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
        f.write("This is test content.")
        temp_file_path = f.name
    
    try:
        class MockFile:
            def __init__(self, path):
                self.name = path
        
        mock_file = MockFile(temp_file_path)
        content = app.extract_text_from_file(mock_file)
        
        assert "This is test content." in content
        assert "[Context from file:" in content
    
    finally:
        os.unlink(temp_file_path)

def test_file_context_none():
    """Test that function handles None file gracefully"""
    content = app.extract_text_from_file(None)
    assert content == ""
