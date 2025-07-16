
import customtkinter as ctk
from tkinter import messagebox, filedialog, StringVar
from PIL import Image, ImageTk
import os, sys, subprocess, gdown, zipfile, threading, json
from functools import partial

# ---- Appearance ----
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("dark-blue")

# ---- Path Helpers ----
def get_base_path():
    if getattr(sys, 'frozen', False):
        return os.path.dirname(sys.executable)
    return os.path.abspath(os.path.dirname(__file__))

def get_asset_path(name):    return os.path.join(get_base_path(), 'game', 'assets', name)
def get_rom_path(name):      return os.path.join(get_base_path(), 'roms', name)
def get_emulator_path(name): return os.path.join(get_base_path(), 'game', name)
def get_capa_path(name):     return os.path.join(get_base_path(), 'capas', name)
def get_config_path(name):   return os.path.join(get_base_path(), 'config', name)

# ---- Download remote JSON ----
json_drive_link = (
    "https://drive.google.com/file/d/17pQFo23A_EzoY1-DhkrCW-RD9HY0SpHp/view?usp=drive_link"
)
def gerar_link_direct(link):
    try:
        file_id = link.split("/d/")[1].split("/")[0]
        return f"https://drive.google.com/uc?id={file_id}"
    except:
        return None

def baixar_json_jogos():
    os.makedirs(get_config_path(''), exist_ok=True)
    destino = get_config_path("jogos.json")
    direct = gerar_link_direct(json_drive_link)
    try:
        gdown.download(direct, destino, quiet=True, fuzzy=True)
    except:
        print("Aviso: falha ao baixar JSON remoto, usando local se existir.")
    try:
        with open(destino, 'r', encoding='utf-8') as f:
            return json.load(f)
    except:
        return []

jogos_remotos = baixar_json_jogos()

# ---- ePSXe HLE config ----
def verificar_ou_criar_cfg_hle():
    cfg = get_emulator_path('epsxe001.cfg')
    if not os.path.exists(cfg):
        with open(cfg, 'w') as f:
            f.write('1\nepsxe -nogui\n!Runbios HLE\n!Fullscreen 1\n')

# ---- Local games ----
jogos = []
imagens = []

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

# ---- Actions ----
def configurar_controles():
    try:
        subprocess.Popen(get_emulator_path("epsxe.exe"), shell=True)
    except Exception as e:
        messagebox.showerror("Erro", f"Não foi possível abrir o emulador:\n{e}")

def atualizar_lista():
    for widget in game_frame.winfo_children():
        widget.destroy()
    carregar_jogos()

def carregar_jogos():
    global jogos, imagens
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

def editar_capa(title):
    arquivo = filedialog.askopenfilename(filetypes=[('Imagens','*.png *.jpg *.jpeg')])
    if arquivo:
        try:
            img = Image.open(arquivo).convert('RGB')
            img.save(get_capa_path(f"{title}.png"))
            carregar_jogos()
            if drawer_visible:
                build_drawer()
        except Exception as e:
            messagebox.showerror('Erro', f'Falha ao editar capa:\n{e}')

# ---- Remote download drawer ----
drawer_visible = False

def baixar_jogo_remoto(jogo, status_lbl, btn):
    def worker():
        status_lbl.configure(text='Baixando...')
        try:
            link = gerar_link_direct(jogo['link'])
            zipout = get_rom_path(f"{jogo['nome']}.zip")
            gdown.download(link, zipout, quiet=True)
            with zipfile.ZipFile(zipout, 'r') as z:
                for info in z.infolist():
                    ext = os.path.splitext(info.filename)[1].lower()
                    dest = (get_rom_path(info.filename) if ext in ['.bin','.iso','.img','.cue']
                            else get_capa_path(info.filename))
                    with z.open(info) as src, open(dest, 'wb') as dst:
                        dst.write(src.read())
            os.remove(zipout)
            status_lbl.configure(text='Concluído!')
            btn.configure(state='disabled', image=icon_check)
            carregar_jogos()
            if drawer_visible:
                build_drawer()
        except Exception as e:
            status_lbl.configure(text=f'Erro: {e}')
    threading.Thread(target=worker, daemon=True).start()

# ---- UI Setup ----
root = ctk.CTk()
root.title('One Launcher')
W, H = 1000, 800
SW, SH = root.winfo_screenwidth(), root.winfo_screenheight()
root.geometry(f"{W}x{H}+{(SW-W)//2}+{(SH-H)//2}")

verificar_ou_criar_cfg_hle()

# ---- Icons loader ----
def load_icon(name, size=(24,24)):
    try:
        img = Image.open(get_asset_path(name)).resize(size)
        return ImageTk.PhotoImage(img)
    except:
        return None

icon_download = load_icon('icon_download.png',(32,32))
icon_refresh  = load_icon('icon_refresh.png',(32,32))
icon_config   = load_icon('icon_settings.png',(32,32))
icon_search   = load_icon('icon_search.png', (32,32))
icon_logo     = load_icon('icone.png', (32,32))
icon_check    = load_icon('icon_check.png',(40,40))
icon_edit     = load_icon('icon_edit.png', (20,20))


# ---- Layout ----
main = ctk.CTkFrame(root, fg_color='#1e1e1e')
main.pack(fill='both', expand=True)
content = ctk.CTkFrame(main, fg_color='#1e1e1e')
content.pack(side='left', fill='both', expand=True)
drawer = ctk.CTkFrame(main, fg_color='#121212', width=600)
drawer.pack_propagate(False)

# ---- Icon Buttons ----

def create_icon_button(icon, command):
    btn = ctk.CTkLabel(header, text="", image=icon, fg_color="transparent", cursor="hand2")
    btn.pack(side="right", padx=5)
    btn.bind("<Button-1>", lambda e: command())
    return btn

# ---- Drawer build/toggle ----
search_drawer = StringVar()

def build_drawer():
    
    for w in drawer.winfo_children():
        w.destroy()

    ctk.CTkLabel(
    drawer,
    text="Loja de Jogos",
    font=("Segoe UI", 18, "bold"),
    text_color="white"
    ).pack(pady=(16, 0))
    # Barra de busca no drawer
    search_wrapper = ctk.CTkFrame(drawer, corner_radius=20, fg_color="#2f2f2f", width=260, height=32)
    search_wrapper.pack(padx=10, pady=(16, 8))

    # Ícone de lupa
    ctk.CTkLabel(search_wrapper, text="", image=icon_search, fg_color="transparent", width=24).pack(
        side="left", padx=(10, 0), pady=4
    )

    # Campo de busca
    search_var_drawer = StringVar()
    search_entry = ctk.CTkEntry(
        master=search_wrapper,
        textvariable=search_var_drawer,
        placeholder_text="Buscar jogo...",
        font=("Segoe UI", 14),
        text_color="white",
        placeholder_text_color="#aaaaaa",
        border_color="#2f2f2f",
        fg_color="#2f2f2f",
        border_width=0,
        width=400,
        height=30
    )
    search_entry.pack(side="left", padx=(6, 8), pady=4, fill="x", expand=True)
   
    # Área de listagem
    frame_scroll = ctk.CTkScrollableFrame(drawer, fg_color="#121212", corner_radius=12)
    frame_scroll.pack(fill='both', expand=True, padx=10, pady=5)

    # Detecta quais jogos já existem localmente
    roms_existentes = set()
    for arquivo in os.listdir(get_rom_path('')):
        nome, ext = os.path.splitext(arquivo)
        if ext.lower() in [".bin", ".iso", ".img", ".cue"]:
            roms_existentes.add(nome)

    # Renderiza lista de jogos filtrados
    def renderizar_lista(jogos_filtrados):
        for widget in frame_scroll.winfo_children():
            widget.destroy()

        for jogo in jogos_filtrados:
            nome_formatado = jogo["nome"]

            linha = ctk.CTkFrame(frame_scroll, fg_color="#222222", corner_radius=8, height=60)
            linha.pack(fill="x", pady=8, padx=10)
            linha.pack_propagate(False)

            ctk.CTkLabel(linha, text=jogo["nome"], font=("Segoe UI", 14, "bold"), anchor="w").pack(
                side="left", padx=15
            )

            container = ctk.CTkFrame(linha, fg_color="transparent")
            container.pack(side="left", padx=10)

            status = ctk.CTkLabel(container, text="", anchor="w", font=("Segoe UI", 12))
            progress = ctk.CTkProgressBar(container, mode="indeterminate", height=5, width=140)

            def baixar_jogo(j=jogo, s=status, p=progress, b=None):
                def thread_func():
                    linha.after(0, lambda: (s.pack_forget(), p.pack(pady=4)))
                    p.start()
                    try:
                        direct_link = gerar_link_direct(j["link"])
                        destino = get_rom_path(f"{nome_formatado}.zip")
                        gdown.download(direct_link, destino, quiet=False)

                        if destino.endswith(".zip"):
                            with zipfile.ZipFile(destino, 'r') as zip_ref:
                                for file_info in zip_ref.infolist():
                                    filename = file_info.filename
                                    ext = os.path.splitext(filename)[1].lower()
                                    if ext in [".bin", ".iso", ".img", ".cue"]:
                                        target_path = get_rom_path(os.path.basename(filename))
                                    elif ext in [".png", ".jpg", ".jpeg"]:
                                        target_path = get_capa_path(os.path.basename(filename))
                                    else:
                                        continue
                                    with zip_ref.open(file_info) as source, open(target_path, "wb") as f_out:
                                        f_out.write(source.read())
                            os.remove(destino)

                        linha.after(0, lambda: (
                            p.stop(), p.pack_forget(),
                            s.configure(text="Concluído!"),
                            s.pack(pady=4),
                            b.configure(state="disabled", image=icon_check),
                            carregar_jogos()
                        ))
                    except Exception as e:
                        linha.after(0, lambda: (
                            p.stop(), p.pack_forget(),
                            s.configure(text=f"Erro: {e}"),
                            s.pack(pady=4)
                        ))

                threading.Thread(target=thread_func, daemon=True).start()

            if nome_formatado in roms_existentes:
                btn = ctk.CTkButton(linha, text="", image=icon_check, width=40, height=28, fg_color="transparent", state="disabled")
            else:
                btn = ctk.CTkButton(linha, text="", image=icon_download, width=40, height=28, fg_color="transparent")
                btn.configure(command=lambda j=jogo, s=status, p=progress, b=btn: baixar_jogo(j, s, p, b))

            btn.pack(side="right", padx=5)
            status.pack(pady=4)

    # Refina a busca conforme digitação
    def filtrar_jogos_download(*args):
        termo = search_var_drawer.get().lower()
        jogos_filtrados = [j for j in jogos_remotos if termo in j["nome"].lower()]
        renderizar_lista(jogos_filtrados)

    search_var_drawer.trace_add("write", filtrar_jogos_download)
    renderizar_lista(jogos_remotos)

def toggle_drawer():
    global drawer_visible
    if drawer_visible:
        drawer.pack_forget()
    else:
        drawer.pack(side='right', fill='y')
        build_drawer()
    drawer_visible = not drawer_visible

# ---- Header ----
header = ctk.CTkFrame(content, fg_color='#1e1e1e')
header.pack(fill='x', padx=5, pady=20)

create_icon_button(icon_config, configurar_controles)
create_icon_button(icon_refresh, atualizar_lista)
create_icon_button(icon_download, toggle_drawer)
# ---- Local search ----
search_var = StringVar()
sw2 = ctk.CTkFrame(
    header,
    fg_color='#2f2f2f',
    corner_radius=20,
    width=400,
    height=40
)
sw2.pack_propagate(False)
sw2.pack(side='left', padx=10)

# Ícone da lupa com margem à esquerda
ctk.CTkLabel(
    sw2,
    text='',
    image=icon_search,
    fg_color='transparent',
    width=30
).pack(side='left', padx=(10, 0))

# Campo de entrada com preenchimento e sem colar nas bordas
ctk.CTkEntry(
    sw2,
    textvariable=search_var,
    placeholder_text='Buscar...',
    font=('Segoe UI', 14),
    text_color='white',
    placeholder_text_color='#aaaaaa',
    border_color='#2f2f2f',
    fg_color='#2f2f2f',
    border_width=0
).pack(side='left', fill='both', expand=True, padx=(6, 10), pady=6)

if icon_logo:
    ctk.CTkLabel(header, text='', image=icon_logo, fg_color='transparent').pack(side='left', padx=(5,0))

# ---- Games grid ----
ctk.CTkLabel(content, text='Jogos', font=('Segoe UI',16,'bold'), text_color='white').pack(anchor='w', padx=20, pady=(10,10))
game_frame = ctk.CTkFrame(content, fg_color='#1e1e1e')
game_frame.pack(fill='both', expand=True, padx=10, pady=(0,5))

def exibir_jogos(lista):
    global jogos, imagens
    jogos = lista
    imagens = []
    for w in game_frame.winfo_children(): w.destroy()
    scroll2 = ctk.CTkScrollableFrame(game_frame, fg_color='#121212')
    scroll2.pack(fill='both', expand=True)

    mold = Image.open(get_asset_path('moldura_transparente.png')).convert('RGBA').resize((100,110), Image.LANCZOS)
    ix, iy = 5, 0
    iw, ih = 90, 100

    if not lista:
        ctk.CTkLabel(scroll2, text='Nenhum jogo encontrado!', font=('Segoe UI',16,'bold'), text_color='gray').pack(pady=50)
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

        frm = ctk.CTkFrame(scroll2, fg_color='#121212', corner_radius=8)
        frm.grid(row=idx//4, column=idx%4, padx=8, pady=8)

        btn = ctk.CTkButton(frm, image=tkimg, text=item['title'], compound='top', fg_color='#121212',
                            width=100, height=140, text_color='white', font=('Segoe UI',12,'bold'), hover_color='#2a2a3d',
                            command=lambda i=idx: selecionar_jogo(i))
        btn.pack()
        edit_btn = ctk.CTkButton(frm, image=icon_edit, text='', fg_color='transparent', width=20, height=20,
                                 command=lambda t=item['title']: editar_capa(t))
        edit_btn.place(x=76, y=4)

search_var.trace_add('write', lambda *_: exibir_jogos([j for j in encontrar_jogos() if search_var.get().lower() in j['title'].lower()]))
carregar_jogos()

# ---- Footer ----
ctk.CTkLabel(root, text='Created by Thiago Aciole © 2025', text_color='#aaaaaa', font=('Segoe UI',12)).pack(side='bottom', pady=5)
root.mainloop()
