"""Base engine interface.

All engine levels implement this interface for consistent behavior.
"""

from abc import ABC, abstractmethod


class BaseEngine(ABC):
    """Base class for all engine levels."""

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
        """Return the engine level number (1-5)."""
        ...

    @abstractmethod
    def get_description(self) -> str:
        """Return a human-readable description of this engine level."""
        ...
