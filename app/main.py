# app/main.py
import tkinter as tk
from app.ui.login_frame import show_login

def main():
    root = tk.Tk()
    from app.theme import setup_styles
    setup_styles()
    root.title("Phần mềm quản lý quán cà phê")
    root.geometry("900x600")
    root.configure(bg="#f5f0e1")

    show_login(root)
    root.mainloop()

if __name__ == "__main__":
    main()