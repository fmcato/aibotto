"""Test that the Brotli header fix resolves 400 errors with brotli-compressed responses."""

import pytest
from aibotto.tools.web_fetch import WebFetchTool


def test_brotli_encoding_not_requested():
    """Test that the fetch request does not request Brotli encoding."""
    tool = WebFetchTool()
    
    # Get headers that would be sent
    headers = tool._get_headers()
    
    # Verify that Accept-Encoding does NOT include "br"
    accept_encoding = headers.get("Accept-Encoding", "")
    assert "br" not in accept_encoding, f"Brotli (br) should not be in Accept-Encoding header: {accept_encoding}"
    
    # Verify that gzip and deflate are still present
    assert "gzip" in accept_encoding, f"gzip should be in Accept-Encoding header: {accept_encoding}"
    assert "deflate" in accept_encoding, f"deflate should be in Accept-Encoding header: {accept_encoding}"


def test_headers_structure_correct():
    """Test that overall header structure is maintained."""
    tool = WebFetchTool()
    headers = tool._get_headers()
    
    # Verify key headers are present
    assert "Accept" in headers
    assert "Accept-Language" in headers
    assert "User-Agent" in headers
    assert headers["User-Agent"].startswith("Mozilla/5.0")
    
    # Verify specific encoding header format
    encodings = headers["Accept-Encoding"].split(", ")
    assert encodings == ["gzip", "deflate"], f"Expected ['gzip', 'deflate'], got {encodings}"
