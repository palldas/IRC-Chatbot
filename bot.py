import irc.bot
import irc.strings
import time
import sys
import threading

class ChatBot(irc.bot.SingleServerIRCBot):
    def __init__(self, channel, nickname, server, port=6667):
        super().__init__([(server, port)], nickname, nickname)
        self.channel_name = channel
        self.creator_info = "Pallavi Das and Kasey Liu, CSC 482"

    def on_nicknameinuse(self, c, e):
        c.nick(c.get_nickname() + "_")

    def on_welcome(self, c, e):
        c.join(self.channel_name)
        print(f"[{c.get_nickname()}] Connected and joined {self.channel_name}")

    def on_pubmsg(self, c, e):
        msg = e.arguments[0]
        sender = e.source.nick
        
        print(f"[{self.channel_name}] {sender}: {msg}")
        prefix = c.get_nickname() + ":"
        
        if msg.lower().startswith(prefix.lower()):
            command = msg[len(prefix):].strip().lower()
            self.do_command(e, command, c)

    def send_delayed_msg(self, target, msg):
        def delayed_send():
            time.sleep(2)
            self.connection.privmsg(target, msg)
            print(f"[{target}] {self.connection.get_nickname()}: {msg}")
            
        threading.Thread(target=delayed_send, daemon=True).start()

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

        elif cmd in ["hi", "hello"]:
            self.send_delayed_msg(target, f"{sender}: hi back!")


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
