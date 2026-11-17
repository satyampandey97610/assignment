"""Enum definitions for domain services, intents, safety verdicts, and subtypes."""

from enum import StrEnum


class Service(StrEnum):
    DOCTOR = "DOCTOR"
    LAB = "LAB"


class Intent(StrEnum):
    BOOK_SERVICE = "BOOK_SERVICE"
    LIST_SERVICES = "LIST_SERVICES"
    LOG_SYMPTOM = "LOG_SYMPTOM"
    CLINIC_INFO = "CLINIC_INFO"
    MEDICAL_ADVICE = "MEDICAL_ADVICE"
    EMERGENCY = "EMERGENCY"
    SMALL_TALK = "SMALL_TALK"
    UNKNOWN = "UNKNOWN"


class SafetyVerdict(StrEnum):
    EMERGENCY = "EMERGENCY"
    MEDICAL_ADVICE = "MEDICAL_ADVICE"
    SAFE = "SAFE"


class BookingStatus(StrEnum):
    CONFIRMED = "CONFIRMED"
    CANCELLED = "CANCELLED"
    COMPLETED = "COMPLETED"
    NO_SHOW = "NO_SHOW"


class EscalationStatus(StrEnum):
    OPEN = "OPEN"
    ACKNOWLEDGED = "ACKNOWLEDGED"
    CLOSED = "CLOSED"


class Weekday(StrEnum):
    MON = "MON"
    TUE = "TUE"
    WED = "WED"
    THU = "THU"
    FRI = "FRI"
    SAT = "SAT"
    SUN = "SUN"


class Subtype(StrEnum):
    # Doctor departments
    GENERAL_PHYSICIAN = "GENERAL_PHYSICIAN"
    CARDIOLOGY = "CARDIOLOGY"
    PAEDIATRICS = "PAEDIATRICS"
    ORTHOPAEDICS = "ORTHOPAEDICS"
    DERMATOLOGY = "DERMATOLOGY"
    ENT = "ENT"
    GYNAECOLOGY = "GYNAECOLOGY"
    PHYSIOTHERAPY = "PHYSIOTHERAPY"

    # Lab tests
    CBC = "CBC"
    FASTING_BLOOD_SUGAR = "FASTING_BLOOD_SUGAR"
    HBA1C = "HBA1C"
    LIPID_PROFILE = "LIPID_PROFILE"
    LFT = "LFT"
    KFT = "KFT"
    THYROID_PROFILE = "THYROID_PROFILE"
    VITAMIN_D = "VITAMIN_D"
    URINE_ROUTINE = "URINE_ROUTINE"


DOCTOR_SUBTYPES = {
    Subtype.GENERAL_PHYSICIAN,
    Subtype.CARDIOLOGY,
    Subtype.PAEDIATRICS,
    Subtype.ORTHOPAEDICS,
    Subtype.DERMATOLOGY,
    Subtype.ENT,
    Subtype.GYNAECOLOGY,
    Subtype.PHYSIOTHERAPY,
}

LAB_SUBTYPES = {
    Subtype.CBC,
    Subtype.FASTING_BLOOD_SUGAR,
    Subtype.HBA1C,
    Subtype.LIPID_PROFILE,
    Subtype.LFT,
    Subtype.KFT,
    Subtype.THYROID_PROFILE,
    Subtype.VITAMIN_D,
    Subtype.URINE_ROUTINE,
}
