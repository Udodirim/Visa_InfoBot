
"""
CLI wrapper implementing a linear flow:
1. Greeting/prompt for country
2. Country visa check (visa_required flag)
3. Visa-type follow-up if needed
4. Fallbacks and goodbye
All prompts, country list, and visa-type responses come from conversation.json.
"""
import json
import re

# Path to your Conversation JSON file
INTENT_JSON = '/content/drive/MyDrive/Chat_bot/Conversation'

class ChatCLI:
    def __init__(self) -> None:
        # Load entire config
        with open(INTENT_JSON, 'r', encoding='utf-8') as f:
            config = json.load(f)
        # Prompts
        self.prompts = config.get('prompts', {})
        # Country visa mapping
        self.country_map = {
            c['name'].strip().lower(): c['visa_required']
            for c in config.get('country_check', {}).get('countries', [])
        }
        # Visa type responses map (keys are original titles)
        self.visa_types = config.get('visa_types', {})
        # Lowercase lookup map for visa types
        self.visa_type_map = {k.lower(): v for k, v in self.visa_types.items()}
        # Visa type options list for display
        self.opts = ', '.join(self.prompts.get('visa_type_options', list(self.visa_types.keys())))
        # Conversation state
        self.state = 'ASK_COUNTRY'

    def respond(self, user_input: str) -> str:
        text = user_input.strip()
        key = text.lower()
        # Farewell at any time
        if re.search(r"\b(bye|goodbye|see you|exit|quit)\b", text, re.IGNORECASE):
            return self.prompts.get('goodbye', 'Thank you—hope I helped. Goodbye!')
        # State: ask country
        if self.state == 'ASK_COUNTRY':
            if key in self.country_map:
                if not self.country_map[key]:
                    self.state = 'END'
                    return (
                        "Excellent, you do not need a visa to visit Nigeria. "
                        + self.prompts.get('ask_more', '')
                    )
                else:
                    self.state = 'ASK_VISA_TYPE'
                    return self.prompts.get(
                        'ask_visa_type',
                        f"Great! You need a visa to visit Nigeria. Which visa type are you interested in? ({self.opts})"
                    )
            # unrecognized country
            return self.prompts.get('fallback_country', 'Sorry, I didn\'t recognize that country. Please try again.')

        # State: ask visa type
        if self.state == 'ASK_VISA_TYPE':
            vt_key = text.lower()
            # if user asks options
            if 'option' in vt_key:
                return f"Available visa types: {self.opts}"
            details = self.visa_type_map.get(vt_key)
            self.state = 'END'
            if details:
                return details['response'] + "\n" + self.prompts.get('ask_more', '')
            return self.prompts.get(
                'fallback_visa_type',
                f"Sorry, I don't have details for '{text}'. Options: {self.opts}."
            )

        # State: end/follow-up
        if self.state == 'END':
            if re.search(r"\b(yes|yep|yeah|sure|of course)\b", text, re.IGNORECASE):
                self.state = 'ASK_COUNTRY'
                return self.prompts.get('ask_country', "Please tell me which country you're from.")
            return self.prompts.get('goodbye', 'Thank you—hope I helped. Goodbye!')

        # Fallback default
        return self.prompts.get('fallback_country', 'Sorry, I didn\'t understand that.')

    def chat(self) -> None:
        # Start conversation
        print(self.prompts.get('welcome', 'Hello!'))
        print(self.prompts.get('ask_country', 'Which country are you from?'))
        while True:
            user_input = input('> ')
            # direct exit
            if user_input.strip().lower() in ('exit', 'quit'):
                print(self.prompts.get('goodbye', 'Goodbye!'))
                break
            print(self.respond(user_input))

if __name__ == '__main__':
    ChatCLI().chat()
