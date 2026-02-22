"""
Tests for message splitting functionality.
"""

import pytest

from aibotto.utils.message_splitter import MessageSplitter


class TestMessageSplitter:
    """Test cases for MessageSplitter."""

    def test_short_message_not_split(self):
        """Test that short messages are not split."""
        message = "This is a short message"
        chunks = MessageSplitter.split_message_for_rate_limiting(message)
        assert len(chunks) == 1
        assert chunks[0] == message

    def test_long_message_split_by_paragraph(self):
        """Test that long messages are split by paragraphs."""
        # Create a message that's longer than 4095 characters
        paragraph1 = "This is paragraph 1. " * 100
        paragraph2 = "This is paragraph 2. " * 100
        paragraph3 = "This is paragraph 3. " * 100
        message = f"{paragraph1}\n\n{paragraph2}\n\n{paragraph3}"

        chunks = MessageSplitter.split_message_for_rate_limiting(message)

        # Should be split into 3 chunks (one per paragraph)
        assert len(chunks) == 3
        assert paragraph1 in chunks[0]
        assert paragraph2 in chunks[1]
        assert paragraph3 in chunks[2]

    def test_very_long_paragraph_split_by_sentence(self):
        """Test that very long paragraphs are split by sentences."""
        # Create a very long paragraph with multiple sentences
        sentence = "This is a sentence. " * 50
        paragraph = sentence * 10  # Make it very long
        message = paragraph

        chunks = MessageSplitter.split_message_for_rate_limiting(message)

        # Should be split into multiple chunks
        assert len(chunks) > 1
        # Each chunk should end with proper sentence punctuation
        for chunk in chunks[:-1]:  # All but the last chunk
            assert chunk.endswith('.') or chunk.endswith('!') or chunk.endswith('?')

    def test_very_long_sentence_split_by_word(self):
        """Test that very long sentences are split by words."""
        # Create a very long sentence with many words
        word = "supercalifragilisticexpialidocious"
        sentence = " ".join([word] * 200)  # Make it very long
        message = sentence

        chunks = MessageSplitter.split_message_for_rate_limiting(message)

        # Should be split into multiple chunks
        assert len(chunks) > 1
        # Each chunk should contain complete words
        for i, chunk in enumerate(chunks):
            words_in_chunk = chunk.split()
            # Each chunk should end with a complete word
            assert words_in_chunk[-1] == word

    def test_continuation_markers_added(self):
        """Test that continuation markers are added correctly."""
        message = "Short. " * 1000  # Make it long enough to split
        chunks = MessageSplitter.split_message_for_rate_limiting(message)
        marked_chunks = MessageSplitter.add_continuation_markers(chunks)

        # Should have the same number of chunks
        assert len(marked_chunks) == len(chunks)

        # First chunk should have header
        assert "📄 **Message (Part 1 of" in marked_chunks[0]
        assert marked_chunks[0].startswith("📄 **Message (Part 1 of")

        # Middle chunks should have continuation markers
        if len(marked_chunks) > 2:
            assert "📄 **Continuation (Part" in marked_chunks[1]

        # Last chunk should have footer
        assert "✅ **End of message**" in marked_chunks[-1]
        assert marked_chunks[-1].endswith("✅ **End of message**")

    def test_single_chunk_no_markers(self):
        """Test that single chunks don't get continuation markers."""
        message = "This is a single chunk message"
        chunks = MessageSplitter.split_message_for_rate_limiting(message)
        marked_chunks = MessageSplitter.add_continuation_markers(chunks)

        # Should be unchanged
        assert len(marked_chunks) == 1
        assert marked_chunks[0] == message

    def test_send_chunks_with_rate_limit_async(self):
        """Test that send_chunks_with_rate_limit works asynchronously."""
        import asyncio

        async def mock_send_func(text, parse_mode=None):
            """Mock send function that just logs the text."""
            print(f"Sending: {text[:50]}...")
            await asyncio.sleep(0.1)  # Simulate network delay

        message = "Test. " * 500  # Make it long enough to split
        chunks = MessageSplitter.split_message_for_rate_limiting(message)

        # This should not raise an exception
        try:
            asyncio.run(MessageSplitter.send_chunks_with_rate_limit(
                chunks, mock_send_func, delay_between_chunks=0.1
            ))
        except Exception as e:
            pytest.fail(f"send_chunks_with_rate_limit raised an exception: {e}")

    def test_edge_case_empty_message(self):
        """Test handling of empty messages."""
        chunks = MessageSplitter.split_message_for_rate_limiting("")
        assert len(chunks) == 1
        assert chunks[0] == ""

    def test_edge_case_exact_boundary(self):
        """Test handling of messages exactly at the boundary."""
        # Create a message that's exactly 4095 characters
        message = "A" * 4095
        chunks = MessageSplitter.split_message_for_rate_limiting(message)

        # Should not be split
        assert len(chunks) == 1
        assert len(chunks[0]) == 4095

    def test_edge_case_just_over_boundary(self):
        """Test handling of messages just over the boundary."""
        # Create a message that's just over 4095 characters
        message = "A" * 4096
        chunks = MessageSplitter.split_message_for_rate_limiting(message)

        # Should be split into 2 chunks
        assert len(chunks) == 2
        assert len(chunks[0]) <= 4095
        assert len(chunks[1]) <= 4095

    def test_split_message_for_sending_escaping_safety(self):
        """Test that the new splitting method accounts for MarkdownV2 escaping."""
        # Create a message with many MarkdownV2 special characters that will expand
        special_chars = r'_*[]()~`>#+-=|{}.!'
        message = special_chars * 200  # This will expand significantly when escaped
        
        # Use the new method that accounts for escaping
        chunks = MessageSplitter.split_message_for_sending(message)
        
        # All chunks should be safe (won't exceed Telegram's limit after escaping)
        for chunk in chunks:
            # Estimate worst-case expansion (each char could become 2 chars)
            estimated_length = len(chunk) * 2
            assert estimated_length <= 4095, f"Chunk too long after escaping: {estimated_length}"
        
        # Should be split into multiple chunks due to escaping expansion
        assert len(chunks) > 1

    def test_split_message_for_sending_with_markers(self):
        """Test splitting with continuation markers enabled."""
        # Create a long message that will definitely need splitting
        message = "This is a sentence. " * 1000
        
        # Split with marker space reservation
        chunks = MessageSplitter.split_message_for_sending(
            message, reserve_marker_space=True
        )
        
        # Should account for the additional space needed by markers
        assert len(chunks) >= 1
        
        # Verify that even with markers, chunks won't exceed limits
        for chunk in chunks:
            estimated_length = len(chunk) * 2  # Account for escaping
            assert estimated_length <= 4095, f"Chunk too long with markers: {estimated_length}"
