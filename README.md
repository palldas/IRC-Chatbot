CSC 482
Pallavi Das and Kasey Liu
Lab 5: IRC Chatbot 

Files expected in this folder:
- bot.py
- milestone3_bert_self_intro/ (contains model.safetensors + tokenizer/config files)

Setup
1) Install dependencies:
   pip3 install -r Packages.txt
   (Note: The script will automatically download the spaCy 'en_core_web_trf' model on first run if it is not already installed.)

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
  - dasliu-bot: who are you?
  - dasliu-bot: users
  - dasliu-bot: forget
  - dasliu-bot: die
  - dasliu-bot: classify <text>

Part II:
- Outreach/greeting messages trigger the finite-state greeting flow.
- dasliu-bot will send initial outreach after 15 seconds if no one outreaches to it
- dasliu-bot gives up after 20 seconds with no reply

Part III (Specific QA):
Our implementation features a legislative self-introduction classifier built with BERT and spaCy.
- Explicit classification command:
  dasliu-bot: classify Hi, my name is Kasey.

The bot will return a confidence score identifying whether the text is a self-introduction, the primary speaker's name, and any other names detected in the text.

Model notes
- bot.py loads model files from:
  milestone3_bert_self_intro
- Inputs longer than 512 tokens are chunked using 510-token chunks, then
  chunk predictions are aggregated (if any chunk is self-intro, final label is self-intro).
