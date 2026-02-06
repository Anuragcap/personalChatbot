import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import app
import tempfile

class Token:
    def __init__(self, token):
        self.token = token

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

def test_respond_function_exists():
    """Test that respond function exists and is callable"""
    import inspect
    
    # Check function exists
    assert hasattr(app, 'respond')
    
    # Check it's callable
    assert callable(app.respond)
    
    # Check parameter count
    sig = inspect.signature(app.respond)
    params = list(sig.parameters.keys())
    
    # Should have at least message and history parameters
    assert 'message' in params
    assert 'history' in params
    assert 'file_upload' in params
    assert len(params) >= 2

def test_chatinterface_demo_exists():
    """Test that Gradio demo interface exists"""
    assert hasattr(app, 'demo')
    assert app.demo is not None
    
def test_respond_returns_generator():
    """Test that respond returns a generator"""
    hf_token = os.environ.get("HF_TOKEN")
    
    # Create a mock token or None if not available
    token_obj = Token(hf_token) if hf_token else None
    
    gen = app.respond(
        message="Test message",
        history=[],
        system_message="You are a helpful assistant",
        max_tokens=10,
        temperature=0.7,
        top_p=0.9,
        file_upload=None,
        hf_token=token_obj,
        use_local_model=False,
    )
    
    # Should return a generator
    assert hasattr(gen, '__next__') or hasattr(gen, '__iter__')
    
    # Try to get first response
    try:
        first = next(gen)
        assert isinstance(first, str)
        assert len(first) > 0
        print(f"✓ Response received: {first[:50]}...")
    except StopIteration:
        # Generator might be empty, that's okay for test
        print("✓ Generator created successfully")
    except Exception as e:
        # API errors are expected in CI without proper auth
        error_str = str(e)
        if "log in" in error_str.lower() or "token" in error_str.lower():
            print(f"✓ Expected auth warning in CI: {error_str[:50]}")
        else:
            raise

def test_api_requires_token():
    """Test API mode with valid token"""
    hf_token = os.environ.get("HF_TOKEN")
    
    if not hf_token:
        print("⚠️ Skipping test_api_requires_token - HF_TOKEN not set")
        return
    
    gen = app.respond(
        message="Hi",
        history=[],
        system_message="test",
        max_tokens=8,
        temperature=0.2,
        top_p=0.9,
        file_upload=None,
        hf_token=Token(hf_token),
        use_local_model=False,
    )
    first = next(gen)
    assert "please log in" not in first.lower()  # shouldn't get warning
    assert isinstance(first, str)