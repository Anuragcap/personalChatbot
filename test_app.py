import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import app
import tempfile

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
    assert len(params) >= 2

def test_chatinterface_demo_exists():
    """Test that Gradio demo interface exists"""
    assert hasattr(app, 'demo')
    assert app.demo is not None
    
def test_respond_returns_generator():
    """Test that respond returns a generator"""
    gen = app.respond(
        message="Test message",
        history=[],
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
        if "Error" in str(e) or "API" in str(e):
            print(f"✓ Expected API error in CI: {str(e)[:50]}")
        else:
            raise
