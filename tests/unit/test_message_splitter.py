"""
Tests for message splitting functionality.
"""

import pytest

from aibotto.utils.helpers import process_file_content
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

    def test_split_message_for_sending_file_object(self):
        """Test handling of File objects in message splitting."""
        # Create a mock File object with binary data
        class MockFile:
            def __init__(self, file_name, file_data):
                self.file_name = file_name
                self.file_data = file_data

        # Create binary data with UTF-8 encoded box drawing characters
        binary_content = b'docker-compose.yml\n\xe2\x94\x9c\xe2\x94\x80\xe2\x94\x80 bot (main service)\n\xe2\x94\x9c\xe2\x94\x80\xe2\x94\x80 scheduler (cron-based summary service)\n\xe2\x94\x94\xe2\x94\x80\xe2\x94\x80 shared database volume'
        file_obj = MockFile('docker-compose.yml.txt', binary_content)

        # Split the file object
        chunks = MessageSplitter.split_message_for_sending(file_obj)

        # Should return a single chunk for files
        assert len(chunks) == 1
        assert "📄 **File: docker-compose.yml.txt**" in chunks[0]
        assert "docker-compose.yml" in chunks[0]
        assert "bot (main service)" in chunks[0]
        assert "scheduler (cron-based summary service)" in chunks[0]
        # Should have properly decoded the box drawing characters
        assert "├──" in chunks[0]  # Box drawing character
        assert "─" in chunks[0]  # Box drawing character
        assert "└──" in chunks[0]  # Box drawing character

    def test_split_message_for_sending_binary_file(self):
        """Test handling of binary file objects."""
        # Create a mock File object with binary data that can't be decoded as UTF-8
        class MockFile:
            def __init__(self, file_name, file_data):
                self.file_name = file_name
                self.file_data = file_data

        # Create binary data that's not valid UTF-8 (PNG header)
        binary_content = b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x02\x00\x00\x00\x90wS\xde'
        file_obj = MockFile('image.png', binary_content)

        # Split the file object
        chunks = MessageSplitter.split_message_for_sending(file_obj)

        # Should return a single chunk for files
        assert len(chunks) == 1
        assert "📄 **File: image.png**" in chunks[0]
        assert "⚠️ Binary file content" in chunks[0]
        assert "base64" in chunks[0]
        # Should show base64 encoded content (first 2000 bytes)
        assert len(chunks[0]) > 100  # Should have substantial content

    def test_process_file_content_function(self):
        """Test the dedicated file processing function."""
        # Create a mock File object with UTF-8 encoded content
        class MockFile:
            def __init__(self, file_name, file_data):
                self.file_name = file_name
                self.file_data = file_data

        # Test with UTF-8 encoded content
        binary_content = b'docker-compose.yml\n\xe2\x94\x9c\xe2\x94\x80\xe2\x94\x80 bot (main service)'
        file_obj = MockFile('docker-compose.yml.txt', binary_content)

        result = process_file_content(file_obj)

        # Should return formatted file content
        assert "📄 **File: docker-compose.yml.txt**" in result
        assert "docker-compose.yml" in result
        assert "bot (main service)" in result
        assert "├──" in result  # Should have properly decoded box drawing characters
        assert "```" in result  # Should be formatted as code block

    def test_process_file_content_binary(self):
        """Test the file processing function with binary content."""
        # Create a mock File object with binary content
        class MockFile:
            def __init__(self, file_name, file_data):
                self.file_name = file_name
                self.file_data = file_data

        # Test with binary content that can't be decoded as UTF-8
        binary_content = b'\x89PNG\r\n\x1a\n binary data here'
        file_obj = MockFile('image.png', binary_content)

        result = process_file_content(file_obj)

        # Should handle binary content gracefully
        assert "📄 **File: image.png**" in result
        assert "⚠️ Binary file content" in result
        assert "base64" in result

    def test_process_file_content_regular_object(self):
        """Test that the function handles non-file objects gracefully."""
        # Test with a regular string
        result = process_file_content("regular text")
        assert result == "regular text"

        # Test with None
        result = process_file_content(None)
        assert result == "None"
