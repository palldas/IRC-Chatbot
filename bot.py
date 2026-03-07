import irc.bot
import irc.strings
import time
import sys
import threading
import random
import json
import os

initial_outreach_phrases = ["hello", "hi"]
secondary_outreach_phrases = ["I said HI!", "excuse me, hello?", "hellllloooooo!"]
outreach_reply_phrases = ["hello back at you!", "hi"]
inquiry_phrases = ["how are you?", "what's happening?", "how is it going?", "how are you doing?"]
inquiry_reply_phrases = [
    "I'm good",
    "I'm fine",
    "I'm fine, thanks for asking",
    "I'm great!",
    "Great!",
]
inquiry_back_phrases = ["how about you?", "and yourself?", "how about yourself?"]
giveup_phrases = ["Ok, forget you.", "Whatever.", "screw you!", "whatever, fine. Don't answer."]

class ChatBot(irc.bot.SingleServerIRCBot):
    def __init__(self, channel, nickname, server, port=6667):
        super().__init__([(server, port)], nickname, nickname)
        self.channel_name = channel
        self.creator_info = "Pallavi Das and Kasey Liu, CSC 482"
        self.state_file = "bot_state.json"
        self.lock = threading.RLock()
        self.timeout_timer = None
        self.initial_outreach_timer = None
        self.greeting = {
            "state": "START",
            "partner": None,
        }
        self.outreach_inputs = {
            self.normalize_text(p)
            for p in (initial_outreach_phrases + secondary_outreach_phrases + outreach_reply_phrases)
        }
        self.inquiry_inputs = {self.normalize_text(p) for p in (inquiry_phrases + inquiry_back_phrases)}
        self.inquiry_reply_inputs = {self.normalize_text(p) for p in inquiry_reply_phrases}
        self.giveup_inputs = {self.normalize_text(p) for p in giveup_phrases}
        self.load_state()

    def on_nicknameinuse(self, c, e):
        c.nick(c.get_nickname() + "_")

    def on_welcome(self, c, e):
        c.join(self.channel_name)
        print(f"[{c.get_nickname()}] Connected and joined {self.channel_name}")
        self.reset_conversation(persist=True)
        self.schedule_initial_outreach()

    def on_pubmsg(self, c, e):
        msg = e.arguments[0]
        sender = e.source.nick
        
        print(f"[{self.channel_name}] {sender}: {msg}")
        prefix = c.get_nickname() + ":"
        
        if msg.lower().startswith(prefix.lower()):
            text = msg[len(prefix):].strip()
            command = text.lower()
            if self.is_command(command):
                self.do_command(e, command, c)
            else:
                self.handle_greeting_message(sender, text)

    def send_delayed_msg(self, target, msg, delay=2):
        def delayed_send():
            time.sleep(delay)
            self.connection.privmsg(target, msg)
            print(f"[{target}] {self.connection.get_nickname()}: {msg}")
            
        threading.Thread(target=delayed_send, daemon=True).start()

    def is_command(self, cmd):
        return cmd in {"die", "forget", "who are you?", "usage", "users"}

    def load_state(self):
        if not os.path.exists(self.state_file):
            return
        try:
            with open(self.state_file, "r", encoding="utf-8") as f:
                saved = json.load(f)
            if isinstance(saved, dict) and "state" in saved:
                self.greeting["state"] = saved.get("state", "START")
                self.greeting["partner"] = saved.get("partner")
                print(f"Loaded saved state: {self.greeting}")
        except Exception as ex:
            print(f"Failed to load state file: {ex}")

    def save_state(self):
        with open(self.state_file, "w", encoding="utf-8") as f:
            json.dump(self.greeting, f)

    def clear_saved_state(self):
        if os.path.exists(self.state_file):
            os.remove(self.state_file)

    def transition(self, new_state, partner=None, persist=True):
        with self.lock:
            self.greeting["state"] = new_state
            if partner is not None:
                self.greeting["partner"] = partner
            if persist:
                self.save_state()

    def reset_conversation(self, persist=True):
        with self.lock:
            self.cancel_timeout_timer()
            self.greeting = {"state": "START", "partner": None}
            if persist:
                self.save_state()

    def cancel_timeout_timer(self):
        if self.timeout_timer and self.timeout_timer.is_alive():
            self.timeout_timer.cancel()
        self.timeout_timer = None

    def schedule_timeout(self, seconds=None):
        with self.lock:
            self.cancel_timeout_timer()
            timeout = seconds if seconds is not None else 20
            self.timeout_timer = threading.Timer(timeout, self.handle_timeout)
            self.timeout_timer.daemon = True
            self.timeout_timer.start()

    def schedule_initial_outreach(self):
        with self.lock:
            if self.initial_outreach_timer and self.initial_outreach_timer.is_alive():
                self.initial_outreach_timer.cancel()
            wait = 15
            self.initial_outreach_timer = threading.Timer(wait, self.try_initial_outreach)
            self.initial_outreach_timer.daemon = True
            self.initial_outreach_timer.start()

    def try_initial_outreach(self):
        with self.lock:
            if self.greeting["state"] != "START":
                return
            channel_obj = self.channels.get(self.channel_name)
            if not channel_obj:
                self.schedule_initial_outreach()
                return
            my_nick = self.connection.get_nickname().lower()
            users = [u for u in channel_obj.users() if u.lower() != my_nick]
            users = [u for u in users if "serv" not in u.lower() and "bot" not in u.lower()]
            if not users:
                self.schedule_initial_outreach()
                return

            partner = random.choice(users)
            line = random.choice(initial_outreach_phrases)
            self.send_to_user(partner, line)
            self.transition("1_INITIAL_OUTREACH", partner=partner)
            self.schedule_timeout()

    def send_to_user(self, user, text, delay=2):
        self.send_delayed_msg(self.channel_name, f"{user}: {text}", delay=delay)

    def do_giveup(self, speaker_prefix):
        phrase = random.choice(giveup_phrases)
        partner = self.greeting["partner"]
        if partner:
            self.send_to_user(partner, phrase)
        self.transition(speaker_prefix, partner=partner)
        self.transition("END", partner=partner)
        self.reset_conversation(persist=True)
        self.schedule_initial_outreach()

    def handle_timeout(self):
        with self.lock:
            state = self.greeting["state"]
            partner = self.greeting["partner"]
            if not partner:
                return

            if state == "1_INITIAL_OUTREACH":
                self.send_to_user(partner, random.choice(secondary_outreach_phrases))
                self.transition("1_SECONDARY_OUTREACH", partner=partner)
                self.schedule_timeout()
            elif state == "1_SECONDARY_OUTREACH":
                self.do_giveup("1_GIVEUP_FRUSTRATED")
            elif state == "1_INQUIRY":
                self.do_giveup("1_GIVEUP_FRUSTRATED")
            elif state == "2_OUTREACH_REPLY":
                self.do_giveup("2_GIVEUP_FRUSTRATED")
            elif state == "2_INQUIRY":
                self.do_giveup("2_GIVEUP_FRUSTRATED")
            elif state == "2_INQUIRY_REPLY":
                self.transition("END", partner=partner)
                self.reset_conversation(persist=True)
                self.schedule_initial_outreach()

    def contains_outreach(self, text):
        t = self.normalize_text(text)
        return t in self.outreach_inputs

    def contains_inquiry(self, text):
        t = self.normalize_text(text)
        return t in self.inquiry_inputs

    def contains_inquiry_reply(self, text):
        t = self.normalize_text(text)
        return t in self.inquiry_reply_inputs

    def contains_giveup(self, text):
        t = self.normalize_text(text)
        return t in self.giveup_inputs

    def normalize_text(self, text):
        return text.strip().lower()

    def handle_greeting_message(self, sender, text):
        with self.lock:
            state = self.greeting["state"]
            partner = self.greeting["partner"]

            if self.contains_giveup(text):
                if state != "START" and partner == sender:
                    self.transition("END", partner=partner)
                    self.reset_conversation(persist=True)
                    self.schedule_initial_outreach()
                return

            if state == "START":
                if self.contains_outreach(text):
                    self.transition("2_OUTREACH_REPLY", partner=sender)
                    self.send_to_user(sender, random.choice(outreach_reply_phrases))
                    self.schedule_timeout()
                return

            if partner != sender:
                return

            if state in {"1_INITIAL_OUTREACH", "1_SECONDARY_OUTREACH"}:
                if self.contains_outreach(text):
                    self.cancel_timeout_timer()
                    self.transition("2_OUTREACH_REPLY", partner=partner)
                    self.transition("1_INQUIRY", partner=partner)
                    self.send_to_user(partner, random.choice(inquiry_phrases))
                    self.schedule_timeout()
                return

            if state == "1_INQUIRY":
                if self.contains_inquiry_reply(text) and self.contains_inquiry(text):
                    self.cancel_timeout_timer()
                    self.transition("2_INQUIRY_REPLY", partner=partner)
                    self.transition("2_INQUIRY", partner=partner)
                    self.transition("1_INQUIRY_REPLY", partner=partner)
                    self.send_to_user(partner, random.choice(inquiry_reply_phrases))
                    self.transition("END", partner=partner)
                    self.reset_conversation(persist=True)
                    self.schedule_initial_outreach()
                elif self.contains_inquiry_reply(text):
                    self.cancel_timeout_timer()
                    self.transition("2_INQUIRY_REPLY", partner=partner)
                    self.schedule_timeout()
                return

            if state == "2_OUTREACH_REPLY":
                if self.contains_inquiry(text):
                    self.cancel_timeout_timer()
                    self.transition("1_INQUIRY", partner=partner)
                    self.transition("2_INQUIRY_REPLY", partner=partner)
                    self.send_to_user(partner, random.choice(inquiry_reply_phrases), delay=2)
                    self.transition("2_INQUIRY", partner=partner)
                    self.send_to_user(partner, random.choice(inquiry_back_phrases), delay=3)
                    self.schedule_timeout()
                return

            if state == "2_INQUIRY":
                if self.contains_inquiry_reply(text):
                    self.cancel_timeout_timer()
                    self.transition("1_INQUIRY_REPLY", partner=partner)
                    self.transition("END", partner=partner)
                    self.reset_conversation(persist=True)
                    self.schedule_initial_outreach()
                return

            if state == "2_INQUIRY_REPLY":
                if self.contains_inquiry(text):
                    self.cancel_timeout_timer()
                    self.transition("2_INQUIRY", partner=partner)
                    self.transition("1_INQUIRY_REPLY", partner=partner)
                    self.send_to_user(partner, random.choice(inquiry_reply_phrases))
                    self.transition("END", partner=partner)
                    self.reset_conversation(persist=True)
                    self.schedule_initial_outreach()

    def do_command(self, e, cmd, c):
        sender = e.source.nick
        target = self.channel_name

        if cmd == "die":
            self.send_delayed_msg(target, f"{sender}: I shall!")
            time.sleep(3) 
            c.quit("Quit: chat-bot")
            sys.exit(0)

        elif cmd == "forget":
            self.send_delayed_msg(target, f"{sender}: forgetting everything")
            with self.lock:
                self.cancel_timeout_timer()
                if self.initial_outreach_timer and self.initial_outreach_timer.is_alive():
                    self.initial_outreach_timer.cancel()
                self.reset_conversation(persist=False)
                self.clear_saved_state()
                self.schedule_initial_outreach()
            
        elif cmd in ["who are you?", "usage"]:
            msg1 = f"My name is {c.get_nickname()}. I was created by {self.creator_info}"
            msg2 = 'I can answer questions about the weather! Ask me a question like this: "What is the weather in Paris?"'
            self.send_delayed_msg(target, f"{sender}: {msg1}")
            self.send_delayed_msg(target, f"{sender}: {msg2}")

        elif cmd == "users":
            channel_obj = self.channels.get(self.channel_name)
            if channel_obj:
                users_list = ", ".join(channel_obj.users())
                self.send_delayed_msg(target, f"{sender}: {users_list}")
            else:
                self.send_delayed_msg(target, f"{sender}: I am not in the channel.")


if __name__ == "__main__":
    SERVER = "irc.libera.chat"
    PORT = 6667
    CHANNEL = "#CSC482"
    BOTNICK = "dasliu-bot"
    
    print(f"Starting {BOTNICK} on {SERVER}:{PORT} in {CHANNEL}...")
    bot = ChatBot(CHANNEL, BOTNICK, SERVER, PORT)
    try:
        bot.start()
    except KeyboardInterrupt:
        print("\nBot shutting down manually.")
        sys.exit(0)
