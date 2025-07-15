
import customtkinter as ctk
from tkinter import Canvas, messagebox
from PIL import Image, ImageTk
import os
import sys
import subprocess
import gdown
import zipfile
import tempfile
import threading

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("dark-blue")

def get_base_path():
    if getattr(sys, 'frozen', False):
        return os.path.dirname(sys.executable)
    return os.path.abspath(os.path.dirname(__file__))

def get_asset_path(filename):
    return os.path.join(get_base_path(), 'game', 'assets', filename)

def get_rom_path(filename):
    return os.path.join(get_base_path(), 'roms', filename)

def get_emulator_path(filename):
    return os.path.join(get_base_path(), 'game', filename)

def get_capa_path(filename):
    return os.path.join(get_base_path(), 'capas', filename)

def carregar_lista_jogos_remota():
    try:
        pasta_drive_id = "19xDDredXpO1XVAhCioHSSSNSME8ieX0-"
        destino_roms = get_rom_path('')

        if not os.path.exists(destino_roms):
            os.makedirs(destino_roms)

        # Cria pasta temporária (evita criar ps1 dentro de roms)
        with tempfile.TemporaryDirectory() as temp_dir:
            gdown.download_folder(
                id=pasta_drive_id,
                output=temp_dir,
                quiet=False,
                use_cookies=False
            )

            # Move e extrai arquivos direto na raiz de 'roms'
            for arquivo in os.listdir(temp_dir):
                src_path = os.path.join(temp_dir, arquivo)
                dst_path = os.path.join(destino_roms, arquivo)

                # Copia para pasta roms
                os.rename(src_path, dst_path)

                # Se for zip, extrai e remove
                if dst_path.endswith(".zip"):
                    with zipfile.ZipFile(dst_path, 'r') as zip_ref:
                        zip_ref.extractall(destino_roms)
                    os.remove(dst_path)

    except Exception as e:
        messagebox.showerror("Erro", f"Erro ao baixar ou extrair jogos:\n{e}")


def verificar_ou_criar_cfg_hle():
    cfg_path = get_emulator_path("epsxe001.cfg")
    if not os.path.exists(cfg_path):
        conteudo_cfg = "1\nepsxe -nogui\n!Runbios HLE\n!Fullscreen 1\n"
        with open(cfg_path, "w") as f:
            f.write(conteudo_cfg)

def encontrar_jogos():
    jogos = []
    rom_dir = get_rom_path('')
    if not os.path.exists(rom_dir):
        os.makedirs(rom_dir)
    for arquivo in os.listdir(rom_dir):
        if arquivo.lower().endswith(('.bin', '.iso', '.cue', '.img')):
            nome_jogo = os.path.splitext(arquivo)[0]
            capa = f"{nome_jogo}.png"
            capa_path = get_capa_path(capa)
            if not os.path.isfile(capa_path):
                capa = "default.png"
            jogos.append({"title": nome_jogo, "image": capa, "file": arquivo})
    return jogos

def selecionar_jogo(index):
    jogo = jogos[index]
    try:
        epsxe_path = get_emulator_path("epsxe.exe")
        game_file = get_rom_path(jogo["file"])
        args = [epsxe_path, "-nogui"]
        args += ["-loadiso", game_file] if jogo["file"].lower().endswith(".iso") else ["-loadbin", game_file]
        subprocess.Popen(args, shell=True)
        root.destroy()
    except Exception as e:
        messagebox.showerror("Erro ao iniciar o jogo", str(e))

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

def exibir_jogos(lista_jogos):
    global imagens
    imagens = []

    for widget in game_frame.winfo_children():
        widget.destroy()

    if not lista_jogos:
        sem_jogos_label = ctk.CTkLabel(game_frame, text="Nenhum jogo encontrado!", font=("Segoe UI", 16, "bold"), text_color="gray")
        sem_jogos_label.pack(pady=50)
        return

    for idx, jogo in enumerate(lista_jogos):
        img_path = get_capa_path(jogo["image"])
        try:
            img = Image.open(img_path).resize((64, 64))
        except:
            img = Image.open(get_asset_path("default.png")).resize((64, 64))

        img_tk = ImageTk.PhotoImage(img)
        imagens.append(img_tk)

        frame_item = ctk.CTkFrame(game_frame, fg_color="#1e1e1e", corner_radius=8)
        titulo_quebrado = '\n'.join(jogo["title"].split()[:3])

        btn = ctk.CTkButton(
            frame_item, image=img_tk, text=titulo_quebrado, compound="top",
            width=80, height=100, fg_color="#1e1e1e", text_color="white",
            font=("Segoe UI", 12, "bold"), hover_color="#2a2a3d",
            command=lambda i=jogos.index(jogo): selecionar_jogo(i)
        )
        btn.pack()
        frame_item.grid(row=idx // 5, column=idx % 5, padx=10, pady=10)


def baixar_jogos_drive():
    def run():
        try:
            root.after(0, lambda: (
                progress_label.configure(text="Baixando jogos..."),
                progress_label.pack(side="bottom"),
                progress_bar.pack(side="bottom", fill="x", padx=10, pady=(0, 2)),
                progress_bar.start()
            ))

            carregar_lista_jogos_remota()

        except Exception as e:
            root.after(0, lambda: messagebox.showerror("Erro", f"Falha ao baixar jogos:\n{e}"))
        finally:
            root.after(0, lambda: (
                progress_bar.stop(),
                progress_bar.pack_forget(),
                progress_label.pack_forget(),
                atualizar_lista()
            ))

    threading.Thread(target=run, daemon=True).start()

verificar_ou_criar_cfg_hle()

root = ctk.CTk()
root.title("One Launcher")
root.geometry("530x520")

progress_bar = ctk.CTkProgressBar(root, mode="indeterminate", height=5)
progress_bar.set(0)
progress_label = ctk.CTkLabel(root, text="", font=("Segoe UI", 12), text_color="white")
try:
    root.iconbitmap(get_asset_path("icone.ico"))
except:
    pass

main_content = ctk.CTkFrame(root, fg_color="#1e1e1e")
main_content.pack(fill="both", expand=True)

header = ctk.CTkFrame(main_content, fg_color="#1e1e1e")
header.pack(fill="x", padx=10, pady=5)

def load_icon(name, size=(36, 36)):
    path = get_asset_path(name)
    try:
        img = Image.open(path).resize(size)
        return ImageTk.PhotoImage(img)
    except:
        return None

icon_refresh = load_icon("icon_refresh.png")
icon_config = load_icon("icon_settings.png")
icon_lupa = load_icon("icon_search.png", size=(28, 28))
icon_logo = load_icon("icone.png", size=(32, 32))
icon_download = load_icon("icon_download.png")

def create_icon_button(icon, command):
    btn = ctk.CTkLabel(header, text="", image=icon, fg_color="transparent", cursor="hand2")
    btn.pack(side="right", padx=5)
    btn.bind("<Button-1>", lambda e: command())
    return btn

create_icon_button(icon_config, configurar_controles)
create_icon_button(icon_refresh, atualizar_lista)
create_icon_button(icon_download, baixar_jogos_drive)

search_wrapper = ctk.CTkFrame(header, corner_radius=20, fg_color="#2f2f2f", width=260, height=32)
search_wrapper.pack(side="left", padx=10, pady=4)

lupa_label = ctk.CTkLabel(search_wrapper, text="", image=icon_lupa, fg_color="transparent", width=24)
lupa_label.pack(side="left", padx=(10, 0), pady=4)

search_var = ctk.StringVar()
search_entry = ctk.CTkEntry(
    master=search_wrapper,
    textvariable=search_var,
    placeholder_text="Buscar jogo...",
    font=("Segoe UI", 14),
    text_color="white",
    placeholder_text_color="#aaaaaa",
    border_color="#2f2f2f",
    fg_color="#2f2f2f",
    border_width=0,
    width=200,
    height=30
)
search_entry.pack(side="left", padx=(6, 8), pady=4, fill="x", expand=True)

if icon_logo:
    logo_label = ctk.CTkLabel(header, text="", image=icon_logo, fg_color="transparent")
    logo_label.pack(side="left", padx=(5, 0))

label_jogos = ctk.CTkLabel(main_content, text="Jogos", font=("Segoe UI", 16, "bold"), text_color="white")
label_jogos.pack(anchor="w", padx=20, pady=(5, 2))

def filtrar_jogos(*args):
    termo = search_var.get().lower()
    for widget in game_frame.winfo_children():
        widget.destroy()
    jogos_filtrados = [j for j in jogos if termo in j["title"].lower()]
    exibir_jogos(jogos_filtrados)

search_var.trace_add("write", filtrar_jogos)

game_frame = ctk.CTkFrame(main_content, fg_color="#1e1e1e")
game_frame.pack(fill="both", expand=True, padx=10, pady=(0, 5))

progress_bar = ctk.CTkProgressBar(root, mode="indeterminate", height=5)
progress_bar.set(0)
progress_label = ctk.CTkLabel(root, text="", font=("Segoe UI", 12), text_color="white")

footer = ctk.CTkLabel(root, text="Created by Thiago Aciole © 2025", text_color="#aaaaaa", font=("Segoe UI", 12))
footer.pack(side="bottom", pady=5)

carregar_jogos()

root.after(500, lambda: (
    baixar_jogos_drive() if len(jogos) == 0 and messagebox.askyesno("ROMs não encontradas", "Nenhuma ROM foi encontrada. Deseja baixar agora?") else None
))

root.mainloop()
