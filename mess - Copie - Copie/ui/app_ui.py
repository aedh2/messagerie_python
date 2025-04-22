import tkinter as tk
from tkinter import messagebox
from core.auth import (
    register_user, login_user, get_public_key, save_message,
    get_messages, get_all_users, get_user_language, set_user_language
)
from core.crypto_utils import encrypt_message, decrypt_message, load_private_key
from datetime import datetime
from deep_translator import GoogleTranslator
from PIL import Image, ImageTk
import cv2, os, uuid
import threading
from core.hybrid_crypto import encrypt_image_base64_hybrid
from core.hybrid_crypto import decrypt_image_base64_hybrid
import io
from core.hybrid_crypto import encrypt_binary_hybrid
from core.image_storage import save_image
from core.image_storage import get_images
from core.hybrid_crypto import decrypt_binary_hybrid



def launch_app():
    app = tk.Tk()
    app.title("Messagerie Sécurisée")
    app.geometry("400x300")
    app.configure(bg="#e4e6eb")

    def switch_to_login():
        frame_register.pack_forget()
        frame_login.pack(fill="both", expand=True)

    def switch_to_register():
        frame_login.pack_forget()
        frame_register.pack(fill="both", expand=True)

    def open_settings(username):
        settings = tk.Toplevel()
        settings.title("Paramètres")
        settings.geometry("300x150")
        settings.configure(bg="#e4e6eb")

        tk.Label(settings, text="Langue de traduction :", bg="#e4e6eb", font=("Helvetica", 12)).pack(pady=(20, 10))

        language_var = tk.StringVar(value=get_user_language(username))
        language_options = ["fr", "en", "de", "es", "it", "ar", "zh-cn", "ru", "ja", "ko"]
        lang_menu = tk.OptionMenu(settings, language_var, *language_options)
        lang_menu.pack()

        def save_and_return():
            set_user_language(username, language_var.get())
            settings.destroy()
            open_chat(username)

        tk.Button(settings, text="Retour", command=save_and_return).pack(pady=15)


    def open_camera_window(username, chat_window, receiver):
        chat_window.destroy()

        cam_win = tk.Toplevel()
        cam_win.title("Prendre une photo")
        cam_win.geometry("500x440")
        cam_win.configure(bg="#e4e6eb")

        preview_label = tk.Label(cam_win)
        preview_label.pack(pady=10)

        cap = cv2.VideoCapture(0)
        if not cap.isOpened():
            messagebox.showerror("Erreur", "Impossible d'accéder à la caméra.")
            cam_win.destroy()
            open_chat(username)
            return

        running = True

        def show_preview():
            while running:
                ret, frame = cap.read()
                if ret:
                    frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                    img = Image.fromarray(frame_rgb)
                    img.thumbnail((400, 300))
                    imgtk = ImageTk.PhotoImage(img)
                    preview_label.imgtk = imgtk
                    preview_label.configure(image=imgtk)
                else:
                    break
                preview_label.update()

        threading.Thread(target=show_preview, daemon=True).start()

        def take_picture():
            nonlocal running
            running = False
            ret, frame = cap.read()
            cap.release()

            if not ret:
                messagebox.showerror("Erreur", "Capture échouée.")
                cam_win.destroy()
                open_chat(username)
                return

            _, buffer = cv2.imencode('.png', frame)
            image_bytes = buffer.tobytes()

            pub_receiver = get_public_key(receiver)
            pub_self = get_public_key(username)

            img_recv, key_recv, iv_recv = encrypt_binary_hybrid(image_bytes, pub_receiver)
            img_self, key_self, iv_self = encrypt_binary_hybrid(image_bytes, pub_self)

            save_image(username, receiver, img_recv, key_recv, iv_recv, img_self, key_self, iv_self)

            messagebox.showinfo("Succès", "Image envoyée.")
            cam_win.destroy()
            open_chat(username)

        tk.Button(cam_win, text="📸 Prendre la photo", command=take_picture, bg="#0084ff", fg="white", font=("Helvetica", 12)).pack(pady=5)
        tk.Button(cam_win, text="Retour", command=lambda: (cap.release(), cam_win.destroy(), open_chat(username)), font=("Helvetica", 10)).pack(pady=5)

    def open_chat(username):
        last_messages = []
        current_dest = None
        last_loaded = None


        chat = tk.Toplevel()
        chat.title(f"Messagerie - {username}")
        chat.geometry("840x480")
        chat.configure(bg="#e4e6eb")

        top_menu = tk.Frame(chat, bg="#e4e6eb")
        top_menu.pack(fill="x", padx=10, pady=5)
        tk.Button(top_menu, text="Paramètres", command=lambda: (chat.destroy(), open_settings(username)), bg="#d0d0d0").pack(side="right")

        frame_left = tk.Frame(chat, width=250, bg="#ffffff", bd=2, relief="solid")
        frame_left.pack(side="left", fill="y")

        tk.Label(frame_left, text="Discussions", font=("Helvetica", 14, "bold"), bg="#ffffff").pack(pady=10)

        users_listbox = tk.Listbox(frame_left, font=("Helvetica", 12), bd=0, bg="#f0f2f5")
        users_listbox.pack(fill="both", expand=True, padx=5, pady=5)

        frame_right = tk.Frame(chat, bg="#e4e6eb")
        frame_right.pack(side="right", fill="both", expand=True)

        chat_area_frame = tk.Frame(frame_right, bg="#e4e6eb")
        chat_area_frame.pack(fill="both", expand=True)

        canvas = tk.Canvas(chat_area_frame, bg="#e4e6eb", bd=0)
        scrollbar = tk.Scrollbar(chat_area_frame, orient="vertical", command=canvas.yview)
        chat_frame = tk.Frame(canvas, bg="#e4e6eb")

        chat_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=chat_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        bottom_frame = tk.Frame(frame_right, bg="#e4e6eb")
        bottom_frame.pack(fill="x", padx=10, pady=10)

        tk.Button(
            bottom_frame,
            text="📷",
            command=lambda: (
                open_camera_window(username, chat, users_listbox.get(users_listbox.curselection()[0]))
                if users_listbox.curselection() else messagebox.showerror("Erreur", "Sélectionnez un destinataire")
            ),
            bg="#cccccc",
            font=("Helvetica", 12)
        ).pack(side="left", padx=(0, 10))

        entry_msg = tk.Entry(bottom_frame, font=("Helvetica", 12), bg="white", relief="solid")
        entry_msg.pack(side="left", fill="x", expand=True, padx=(0, 10), ipady=6)


        def inserer_message_invisible_si_nouveau(user1, user2):
            messages = get_messages(user1, user2)
            if not messages:
                invisible_text = "sdlfjqmlsdjf sdj fmlsqdj mflsdj lmsdqj fmldsjf mlsqdkjf lmsqdjf lmkqdsjf mlqdskjf mlsqdkjf mlksqkjd"
                pub1 = get_public_key(user1)
                pub2 = get_public_key(user2)

                encrypted1 = encrypt_message(pub1, invisible_text)
                encrypted2 = encrypt_message(pub2, invisible_text)

                save_message(user1, user2, encrypted2, encrypted1)




        def afficher_image_en_grand(image_source):
            chat_area_frame.pack_forget()
            bottom_frame.pack_forget()
            grand_frame = tk.Frame(frame_right, bg="#000000")
            grand_frame.pack(fill="both", expand=True)

            if isinstance(image_source, str):
                img = Image.open(image_source)
            else:
                img = Image.open(image_source)

            img.thumbnail((800, 600))
            img_tk = ImageTk.PhotoImage(img)

            img_label = tk.Label(grand_frame, image=img_tk, bg="black")
            img_label.image = img_tk
            img_label.pack(expand=True)

            btn_fermer = tk.Button(grand_frame, text="X", command=lambda: (
                grand_frame.destroy(),
                chat_area_frame.pack(fill="both", expand=True),
                bottom_frame.pack(fill="x", padx=10, pady=10)
            ), font=("Arial", 12, "bold"), bg="red", fg="white")
            btn_fermer.place(x=5, y=5)



        def afficher_message(sender, msg, is_self=False):
            heure = datetime.now().strftime("%H:%M")
            bubble = tk.Frame(chat_frame, bg="#e4e6eb", pady=2)

            msg_original = msg
            msg_traduit = None

            if not msg.startswith("sdlfjqmlsdjf") and len(msg) > 300:  # heuristique simple pour images
                try:
                    decrypted_data = decrypt_image_base64_hybrid(msg, load_private_key(username))
                    image = Image.open(io.BytesIO(decrypted_data))
                    image.thumbnail((150, 150))
                    img_tk = ImageTk.PhotoImage(image)

                    def on_click_image(event):
                        afficher_image_en_grand(io.BytesIO(decrypted_data))

                    label = tk.Label(bubble, image=img_tk, cursor="hand2")
                    label.image = img_tk
                    label.bind("<Button-1>", on_click_image)
                    label.pack(anchor="e" if is_self else "w", padx=12)
                except Exception as e:
                    tk.Label(bubble, text=f"[Erreur image] {e}").pack(anchor="w", padx=12)

            else:
                if msg_original.strip().startswith("sdlfjqmlsdjf"):

                    invisible_label = tk.Label(
                        bubble,
                        text=msg_original,
                        font=("Helvetica", 11),
                        wraplength=300,
                        padx=12,
                        pady=8,
                        justify="left",
                        bg="blue",  # même couleur que l'arrière-plan
                        fg="blue",  # même couleur pour rendre le texte invisible
                        bd=0,
                        relief="flat"
                    )

                else:
                    if msg_original.strip() == "hello this is the default message that sends":
                        # Invisible default message at the top (same as chat background)
                        label = tk.Label(
                            bubble,
                            text=msg_original,
                            font=("Helvetica", 11),
                            wraplength=300,
                            padx=12,
                            pady=8,
                            justify="left",
                            bg="#e4e6eb",  # same as chat background
                            fg="#e4e6eb",  # text same as background
                            bd=0,
                            relief="flat"
                        )
                        label.pack(anchor="w", padx=12)
                    else:
                        # Normal text message
                        label = tk.Label(
                            bubble,
                            text=f"{msg_original}\n{heure}",
                            font=("Helvetica", 11),
                            wraplength=300,
                            padx=12,
                            pady=8,
                            justify="right" if is_self else "left",
                            bg="#0084ff" if is_self else "#f0f2f5",
                            fg="white" if is_self else "black",
                            bd=0,
                            relief="flat"
                        )
                        label.configure(
                            highlightbackground="#0084ff" if is_self else "#f0f2f5",
                            highlightcolor="#0084ff" if is_self else "#f0f2f5"
                        )

                        if is_self:
                            label.pack(anchor="e", padx=(300, 12))
                        else:
                            label.pack(anchor="w", padx=(12, 5), side="left")

                            def toggle_translation():
                                nonlocal msg_traduit
                                if translate_btn["text"] == "Traduire":
                                    msg_traduit = traduire_message(msg_original)
                                    label.config(text=f"{msg_traduit}\n{heure}")
                                    translate_btn.config(text="Original")
                                else:
                                    label.config(text=f"{msg_original}\n{heure}")
                                    translate_btn.config(text="Traduire")

                            translate_btn = tk.Button(
                                bubble, text="Traduire", font=("Helvetica", 8),
                                command=toggle_translation, bg="#d0d0d0", relief="flat"
                            )
                            translate_btn.pack(side="left", padx=(0, 5))

                    label.configure(
                        highlightbackground="#0084ff" if is_self else "#f0f2f5",
                        highlightcolor="#0084ff" if is_self else "#f0f2f5"
                    )

                    if is_self:
                        label.pack(anchor="e", padx=(300, 12))
                    else:
                        label.pack(anchor="w", padx=(12, 5), side="left")

                        def toggle_translation():
                            nonlocal msg_traduit
                            if translate_btn["text"] == "Traduire":
                                msg_traduit = traduire_message(msg_original)
                                label.config(text=f"{msg_traduit}\n{heure}")
                                translate_btn.config(text="Original")
                            else:
                                label.config(text=f"{msg_original}\n{heure}")
                                translate_btn.config(text="Traduire")

                        translate_btn = tk.Button(
                            bubble, text="Traduire", font=("Helvetica", 8),
                            command=toggle_translation, bg="#d0d0d0", relief="flat"
                        )
                        translate_btn.pack(side="left", padx=(0, 5))


            bubble.pack(fill="x", anchor="e" if is_self else "w", pady=4)
            canvas.update_idletasks()
            canvas.yview_moveto(1)


        def traduire_message(msg):
            try:
                lang = get_user_language(username)
                return GoogleTranslator(source='auto', target=lang).translate(msg)
            except Exception as e:
                return f"Erreur : {e}"

        def charger_utilisateurs():
            users_listbox.delete(0, tk.END)
            for user in get_all_users():
                if user != username:
                    users_listbox.insert(tk.END, user)

        def charger_discussion(dest):
            nonlocal current_dest, last_messages
            current_dest = dest
            last_messages = None

            inserer_message_invisible_si_nouveau(username, dest)  # insère si nécessaire
            chat.after(100, actualiser_discussion)  # on laisse un petit délai



        def actualiser_discussion():
            nonlocal last_messages, current_dest, last_loaded
            if not current_dest:
                return

            private_key = load_private_key(username)
            messages = get_messages(username, current_dest)

            # Comparer avec la dernière version chargée
            if last_loaded == messages:
                chat.after(2000, actualiser_discussion)
                return

            last_loaded = messages

            if last_messages is None or messages != last_messages:
                for widget in chat_frame.winfo_children():
                    widget.destroy()

                message_invisible = None
                messages_visibles = []

                for sender, receiver, enc_recv, enc_send in messages:
                    try:
                        decrypted = decrypt_message(private_key, enc_recv if receiver == username else enc_send)

                        if decrypted.strip().startswith("sdlfjqmlsdjf") and sender == username:
                            message_invisible = (sender, decrypted)
                        else:
                            messages_visibles.append((sender, decrypted))
                    except Exception as e:
                        print(f"Erreur déchiffrement: {e}")

                # ➕ Message par défaut affiché en haut
                # ➕ Message par défaut affiché en haut (invisible style)
                # ➕ Message par défaut affiché en haut (invisible style)
                afficher_message("__DEFAULT__", "hello this is the default message that sends", is_self=True)


                # ➕ Message "invisible" ensuite (si existant)
                if message_invisible:
                    afficher_message(message_invisible[0], message_invisible[1], is_self=True)

                # ➕ Affichage des autres messages
                for sender, msg in messages_visibles:
                    afficher_message(sender, msg, is_self=(sender == username))
            # Afficher les images stockées dans la BDD
            images = get_images(username, current_dest)
            for img in images:
                sender, receiver = img[0], img[1]

                # Choisir la bonne partie à déchiffrer selon l'utilisateur
                if username == receiver:
                    key_enc = img[2]
                    iv_enc = img[3]
                    data_enc = img[4]
                else:
                    key_enc = img[5]
                    iv_enc = img[6]
                    data_enc = img[7]

                try:
                    decrypted = decrypt_binary_hybrid(data_enc, key_enc, iv_enc, private_key)
                    image = Image.open(io.BytesIO(decrypted))
                    image.thumbnail((150, 150))
                    img_tk = ImageTk.PhotoImage(image)

                    def on_click_image(event, img=decrypted):
                        afficher_image_en_grand(io.BytesIO(img))

                    bubble = tk.Frame(chat_frame, bg="#e4e6eb", pady=2)
                    label = tk.Label(bubble, image=img_tk, cursor="hand2")
                    label.image = img_tk
                    label.bind("<Button-1>", on_click_image)
                    label.pack(anchor="e" if sender == username else "w", padx=12)
                    bubble.pack(fill="x", anchor="e" if sender == username else "w", pady=4)

                except Exception as e:
                    print(f"Erreur image : {e}")
            chat.after(2000, actualiser_discussion)



        def envoyer():
            msg = entry_msg.get()
            if not msg.strip():
                return
            selection = users_listbox.curselection()
            if not selection:
                messagebox.showerror("Erreur", "Sélectionnez un utilisateur.")
                return
            dest = users_listbox.get(selection[0])
            pub_dest = get_public_key(dest)
            pub_self = get_public_key(username)
            if not pub_dest or not pub_self:
                return
            encrypted_dest = encrypt_message(pub_dest, msg)
            encrypted_self = encrypt_message(pub_self, msg)
            save_message(username, dest, encrypted_dest, encrypted_self)
            afficher_message("Moi", msg, is_self=True)
            entry_msg.delete(0, tk.END)

        users_listbox.bind("<<ListboxSelect>>", lambda e: charger_discussion(users_listbox.get(users_listbox.curselection()[0])))
        tk.Button(bottom_frame, text="Envoyer", command=envoyer, bg="#0084ff", fg="white").pack(side="right")
        charger_utilisateurs()

    # Écran de connexion
    frame_login = tk.Frame(app, bg="#e4e6eb")
    tk.Label(frame_login, text="Connexion", font=("Arial", 16, "bold"), bg="#e4e6eb").pack(pady=10)
    login_user_entry = tk.Entry(frame_login)
    login_user_entry.pack(pady=5)
    login_pass_entry = tk.Entry(frame_login, show="*")
    login_pass_entry.pack(pady=5)
    tk.Button(frame_login, text="Connexion", command=lambda: (
        open_chat(login_user_entry.get()) if login_user(login_user_entry.get(), login_pass_entry.get()) else messagebox.showerror("Erreur", "Identifiants invalides")
    )).pack(pady=5)
    tk.Button(frame_login, text="S'inscrire", command=switch_to_register).pack()
    frame_login.pack(fill="both", expand=True)

    # Écran d'inscription
    frame_register = tk.Frame(app, bg="#e4e6eb")
    tk.Label(frame_register, text="Inscription", font=("Arial", 16, "bold"), bg="#e4e6eb").pack(pady=10)
    reg_user_entry = tk.Entry(frame_register)
    reg_user_entry.pack(pady=5)
    reg_pass_entry = tk.Entry(frame_register, show="*")
    reg_pass_entry.pack(pady=5)

    def try_register():
        username = reg_user_entry.get().strip()
        password = reg_pass_entry.get().strip()
        if not username or not password:
            messagebox.showerror("Erreur", "Champs vides.")
            return
        if register_user(username, password):
            messagebox.showinfo("Succès", "Compte créé.")
            switch_to_login()
        else:
            messagebox.showerror("Erreur", "Nom déjà utilisé.")

    tk.Button(frame_register, text="S'inscrire", command=try_register).pack(pady=5)
    tk.Button(frame_register, text="Retour", command=switch_to_login).pack()

    app.mainloop()
