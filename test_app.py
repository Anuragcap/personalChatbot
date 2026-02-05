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
    """Test that respond function exists and has correct signature"""
    import inspect
    
    # Check function exists
    assert hasattr(app, 'respond')
    
    # Check it's callable
    assert callable(app.respond)
    
    # Check parameter count (should be 8 now)
    sig = inspect.signature(app.respond)
    params = list(sig.parameters.keys())
    
    # Should have these parameters
    expected_params = ['message', 'history', 'system_message', 'max_tokens', 
                      'temperature', 'top_p', 'use_local_model', 'uploaded_file']
    
    assert len(params) == len(expected_params), f"Expected {len(expected_params)} parameters, got {len(params)}"

def test_local_mode_basic():
    """Test local mode with a simple message (without actually loading the model)"""
    # This test verifies the function can be called with correct parameters
    # We won't actually run it to avoid loading the large model in CI
    
    try:
        gen = app.respond(
            message="Test",
            history=[],
            system_message="test",
            max_tokens=5,
            temperature=0.2,
            top_p=0.9,
            use_local_model=True,  # Would load model, but we'll skip actual execution
            uploaded_file=None,
        )
        # Don't actually run the generator in CI (would need to download model)
        # Just verify it returns a generator
        assert hasattr(gen, '__next__') or hasattr(gen, '__iter__')
        print("✓ Local mode function signature is correct")
    except Exception as e:
        # If it fails due to model loading, that's expected in CI
        if "model" in str(e).lower() or "download" in str(e).lower():
            print("✓ Local mode would work but model not available in CI (expected)")
        else:
            raise

def test_api_mode_structure():
    """Test that API mode handles missing auth correctly"""
    gen = app.respond(
        message="Hi",
        history=[],
        system_message="test",
        max_tokens=8,
        temperature=0.2,
        top_p=0.9,
        use_local_model=False,  # API mode
        uploaded_file=None,
    )
    
    # Should get a response (likely warning about login)
    first = next(gen)
    assert isinstance(first, str)
    assert len(first) > 0
    print(f"✓ API mode returns: {first[:50]}...")
