from pytchat import LiveChat
import time
chat = LiveChat(video_id = "Ww6QEItZtUs")

while chat.is_alive():
  try:
    data = chat.get()
    items = data.items
    for c in items:
        print(f"{c.datetime} [{c.author.name}]- {c.message}")
    time.sleep(3)
  except KeyboardInterrupt:
    chat.terminate()
    break