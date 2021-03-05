import pytchat
chat = pytchat.create(video_id="Ww6QEItZtUs")
while chat.is_alive():
    print("chat is alive")
    for c in chat.get().sync_items():
        print(f"{c.datetime} [{c.author.name}]- {c.message}")