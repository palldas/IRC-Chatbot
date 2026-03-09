CSC 482 
Lab 5: IRC Chatbot 

Files expected in this folder:
- bot.py
- bot_state.json
- milestone3_bert_self_intro/ (contains model.safetensors + tokenizer/config files)

Setup
1) Install dependencies:
   pip3 install -r Packages.txt

Run
1) From this directory:
   python3 bot.py

2) Bot connects with defaults in bot.py:
   SERVER = irc.libera.chat
   PORT = 6667
   CHANNEL = #CSC482
   BOTNICK = dasliu-bot

How to interact
- Address the bot in channel using:
  dasliu-bot: <message>

Part I commands:
- Commands:
  - dasliu-bot: usage
  - dasliu-bot: users
  - dasliu-bot: forget

Part II:
- Outreach/greeting messages trigger the finite-state greeting flow.
- dasliu-bot will send initial outreach after 15 seconds if no one outreaches to it
- dasliu-bot gives up after 20 seconds with no reply

Part III examples:
- Explicit classification command:
  dasliu-bot: classify Hi, my name is Kasey.
- Or send non-greeting addressed text:
  dasliu-bot: I am Kasey and I am a student.

Model notes
- bot.py loads model files from:
  milestone3_bert_self_intro
- Inputs longer than 512 tokens are chunked using 510-token chunks, then
  chunk predictions are aggregated (if any chunk is self-intro, final label is self-intro).
