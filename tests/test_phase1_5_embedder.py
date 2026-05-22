import pytest
import numpy as np
from unittest.mock import patch, MagicMock
from src.ingest.subphases.phase_1_5_embedder.embedder import Embedder

@patch("src.ingest.subphases.phase_1_5_embedder.embedder.SentenceTransformer")
def test_embedder_logic(mock_st_class):
    # Setup mock instance and encode method
    mock_st_instance = MagicMock()
    # Dummy embeddings for 2 chunks, dim=384 (using a smaller dim here just for array shape check)
    dummy_embeddings = np.array([[0.1] * 384, [0.2] * 384])
    mock_st_instance.encode.return_value = dummy_embeddings
    mock_st_class.return_value = mock_st_instance

    # Initialize embedder
    embedder = Embedder()
    
    # Dummy chunks from Phase 1.4
    chunks = [
        {"chunk_id": "c1", "scheme_name": "Scheme A", "text": "Hello world"},
        {"chunk_id": "c2", "scheme_name": "Scheme B", "text": "Foo bar"}
    ]
    
    result = embedder.embed(chunks)
    
    # Assertions
    assert "embeddings" in result
    assert "chunks" in result
    assert len(result["chunks"]) == 2
    assert result["embeddings"].shape == (2, 384)
    
    # Verify encode was called with correct inputs (prepended scheme name)
    args, kwargs = mock_st_instance.encode.call_args
    texts_passed = args[0]
    
    assert len(texts_passed) == 2
    assert texts_passed[0] == "Scheme A\n\nHello world"
    assert texts_passed[1] == "Scheme B\n\nFoo bar"
    assert kwargs.get("convert_to_numpy") is True
