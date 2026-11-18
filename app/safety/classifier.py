"""Safety classification using LLM with structured output, strict timeout, and regex fallback."""

import asyncio
import re
from typing import Literal

from langchain_core.messages import HumanMessage, SystemMessage
from pydantic import BaseModel, Field

from app.config import settings
from app.enums import SafetyVerdict
from app.llm.cache import execute_with_cache
from app.llm.factory import get_chat_model
from app.logging import log_safety_classifier_failure
from app.safety.fallback_regex import is_regex_emergency


class SafetyClassificationOutput(BaseModel):
    """Structured output schema for safety classification."""

    verdict: SafetyVerdict = Field(
        ...,
        description="EMERGENCY if active life-threatening emergency, MEDICAL_ADVICE if seeking diagnosis/prescriptions/dosage, otherwise SAFE.",
    )
    language: Literal["en", "hi", "hinglish"] = Field(
        ...,
        description="The primary language used by the patient: en, hi (Devanagari), or hinglish (Latin-script Hindi).",
    )


SAFETY_SYSTEM_PROMPT = """You are a healthcare safety classifier for residential clinic concierge patients.
Your role is to strictly classify incoming patient messages into one of three verdicts, and detect the language.

VERDICT RULES:
1. EMERGENCY: The message indicates that a person RIGHT NOW has an acute, life-threatening condition (Level-1 sign):
   - Chest pain, severe chest pressure, suspected heart attack
   - Difficulty breathing, shortness of breath, suffocating, choking
   - Unresponsive, unconscious, collapsed, fainted
   - Severe, uncontrollable bleeding
   - Stroke signs: face drooping, arm weakness, slurred speech
   - Active seizure or convulsion
   - Thoughts, threats, or expressions of suicide or self-harm
   Past, resolved, mild, or hypothetical symptoms are NOT emergency.

2. MEDICAL_ADVICE: The message asks the assistant to practise medicine:
   - Requesting a medical diagnosis ("What does this mean?", "Is this serious?")
   - Asking for medication recommendations, prescriptions, or dosages ("What medicine should I take?", "How many mg of paracetamol?")
   - Asking whether to take, change, or stop a prescription drug
   - Asking for clinical interpretation of test results
   NOTE: Simply asking to book a doctor, asking clinic hours, or logging a symptom without asking for treatment is SAFE.

3. SAFE: The message is safe to process:
   - Booking requests ("Book Dr. Khanna tomorrow")
   - Requesting clinic information ("When is the wellness center open?", "Is CBC covered?")
   - Symptom logging ("Log that I have had mild nausea for 2 hours")
   - General queries or small talk ("Hello", "Thank you")

If both EMERGENCY and MEDICAL_ADVICE apply, EMERGENCY strictly wins.

LANGUAGE:
- 'hi' if written in Devanagari script (e.g., 'मुझे सिरदर्द है')
- 'hinglish' if Hindi words are written in Latin script (e.g., 'mujhe fever hai, doctor chahiye')
- 'en' if written predominantly in English (e.g., 'I want to book an appointment')

FEW-SHOT EXAMPLES:
- User: "My grandfather suddenly fell down and is not waking up!"
  Result: {"verdict": "EMERGENCY", "language": "en"}
- User: "सीने में बहुत तेज दर्द हो रहा है सांस भी नहीं आ रही"
  Result: {"verdict": "EMERGENCY", "language": "hi"}
- User: "bhaiya gale mein infection hai kaunsi antibiotic lu?"
  Result: {"verdict": "MEDICAL_ADVICE", "language": "hinglish"}
- User: "What dose of amoxicillin should I give to my 5-year-old child?"
  Result: {"verdict": "MEDICAL_ADVICE", "language": "en"}
- User: "Dr. Khanna ki cardiology appointment book karni hai Tuesday"
  Result: {"verdict": "SAFE", "language": "hinglish"}
- User: "I had a mild fever yesterday, please log symptom fever severity 2"
  Result: {"verdict": "SAFE", "language": "en"}
"""


def detect_fallback_language(
    text: str,
    request_language: str | None = None,
    patient_language: str | None = None,
) -> str:
    """Determine best guess for language when classifier fails."""
    if request_language in ("en", "hi", "hinglish"):
        return request_language
    if patient_language in ("en", "hi", "hinglish"):
        return patient_language
    if re.search(r"[\u0900-\u097F]", text):
        return "hi"
    return "en"


async def classify_safety(
    message: str,
    patient_id: str = "unknown",
    request_id: str = "unknown",
    request_language: str | None = None,
    patient_language: str | None = None,
    model=None,
) -> tuple[SafetyVerdict, str, bool]:
    """Classify user message safety and language.

    Returns:
        tuple of (verdict, language, safety_failed)
    """
    clean_msg = message.strip()
    regex_hit = is_regex_emergency(clean_msg)

    # Prepare messages for cache and LLM call (strictly without volatile dates/ids)
    messages_payload = [
        {"role": "system", "content": SAFETY_SYSTEM_PROMPT},
        {"role": "user", "content": clean_msg},
    ]

    async def _call_llm():
        chat_model = model or get_chat_model(temperature=0.0)
        structured_model = chat_model.with_structured_output(SafetyClassificationOutput)
        langchain_msgs = [
            SystemMessage(content=SAFETY_SYSTEM_PROMPT),
            HumanMessage(content=clean_msg),
        ]
        return await structured_model.ainvoke(langchain_msgs)

    try:
        data = await asyncio.wait_for(
            execute_with_cache(
                task_name="safety_classifier",
                schema_name="SafetyClassificationOutput",
                messages=messages_payload,
                llm_callable=_call_llm,
            ),
            timeout=settings.SAFETY_TIMEOUT_S,
        )

        verdict_str = data.get("verdict", "SAFE")
        verdict = SafetyVerdict(verdict_str)
        detected_lang = data.get("language", "en")

        # Belt-and-braces: If regex matched emergency, higher level wins (never downgrade)
        if regex_hit:
            verdict = SafetyVerdict.EMERGENCY

        return verdict, detected_lang, False

    except (asyncio.TimeoutError, Exception) as exc:
        reason = "timeout" if isinstance(exc, asyncio.TimeoutError) else f"provider_error: {exc}"
        log_safety_classifier_failure(
            reason=reason,
            patient_id=patient_id,
            request_id=request_id,
        )

        lang = detect_fallback_language(clean_msg, request_language, patient_language)

        # Fail closed with regex fallback:
        if regex_hit:
            # Regex detected an acute emergency despite classifier failure
            return SafetyVerdict.EMERGENCY, lang, False
        else:
            # Block message execution safely
            return SafetyVerdict.SAFE, lang, True
