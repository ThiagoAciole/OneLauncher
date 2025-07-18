import customtkinter as ctk
from tkinter import StringVar, messagebox
from PIL import Image, ImageTk
import os, subprocess
from tkinter import filedialog

from utils import (
    get_asset_path, get_rom_path, get_capa_path,
    get_emulator_path, load_icons
)
import drawer as drawer_module

jogos = []
imagens = []
root = None
game_frame = None
icon_download = icon_refresh = icon_config = icon_search = icon_logo = icon_check = icon_edit = None

def configurar_controles():
    try:
        subprocess.Popen(get_emulator_path("epsxe.exe"), shell=True)
    except Exception as e:
        messagebox.showerror("Erro", f"Não foi possível abrir o emulador:\n{e}")

def encontrar_jogos():
    os.makedirs(get_rom_path(''), exist_ok=True)
    lista = []
    for f in os.listdir(get_rom_path('')):
        if f.lower().endswith(('.bin', '.iso', '.img', '.cue')):
            title = os.path.splitext(f)[0]
            capa = f"{title}.png"
            if not os.path.isfile(get_capa_path(capa)):
                capa = 'default.png'
            lista.append({'title': title, 'file': f, 'image': capa})
    return lista

def carregar_jogos():
    global jogos
    jogos = encontrar_jogos()
    exibir_jogos(jogos)

def selecionar_jogo(idx):
    try:
        j = jogos[idx]
        exe = get_emulator_path('epsxe.exe')
        path = get_rom_path(j['file'])
        args = [exe, '-nogui']
        ext = os.path.splitext(path)[1].lower()
        args += ['-loadiso', path] if ext == '.iso' else ['-loadbin', path]
        subprocess.Popen(args, shell=True)
        root.destroy()
    except Exception as e:
        messagebox.showerror('Erro ao iniciar jogo', str(e))



def exibir_jogos(lista):
    global imagens
    imagens = []
    for w in game_frame.winfo_children():
        w.destroy()

    scroll = ctk.CTkScrollableFrame(game_frame, fg_color='#121212')
    scroll.pack(fill='both', expand=True)

    mold = Image.open(get_asset_path('moldura_transparente.png')).convert('RGBA').resize((100,110), Image.LANCZOS)
    ix, iy = 5, 0
    iw, ih = 90, 100

    if not lista:
        ctk.CTkLabel(scroll, text='Nenhum jogo encontrado!', font=('Segoe UI',16,'bold'), text_color='gray').pack(pady=50)
        return

    for idx, item in enumerate(lista):
        try:
            img = Image.open(get_capa_path(item['image'])).convert('RGBA')
            scale = max(iw/img.width, ih/img.height)
            sz = (int(img.width*scale), int(img.height*scale))
            crop = img.resize(sz, Image.LANCZOS).crop(((sz[0]-iw)//2,(sz[1]-ih)//2,(sz[0]-iw)//2+iw,(sz[1]-ih)//2+ih))
            canvas = Image.new('RGBA', (100,110), (0,0,0,0))
            canvas.paste(crop, (ix,iy))
            canvas.paste(mold, (0,0), mask=mold)
        except:
            canvas = mold.copy()

        tkimg = ImageTk.PhotoImage(canvas)
        imagens.append(tkimg)

        frm = ctk.CTkFrame(scroll, fg_color='#121212', corner_radius=8, width=140, height=160)
        frm.grid(row=idx//4, column=idx%4, padx=10, pady=10)
        frm.pack_propagate(False) 

        # Botão com imagem e título
        btn = ctk.CTkButton(
            frm,
            image=tkimg,
            text=item['title'],
            compound='top',
            fg_color='#121212',
            width=100,
            height=140,
            text_color='white',
            font=('Segoe UI',12,'bold'),
            hover_color='#2a2a3d',
            command=lambda i=idx: selecionar_jogo(i)
        )
        btn.pack()

        # Botão de edição flutuante redondo
        edit_btn = ctk.CTkButton(
           master=frm,
            text='',
            image=icon_edit,
            width=24,
            height=28,
            corner_radius=14,
            fg_color="transparent",        # fundo normal (dark)
            hover_color="#3a3a3a",     # destaque no hover
            bg_color="transparent",    # não herda o fundo do pai
            border_width=0,
            cursor='hand2',
            command=lambda t=item['title']: editar_capa(t)
        )
        edit_btn.place(x=70, y=4)  


def editar_capa(title):
    arquivo = filedialog.askopenfilename(filetypes=[('Imagens','*.png *.jpg *.jpeg')])
    if arquivo:
        try:
            img = Image.open(arquivo).convert('RGB')
            img.save(get_capa_path(f"{title}.png"))
            carregar_jogos()
        except Exception as e:
            messagebox.showerror('Erro', f'Falha ao editar capa:\n{e}')

def start_home():
    global root, game_frame
    global icon_download, icon_refresh, icon_config, icon_search, icon_logo, icon_check, icon_edit

    root = ctk.CTk()
    root.title('One Launcher')
    W, H = 1000, 800
    SW, SH = root.winfo_screenwidth(), root.winfo_screenheight()
    root.geometry(f"{W}x{H}+{(SW-W)//2}+{(SH-H)//2}")



    icons = load_icons()
    icon_download = icons["download"]
    icon_refresh  = icons["refresh"]
    icon_config   = icons["config"]
    icon_search   = icons["search"]
    icon_logo     = icons["logo"]
    icon_check    = icons["check"]
    icon_edit     = icons["edit"]

    # Layout
    main = ctk.CTkFrame(root, fg_color='#1e1e1e')
    main.pack(fill='both', expand=True)

    content = ctk.CTkFrame(main, fg_color='#1e1e1e')
    content.pack(side='left', fill='both', expand=True)

    drawer = ctk.CTkFrame(main, fg_color='#121212', width=600)
    drawer.pack_propagate(False)

    from drawer import inject_drawer
    inject_drawer(drawer, {
        "search": icon_search,
        "check": icon_check,
        "download": icon_download,
        "refresh": icon_refresh
    })

    # Header
    header = ctk.CTkFrame(content, fg_color='#1e1e1e')
    header.pack(fill='x', padx=5, pady=20)

    def create_icon_button(icon, command):
        btn = ctk.CTkLabel(header, text="", image=icon, fg_color="transparent", cursor="hand2")
        btn.pack(side="right", padx=5)
        btn.bind("<Button-1>", lambda e: command())

    create_icon_button(icon_config, configurar_controles)
    create_icon_button(icon_refresh, carregar_jogos)
    create_icon_button(icon_download, drawer_module.toggle_drawer)

    search_var = StringVar()
    sw2 = ctk.CTkFrame(header, fg_color='#2f2f2f', corner_radius=20, width=400, height=40)
    sw2.pack_propagate(False)
    sw2.pack(side='left', padx=10)

    ctk.CTkLabel(sw2, text='', image=icon_search, fg_color='transparent', width=30).pack(side='left', padx=(10, 0))
    ctk.CTkEntry(sw2, textvariable=search_var, placeholder_text='Buscar...', font=('Segoe UI', 14),
                 text_color='white', placeholder_text_color='#aaaaaa',
                 border_color='#2f2f2f', fg_color='#2f2f2f', border_width=0
                 ).pack(side='left', fill='both', expand=True, padx=(6, 10), pady=6)

    if icon_logo:
        ctk.CTkLabel(header, text='', image=icon_logo, fg_color='transparent').pack(side='left', padx=(5,0))

    ctk.CTkLabel(content, text='Jogos', font=('Segoe UI',16,'bold'), text_color='white').pack(anchor='w', padx=20, pady=(10,10))
    game_frame = ctk.CTkFrame(content, fg_color='#1e1e1e')
    game_frame.pack(fill='both', expand=True, padx=10, pady=(0,5))

    search_var.trace_add('write', lambda *_: exibir_jogos([j for j in encontrar_jogos() if search_var.get().lower() in j['title'].lower()]))
    carregar_jogos()

    ctk.CTkLabel(root, text='Created by Thiago Aciole © 2025', text_color='#aaaaaa', font=('Segoe UI',12)).pack(side='bottom', pady=5)
    root.mainloop()

