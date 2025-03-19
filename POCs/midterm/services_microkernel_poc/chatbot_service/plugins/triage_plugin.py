def apply_triage_rules(user_input: str, hf_response: str) -> str:
    # VERY basic example.  This would be much more sophisticated in reality.
    combined_input = user_input.lower() + " " + hf_response.lower()

    if any(
        keyword in combined_input for keyword in ["emergency", "chest pain", "bleeding"]
    ):
        return "Please seek immediate medical attention or call emergency services."
    elif any(
        keyword in combined_input for keyword in ["fever", "cough", "sore throat"]
    ):
        return "You may have a common cold or flu.  Consider scheduling an appointment with a doctor."
    else:
        return hf_response  # Return the original HF response if no rules match
