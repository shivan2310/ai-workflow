from typing import List, Dict, Any
from app.schemas.tools import DraftEmailInput, DraftEmailOutput


def draft_email(input_data: DraftEmailInput) -> DraftEmailOutput:
    """
    Generates a professional invitation email draft based on verified details.
    Missing details are explicitly flagged and marked with placeholders.
    Never sends emails.
    """
    details: Dict[str, Any] = input_data.known_event_details or {}
    missing: List[str] = []

    # Check for essential event parameters
    expected_fields = {
        "date": "Date & Time",
        "venue": "Venue / Room Location",
        "speaker": "Speaker / Facilitator",
        "registration_deadline": "Registration Deadline",
    }

    placeholders: Dict[str, str] = {}
    for key, label in expected_fields.items():
        if key in details and details[key]:
            placeholders[key] = str(details[key])
        else:
            missing.append(label)
            placeholders[key] = f"[{label}: To be announced]"

    # Construct formal invitation email
    topic = details.get("topic", input_data.purpose)
    subject = f"Invitation: {topic} — Workshop Details & RSVP"

    salutation = "Dear Students & Participants,"
    if "faculty" in input_data.intended_audience.lower():
        salutation = "Dear Faculty Members & Attendees,"

    body = (
        f"{salutation}\n\n"
        f"We are excited to invite you to an upcoming workshop focused on {topic}.\n\n"
        f"Event Overview:\n"
        f"• Purpose: {input_data.purpose}\n"
        f"• Target Audience: {input_data.intended_audience}\n"
        f"• Date: {placeholders['date']}\n"
        f"• Location: {placeholders['venue']}\n"
        f"• Keynote / Instructor: {placeholders['speaker']}\n"
        f"• Registration Closes: {placeholders['registration_deadline']}\n\n"
        f"Please reserve your seat at your earliest convenience.\n\n"
        f"Best regards,\n"
        f"AutoPilot AI Workshop Coordination Team\n"
        f"(This is an automated preparation draft. No emails have been dispatched.)"
    )

    return DraftEmailOutput(
        subject=subject,
        body=body,
        missing_information=missing,
        is_draft_only=True,
    )
