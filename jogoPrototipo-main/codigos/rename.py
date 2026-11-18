
import tkinter as tk
from tkinter import ttk
from PIL import Image, ImageTk

jogo = tk.Tk()
jogo.geometry("1980x1080")
jogo.title("Em busca da esperança")

# Carregar imagem de fundo
imagem = Image.open(r"C:\Users\RAFAELVICTORSOARESBI\.vscode\prototipo_jogo\.venv\c.png")
imagem = imagem.resize((1980, 1080))
fundo = ImageTk.PhotoImage(imagem)

# Configurar fundo
def configurar_tela(frame):
    label_fundo = tk.Label(frame, image=fundo)
    label_fundo.place(x=0, y=0, relwidth=1, relheight=1)
    label_fundo.lower()

# Comando para criação de telas em python
frame_tela1 = ttk.Frame(jogo)
frame_tela2 = ttk.Frame(jogo)

configurar_tela(frame_tela1)
configurar_tela(frame_tela2)

# Navegação entre telas
def mostrar_tela2():
    frame_tela1.pack_forget()
    frame_tela2.pack(fill="both", expand=True)

def mostrar_tela1():
    frame_tela2.pack_forget()
    frame_tela1.pack(fill="both", expand=True)

# Conteúdo da tela 1
ttk.Label(
    frame_tela1,
    text="Tela 1",
    font=("Arial", 14)
).pack(pady=20)

ttk.Button(
    frame_tela1,
    text="Ir para Tela 2",
    command=mostrar_tela2
).pack(pady=10)

# Conteúdo da tela 2
ttk.Label(
    frame_tela2,
    text="Tela 2",
    font=("Arial", 14)
).pack(pady=20)

ttk.Button(
    frame_tela2,
    text="Ir para Tela 1",
    command=mostrar_tela1
).pack(pady=10)

# Mostrar primeira tela
frame_tela1.pack(fill="both", expand=True)

jogo.mainloop()
