import json
import os
import re
import time
from collections import Counter
from datetime import datetime
from pathlib import Path

import streamlit as st

# ===================== Config / constants =====================
APP_VERSION = "ui-v4"  # bump to force a state reset if needed
BASE_DIR = Path(__file__).parent
CONFIG_PATH = BASE_DIR / "Conversation"  # Capital C, no extension

with open(CONFIG_PATH, "r", encoding="utf-8") as f:
    config = json.load(f)

cfg_stat = os.stat(CONFIG_PATH)
SESSION_KEY = f"{APP_VERSION}:{int(cfg_stat.st_mtime)}:{cfg_stat.st_size}"

# ===================== Small helpers =====================
def canon(s: str) -> str:
    """Canonicalize for keys: lower + strip spaces/underscores/hyphens."""
    return re.sub(r"[\s_-]+", "", s.strip().lower())

def pretty(label: str) -> str:
    """Human-friendly label for display."""
    if canon(label) == "visaonarrival":
        return "Visa on Arrival"
    cleaned = label.replace("_", " ").replace("-", " ").strip()
    return cleaned if any(ch.isupper() for ch in cleaned) else cleaned.title()

def is_farewell(text: str) -> bool:
    return re.search(r"\b(bye|goodbye|see you|exit|quit)\b", text, re.IGNORECASE) is not None

def is_greeting(text: str) -> bool:
    return re.search(r"\b(hi|hello|hey|good day)\b", text, re.IGNORECASE) is not None

def is_thanks(text: str) -> bool:
    return re.search(r"\b(thanks?|thank\s*you)\b", text, re.IGNORECASE) is not None

def match_country(text: str, countries: dict) -> str | None:
    """Find a country as a whole word; tolerant of punctuation like 'Iran?' or 'Iraq,'."""
    low = re.sub(r"[^\w\s]", " ", text.lower())  # strip punctuation to spaces
    for c in countries.keys():
        if re.search(rf"\b{re.escape(c)}\b", low):
            return c
    return None

def resolve_visa_type(user_text: str, visa_types: dict, display_options: list[str]) -> str | None:
    """
    Robust resolver: accepts 'tourist', 'tourist visa', 'visa-on-arrival', etc.
    Returns canonical key from visa_types or None.
    """
    vt = canon(user_text)
    if vt in visa_types:
        return vt
    for k in visa_types.keys():
        if vt.startswith(k) or k in vt:
            return k
    for disp in display_options:
        dkey = canon(disp)
        if vt == dkey or vt.startswith(dkey) or dkey in vt:
            return dkey
    return None

# ===================== Data maps from JSON =====================
country_map = {
    c["name"].strip().lower(): bool(c["visa_required"])
    for c in config["country_check"]["countries"]
}

visa_types_raw = config.get("visa_types", {})
visa_types = {canon(k): v for k, v in visa_types_raw.items()}

# Build one pretty, de-duplicated options list from prompts + schema
prompt_opts = [pretty(x) for x in config.get("prompts", {}).get("visa_type_options", [])]
schema_opts = [pretty(k) for k in visa_types_raw.keys()]
seen, friendly_options = set(), []
for opt in prompt_opts + schema_opts:
    key = canon(opt)
    if key not in seen:
        seen.add(key)
        friendly_options.append(opt)

# Show chips WITHOUT "General"
display_options = [o for o in friendly_options if canon(o) != "general"]
options_str_display = ", ".join(display_options)

# ===================== Page chrome & CSS =====================
st.set_page_config(page_title="Nigeria Immigration Chatbot", layout="wide")

st.markdown("""
<style>
.block-container {max-width: 920px; margin: auto;}
[data-testid="stChatMessage"] {padding: 0.35rem 0.25rem;}
section.main > div {padding-bottom: 6rem;}
.sidebar-content {overflow-y: auto;}
</style>
""", unsafe_allow_html=True)

st.title("🛂 Nigerian Immigration Chatbot")
last_updated = datetime.fromtimestamp(cfg_stat.st_mtime).strftime("%d %b %Y")
st.caption(f"Demo • Data last updated: {last_updated}")

# ===================== Session state bootstrap =====================
def seed_welcome():
    return [
        ("Bot", config["prompts"]["welcome"]),
        ("Bot", config["prompts"]["ask_country"]),
    ]

def reset_chat():
    st.session_state.state = "ASK_COUNTRY"
    st.session_state.history = seed_welcome()
    st.session_state.current_country = None
    st.session_state.session_key = SESSION_KEY
    st.session_state.last_downloadable = ""  # last long answer for download
    st.session_state.analytics = {"countries": [], "visa_required": 0, "visa_free": 0}
    st.session_state["_focus_composer"] = True  # focus input after reset

# defaults
st.session_state.setdefault("state", "ASK_COUNTRY")
st.session_state.setdefault("history", [])
st.session_state.setdefault("current_country", None)
st.session_state.setdefault("session_key", SESSION_KEY)
st.session_state.setdefault("last_downloadable", "")
st.session_state.setdefault("analytics", {"countries": [], "visa_required": 0, "visa_free": 0})
st.session_state.setdefault("_focus_composer", False)

# Reset only if data file changed or first run
if st.session_state.session_key != SESSION_KEY or not st.session_state.history:
    reset_chat()

# Guard: ensure fresh chat starts with welcome
expected = seed_welcome()
if st.session_state.state == "ASK_COUNTRY" and (len(st.session_state.history) < 2 or st.session_state.history[:2] != expected):
    st.session_state.history = expected

# ===================== Sidebar (tabs) =====================
with st.sidebar:
    tabs = st.tabs(["Admin", "Countries", "Analytics"])

    with tabs[0]:
        st.subheader("Admin")
        if st.button("🗑️ New chat"):
            reset_chat()
            st.rerun()
        st.write("History persists across refresh. Data updates reset automatically.")
        st.write(f"App version: `{APP_VERSION}`")

    with tabs[1]:
        st.subheader("Visa-free countries")
        visa_free = sorted([c.title() for c, req in country_map.items() if not req])
        st.write(visa_free)
        st.subheader("Visa-required countries")
        visa_req = sorted([c.title() for c, req in country_map.items() if req])
        st.write(visa_req)

    with tabs[2]:
        st.subheader("Session analytics (demo)")
        asked = st.session_state.analytics["countries"]
        if asked:
            top = Counter(asked).most_common(10)
            st.write("**Top countries asked:**")
            st.write([f"{c.title()} ({n})" for c, n in top])
        colA, colB = st.columns(2)
        colA.metric("Visa-free answers", st.session_state.analytics["visa_free"])
        colB.metric("Visa-required answers", st.session_state.analytics["visa_required"])

# ===================== Render transcript (chat bubbles) =====================
for who, msg in st.session_state.history:
    avatar = "🤖" if who == "Bot" else "🧑"
    with st.chat_message("assistant" if who == "Bot" else "user", avatar=avatar):
        st.markdown(msg)

# ===================== Quick-reply chips (direct handler + autofocus) =====================
if st.session_state.state == "ASK_VISA_TYPE":
    st.markdown("**Choose a visa type:**")
    cols = st.columns(min(4, len(display_options)))
    chip_clicked = None
    for i, label in enumerate(display_options):
        if cols[i % len(cols)].button(label, key=f"vt_btn_{i}"):
            chip_clicked = label
            break

    if chip_clicked:
        # Show user bubble
        st.session_state.history.append(("You", chip_clicked))
        # Resolve + answer directly (no round-trip through text handler)
        vt_key = resolve_visa_type(chip_clicked, visa_types, display_options)
        details = visa_types.get(vt_key) if vt_key else None
        general = visa_types.get("general")
        country_disp = st.session_state.get("current_country", "your country")

        if details:
            header = f"**For {country_disp} — here are the requirements:**\n"
            general_md = f"##### General requirements\n{general['response']}" if general and general.get("response") else ""
            specific_md = f"\n\n##### {pretty(vt_key)} visa\n{details['response']}" if details.get("response") else ""
            reply = header + general_md + specific_md if (general_md or specific_md) else f"For {country_disp}, no details available."
            st.session_state.history.append(("Bot", reply))
            st.session_state.last_downloadable = reply
            st.session_state.state = "END"
        else:
            st.session_state.history.append((
                "Bot",
                config["prompts"].get(
                    "fallback_visa_type",
                    f"Sorry, I don't have details for '{chip_clicked}'. Options: {options_str_display}."
                )
            ))
        # focus composer on next run
        st.session_state["_focus_composer"] = True
        st.rerun()

# ===================== Input composer (form: Enter submits OR click Send) =====================
with st.form("composer", clear_on_submit=True):
    c1, c2 = st.columns([1, 0.2])
    user_text = c1.text_input(
        "You",
        placeholder="Type a country or question… (e.g., Bolivia or 'How about Iran')",
        label_visibility="collapsed",
        key="composer_input"
    )
    submitted = c2.form_submit_button("Send", use_container_width=True)

# Autofocus the composer input (after chips or reset)
if st.session_state.get("_focus_composer"):
    st.session_state["_focus_composer"] = False
    st.components.v1.html("""
        <script>
        const i = parent.document.querySelector('input[aria-label="You"]')
                 || parent.document.querySelector('input[placeholder^="Type a country"]');
        if (i) { i.focus(); i.scrollIntoView({behavior:'smooth', block:'end'}); }
        </script>
    """, height=0)

incoming_text = user_text.strip() if submitted and user_text else None

# ===================== Message handler for typed input =====================
if incoming_text:
    text = incoming_text
    key = text.lower()
    st.session_state.history.append(("You", text))

    with st.spinner("Thinking…"):
        time.sleep(0.2)

        # A) Global: THANK YOU (keep conversation open)
        if is_thanks(text):
            st.session_state.history.append(("Bot", "You're welcome! Have an amazing time in Nigeria!"))
            st.session_state.state = "END"

        # B) Global: Farewell
        elif is_farewell(text):
            st.session_state.history.append(("Bot", config["prompts"]["goodbye"]))
            st.session_state.state = "END"

        # C) Country check (works at start AND after END). Parse "how about iran".
        elif st.session_state.state in ("ASK_COUNTRY", "END"):
            if is_greeting(text):
                st.session_state.history.append(("Bot", config["prompts"]["ask_country"]))
                st.session_state.state = "ASK_COUNTRY"
            else:
                found = key if key in country_map else match_country(text, country_map)
                if found:
                    country_disp = found.title()
                    st.session_state.current_country = country_disp
                    st.session_state.analytics["countries"].append(found)

                    if not country_map[found]:
                        vf = config["prompts"].get(
                            "visa_free_msg",
                            "Excellent—you do not need a visa to visit Nigeria."
                        )
                        st.session_state.history.append(("Bot", f"For {country_disp}, {vf}"))
                        st.session_state.analytics["visa_free"] += 1
                        st.session_state.state = "END"
                    else:
                        ask_tmpl = config["prompts"].get(
                            "ask_visa_type",
                            "Great! You need a visa to visit Nigeria. Which visa type are you interested in?"
                        )
                        if "{visa_type_options}" in ask_tmpl:
                            ask = ask_tmpl.format(visa_type_options=options_str_display)
                        else:
                            ask = f"{ask_tmpl} ({options_str_display})"
                        ask = re.sub(r"\)\s*\([^()]*\)\s*$", ")", ask)  # drop accidental duplicate list
                        ask = f"For {country_disp}, {ask}"
                        st.session_state.history.append(("Bot", ask))
                        st.session_state.analytics["visa_required"] += 1
                        st.session_state.state = "ASK_VISA_TYPE"
                else:
                    st.session_state.history.append((
                        "Bot",
                        config["prompts"].get(
                            "fallback_country",
                            "Sorry, I didn't recognize that country. Please tell me which country you're from."
                        )
                    ))
                    st.session_state.state = "ASK_COUNTRY"

        # D) Visa-type follow-up (typed input path) with country-switch + same-country nudge
        elif st.session_state.state == "ASK_VISA_TYPE":
            # 1) Allow the user to change country mid-flow (and nudge if it's the same one)
            new_found = (key if key in country_map else match_country(text, country_map))
            if new_found:
                current_disp = st.session_state.get("current_country") or ""
                if canon(new_found) == canon(current_disp):
                    st.session_state.history.append((
                        "Bot",
                        f"We're already discussing **{current_disp}**. "
                        f"Please choose a visa type ({options_str_display}) or ask about another country."
                    ))
                    # Stay in ASK_VISA_TYPE
                else:
                    country_disp = new_found.title()
                    st.session_state.current_country = country_disp
                    st.session_state.analytics["countries"].append(new_found)

                    if not country_map[new_found]:
                        vf = config["prompts"].get(
                            "visa_free_msg",
                            "Excellent—you do not need a visa to visit Nigeria."
                        )
                        st.session_state.history.append(("Bot", f"For {country_disp}, {vf}"))
                        st.session_state.analytics["visa_free"] += 1
                        st.session_state.state = "END"
                    else:
                        ask_tmpl = config["prompts"].get(
                            "ask_visa_type",
                            "Great! You need a visa to visit Nigeria. Which visa type are you interested in?"
                        )
                        if "{visa_type_options}" in ask_tmpl:
                            ask = ask_tmpl.format(visa_type_options=options_str_display)
                        else:
                            ask = f"{ask_tmpl} ({options_str_display})"
                        ask = re.sub(r"\)\s*\([^()]*\)\s*$", ")", ask)  # drop accidental duplicate list
                        ask = f"For {country_disp}, {ask}"
                        st.session_state.history.append(("Bot", ask))
                        st.session_state.analytics["visa_required"] += 1
                        st.session_state.state = "ASK_VISA_TYPE"

            else:
                # 2) Treat input as a visa-type choice
                vt_key = resolve_visa_type(text, visa_types, display_options)
                details = visa_types.get(vt_key) if vt_key else None
                general = visa_types.get("general")
                country_disp = st.session_state.get("current_country", "your country")

                if details:
                    header = f"**For {country_disp} — here are the requirements:**\n"
                    general_md = f"##### General requirements\n{general['response']}" if general and general.get("response") else ""
                    specific_md = f"\n\n##### {pretty(vt_key)} visa\n{details['response']}" if details.get("response") else ""
                    reply = header + general_md + specific_md if (general_md or specific_md) else f"For {country_disp}, no details available."
                    st.session_state.history.append(("Bot", reply))
                    st.session_state.last_downloadable = reply
                    st.session_state.state = "END"
                else:
                    st.session_state.history.append((
                        "Bot",
                        config["prompts"].get(
                            "fallback_visa_type",
                            f"Sorry, I don't have details for '{text}'. Options: {options_str_display}."
                        )
                    ))

# ===================== Utilities under composer =====================
if st.session_state.last_downloadable:
    st.download_button(
        "⬇️ Download last answer (Markdown)",
        data=st.session_state.last_downloadable,
        file_name="nigeria-visa-info.md",
        mime="text/markdown",
        use_container_width=True,
    )
