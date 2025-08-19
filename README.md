# **Visa InfoBot**

Visa InfoBot is a portable visa-information chatbot. It separates the conversation logic from the data, so you can reuse the same app with any country’s rules by swapping a single JSON file. This demo uses Nigeria as the example dataset: type a country (e.g., “Bolivia” or “How about Iran?”) and the bot tells you whether a visa is required to enter Nigeria. If a visa is needed, it guides you through visa types and shows the relevant requirements.

---

## Features
- Friendly onboarding (“Which country are you from?”)
- Country detection in free text (e.g., “How about Iran?”)
- Instant visa decision (visa-free vs visa-required)
- If visa-required → quick-reply chips for visa types
- **General + specific** requirements in one answer
- Mid-flow country switch + “same-country” nudge
- Admin sidebar: visa-free/required lists & simple analytics
- Two interfaces: **Streamlit UI** and **CLI**

---

## Project Structure

```
Visa-InfoBot/
├─ streamlit_app.py # Streamlit UI (primary app)
├─ interface.py # CLI chat (optional)
├─ Conversation # JSON config (prompts, countries, visa text) ← required
├─ data_loader.py # Helpers for classic intent model
├─ rule_based.py # Greetings/farewell & small rules
├─ model_intent.py # Tfidf + Naive Bayes (fallback intent model)
├─ visa_intent_model.pkl # (optional) saved model
└─ README.md
```

---
**Troubleshooting**

- **File not found:** Conversation
The app can’t see its config file. Make sure a file named Conversation (capital C, no extension) is in the same folder as streamlit_app.py. If you renamed it, update CONFIG_PATH in streamlit_app.py.

- **New chat doesn’t clear**
Streamlit keeps session state between reruns. Use Sidebar → Admin → New chat to reset. The app also auto-resets when the Conversation file changes (modified time/size).

- **Enter doesn’t send (requires two presses)**
First, enter didn’t send? Just type again and hit Enter (or click Send)—it’ll go through. We’re working on a one-press fix.

**License**
MIT © Udodirim Nwosu (udynwosu@gmail.com)
