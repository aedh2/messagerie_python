from core.auth import connect_db

def save_image(sender, receiver, img_enc_recv, key_enc_recv, iv_enc_recv, img_enc_self, key_enc_self, iv_enc_self):
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO images (
            sender, receiver,
            encrypted_key_for_receiver, encrypted_iv_for_receiver, encrypted_image_for_receiver,
            encrypted_key_for_sender, encrypted_iv_for_sender, encrypted_image_for_sender
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
    """, (sender, receiver, key_enc_recv, iv_enc_recv, img_enc_recv, key_enc_self, iv_enc_self, img_enc_self))
    conn.commit()
    cursor.close()
    conn.close()

def get_images(user1, user2):
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT sender, receiver,
               encrypted_key_for_receiver, encrypted_iv_for_receiver, encrypted_image_for_receiver,
               encrypted_key_for_sender, encrypted_iv_for_sender, encrypted_image_for_sender
        FROM images
        WHERE (sender = %s AND receiver = %s) OR (sender = %s AND receiver = %s)
        ORDER BY timestamp ASC
    """, (user1, user2, user2, user1))
    results = cursor.fetchall()
    cursor.close()
    conn.close()
    return results
