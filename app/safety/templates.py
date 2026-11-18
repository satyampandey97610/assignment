"""Fixed non-LLM response templates for emergencies, refusals, blocked failures, and abstentions."""

# Emergency templates: Call 112, hospital emergency phone, stay with person, nurse callback in 5 min
EMERGENCY_TEMPLATES = {
    "en": (
        "EMERGENCY DETECTED: Please call 112 immediately. "
        "You can also reach the hospital emergency desk at {hospital_emergency_phone}. "
        "Please stay with the person. An emergency escalation has been raised and a triage nurse "
        "will call you back within 5 minutes. Do not administer medications."
    ),
    "hi": (
        "आपातकालीन स्थिति: कृपया तुरंत 112 पर कॉल करें। "
        "आप अस्पताल के इमरजेंसी नंबर {hospital_emergency_phone} पर भी संपर्क कर सकते हैं। "
        "कृपया मरीज़ के साथ ही रहें। इमरजेंसी सूचना दर्ज कर दी गई है और एक नर्स आपको 5 मिनट के भीतर कॉल करेगी।"
    ),
    "hinglish": (
        "EMERGENCY DETECTED: Kripya turant 112 par call karein. "
        "Aap hospital emergency number {hospital_emergency_phone} par bhi contact kar sakte hain. "
        "Kripya person ke saath hi rahein. Emergency alert raise ho chuka hai aur nurse aapko 5 minutes "
        "ke andar call karegi."
    ),
}

# Medical advice refusal templates: cannot diagnose/prescribe/give dosage, offers to book consultation
MEDICAL_ADVICE_TEMPLATES = {
    "en": (
        "I am an AI assistant and cannot provide medical advice, diagnosis, or medication prescriptions and dosages. "
        "If you are feeling unwell, I can help you book a consultation with a General Physician or specialist at our wellness center. "
        "Would you like me to book an appointment for you?"
    ),
    "hi": (
        "मैं एक एआई सहायक हूँ और कोई भी चिकित्सीय सलाह, निदान, या दवा की खुराक नहीं बता सकता। "
        "यदि आप अस्वस्थ महसूस कर रहे हैं, तो मैं वेलनेस सेंटर में जनरल फिजिशियन या विशेषज्ञ के साथ डॉक्टर परामर्श बुक करने में आपकी मदद कर सकता हूँ। "
        "क्या आप परामर्श बुक करना चाहेंगे?"
    ),
    "hinglish": (
        "Main ek AI assistant hoon aur medical advice, diagnosis ya dawa ki dosage nahi de sakta. "
        "Agar aapki tabiyat kharab hai, toh main wellness center mein General Physician ya specialist ke saath consultation book karne mein help kar sakta hoon. "
        "Kya aap appointment book karna chahenge?"
    ),
}

# Blocked templates for classifier failure (fail-closed policy)
BLOCKED_TEMPLATES = {
    "en": (
        "I can't process this right now. If it is urgent, please call 112 or the hospital emergency desk at {hospital_emergency_phone}."
    ),
    "hi": (
        "मैं इस समय इस अनुरोध को संसाधित नहीं कर सकता। यदि यह आपातकालीन है, तो कृपया 112 पर कॉल करें या अस्पताल इमरजेंसी {hospital_emergency_phone} पर संपर्क करें।"
    ),
    "hinglish": (
        "Main abhi is request ko process nahi kar sakta. Agar yeh urgent hai toh please 112 par call karein ya hospital emergency {hospital_emergency_phone} par contact karein."
    ),
}

# Abstain templates when clinic document retrieval similarity is below threshold
ABSTAIN_TEMPLATES = {
    "en": (
        "I do not have enough information from MicroHeal's official clinic documents to answer your question accurately. "
        "For assistance, please contact the hospital front desk at {hospital_front_desk_phone} or visit the wellness room."
    ),
    "hi": (
        "माइक्रोहील के आधिकारिक दस्तावेज़ों में आपके प्रश्न का निश्चित उत्तर उपलब्ध नहीं है। "
        "अधिक जानकारी के लिए कृपया अस्पताल के फ्रंट डेस्क {hospital_front_desk_phone} पर संपर्क करें या वेलनेस रूम आएं।"
    ),
    "hinglish": (
        "MicroHeal ke clinic documents mein is sawal ki poori jankari available nahi hai. "
        "Help ke liye please hospital front desk par {hospital_front_desk_phone} par call karein ya wellness room visit karein."
    ),
}


def get_emergency_reply(language: str, hospital_emergency_phone: str) -> str:
    lang = language.lower() if language else "en"
    template = EMERGENCY_TEMPLATES.get(lang, EMERGENCY_TEMPLATES["en"])
    return template.format(hospital_emergency_phone=hospital_emergency_phone)


def get_medical_advice_refusal(language: str) -> str:
    lang = language.lower() if language else "en"
    return MEDICAL_ADVICE_TEMPLATES.get(lang, MEDICAL_ADVICE_TEMPLATES["en"])


def get_blocked_reply(language: str, hospital_emergency_phone: str) -> str:
    lang = language.lower() if language else "en"
    template = BLOCKED_TEMPLATES.get(lang, BLOCKED_TEMPLATES["en"])
    return template.format(hospital_emergency_phone=hospital_emergency_phone)


def get_abstain_reply(language: str, hospital_front_desk_phone: str) -> str:
    lang = language.lower() if language else "en"
    template = ABSTAIN_TEMPLATES.get(lang, ABSTAIN_TEMPLATES["en"])
    return template.format(hospital_front_desk_phone=hospital_front_desk_phone)
