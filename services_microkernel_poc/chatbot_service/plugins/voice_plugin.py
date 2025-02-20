async def process_voice_input(user_input: str) -> str:
    """Simulates processing voice input."""
    # In a real implementation, you'd call a Speech-to-Text API here.
    # For the POC, we'll just check for a specific phrase.
    if "voice input" in user_input.lower():
        return "I am experiencing a headache and fatigue."
    return None


def is_voice_input(user_input: str) -> bool:
    """Checks if the input is considered a voice input (for the POC)."""
    return "voice input" in user_input.lower()
