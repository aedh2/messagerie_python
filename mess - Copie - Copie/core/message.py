class Message:
    def __init__(self, sender, receiver, encrypted_text_receiver, encrypted_text_sender):
        self.sender = sender
        self.receiver = receiver
        self.encrypted_text_receiver = encrypted_text_receiver
        self.encrypted_text_sender = encrypted_text_sender
