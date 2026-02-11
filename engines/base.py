"""Base engine interface.

All engine levels implement this interface for consistent behavior.
"""

from abc import ABC, abstractmethod


class BaseEngine(ABC):
    """Base class for all engine levels."""

    def __init__(self):
        """Initialize base engine state."""
        self._conversation_id: str | None = None
        self._sequence: int = 0

    def set_conversation_id(self, conversation_id: str) -> None:
        """Set the conversation ID for grouping queries.

        Called once at the start of a chat session.

        Args:
            conversation_id: UUID from EventLogger.start_conversation()
        """
        self._conversation_id = conversation_id
        self._sequence = 0  # Reset sequence for new conversation

    @abstractmethod
    async def run(self, user_message: str, message_history: list) -> tuple[str, list]:
        """Process a user message and return a response.

        Args:
            user_message: The user's input text
            message_history: Previous messages in the conversation

        Returns:
            Tuple of (response_text, updated_message_history)
        """
        ...

    @abstractmethod
    def get_level(self) -> int:
        """Return the engine level number (1-4)."""
        ...

    @abstractmethod
    def get_description(self) -> str:
        """Return a human-readable description of this engine level."""
        ...
