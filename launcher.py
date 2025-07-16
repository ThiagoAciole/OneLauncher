import customtkinter as ctk
from tkinter import Canvas, messagebox, filedialog
from PIL import Image, ImageTk, ImageDraw
import os
import sys
import subprocess
import gdown
import zipfile
import tempfile
import threading
import json

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("dark-blue")

# === Caminhos ===
def get_base_path():
    if getattr(sys, 'frozen', False):
        return os.path.dirname(sys.executable)
    return os.path.abspath(os.path.dirname(__file__))

def get_asset_path(filename): return os.path.join(get_base_path(), 'game', 'assets', filename)
def get_rom_path(filename): return os.path.join(get_base_path(), 'roms', filename)
def get_emulator_path(filename): return os.path.join(get_base_path(), 'game', filename)
def get_capa_path(filename): return os.path.join(get_base_path(), 'capas', filename)
def get_config_path(filename): return os.path.join(get_base_path(), 'config', filename)

# === Baixar JSON remoto ===
json_drive_link = "https://drive.google.com/file/d/17pQFo23A_EzoY1-DhkrCW-RD9HY0SpHp/view?usp=drive_link"
def gerar_link_direct(link):
    try:
        file_id = link.split("/d/")[1].split("/")[0]
        return f"https://drive.google.com/uc?id={file_id}"
    except:
        return None

def baixar_json_jogos():
    os.makedirs(get_config_path(''), exist_ok=True)
    destino = get_config_path("jogos.json")
    direct_link = gerar_link_direct(json_drive_link)
    try:
        gdown.download(direct_link, destino, quiet=True, fuzzy=True)
        print("Arquivo JSON atualizado com sucesso.")
    except Exception as e:
        print(f"[Aviso] Falha ao baixar JSON: {e}")
        if not os.path.exists(destino):
            print("[Erro crítico] Nenhum arquivo local encontrado. A lista de jogos ficará vazia.")
            return []

    try:
        with open(destino, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print(f"[Erro] Falha ao ler JSON local: {e}")
        return []

jogos_remotos = baixar_json_jogos()

def get_base_path():
    if getattr(sys, 'frozen', False):
        return os.path.dirname(sys.executable)
    return os.path.abspath(os.path.dirname(__file__))

def get_asset_path(filename): return os.path.join(get_base_path(), 'game', 'assets', filename)
def get_rom_path(filename): return os.path.join(get_base_path(), 'roms', filename)
def get_emulator_path(filename): return os.path.join(get_base_path(), 'game', filename)
def get_capa_path(filename): return os.path.join(get_base_path(), 'capas', filename)

# === Funções de Jogo ===
def abrir_janela_de_downloads():
    janela = ctk.CTkToplevel(root)
    janela.title("Baixar Jogos")
    janela.geometry("500x460")
    janela.grab_set()

    search_wrapper = ctk.CTkFrame(janela, corner_radius=20, fg_color="#2f2f2f", width=260, height=32)
    search_wrapper.pack(padx=10, pady=(16, 8))

    ctk.CTkLabel(search_wrapper, text="", image=icon_lupa, fg_color="transparent", width=24).pack(side="left", padx=(10, 0), pady=4)

    search_var = ctk.StringVar()
    search_entry = ctk.CTkEntry(
        master=search_wrapper, textvariable=search_var, placeholder_text="Buscar jogo...",
        font=("Segoe UI", 14), text_color="white", placeholder_text_color="#aaaaaa",
        border_color="#2f2f2f", fg_color="#2f2f2f", border_width=0,
        width=400, height=30
    )
    search_entry.pack(side="left", padx=(6, 8), pady=4, fill="x", expand=True)

    frame_scroll = ctk.CTkScrollableFrame(janela, width=480, height=340, fg_color="#121212", corner_radius=12)
    frame_scroll.pack(padx=10, pady=5)

    def gerar_link_direct(link):
        try:
            file_id = link.split("/d/")[1].split("/")[0]
            return f"https://drive.google.com/uc?id={file_id}"
        except:
            return None

    roms_existentes = set()
    for arquivo in os.listdir(get_rom_path('')):
        nome, ext = os.path.splitext(arquivo)
        if ext.lower() in [".bin", ".iso", ".img", ".cue"]:
            roms_existentes.add(nome)

    def renderizar_lista(jogos_filtrados):
        for widget in frame_scroll.winfo_children():
            widget.destroy()

        for jogo in jogos_filtrados:
            nome_formatado = jogo["nome"]

            linha = ctk.CTkFrame(frame_scroll, fg_color="#222222", corner_radius=8, height=60)
            linha.pack(fill="x", pady=8, padx=10)
            linha.pack_propagate(False)

            nome = ctk.CTkLabel(linha, text=jogo["nome"], font=("Segoe UI", 14, "bold"), anchor="w")
            nome.pack(side="left", padx=15)

            container = ctk.CTkFrame(linha, fg_color="transparent")
            container.pack(side="left", padx=10)

            status = ctk.CTkLabel(container, text="", anchor="w", font=("Segoe UI", 12))
            progress = ctk.CTkProgressBar(container, mode="indeterminate", height=5, width=140)

            def baixar_jogo(j=jogo, s=status, p=progress, b=None):
                def thread_func():
                    janela.after(0, lambda: (s.pack_forget(), p.pack(pady=4)))
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
                                    with zip_ref.open(file_info) as source:
                                        if ext in [".bin", ".iso", ".img", ".cue"]:
                                            target_path = get_rom_path(os.path.basename(filename))
                                        elif ext in [".png", ".jpg", ".jpeg"]:
                                            target_path = get_capa_path(os.path.basename(filename))
                                        else:
                                            continue
                                        with open(target_path, "wb") as f_out:
                                            f_out.write(source.read())
                            os.remove(destino)

                        janela.after(0, lambda: (
                            p.stop(), p.pack_forget(),
                            s.configure(text="Concluído!"),
                            s.pack(pady=4),
                            b.configure(state="disabled", image=icon_verificado),
                            atualizar_lista()
                        ))
                    except Exception as e:
                        janela.after(0, lambda: (
                            p.stop(), p.pack_forget(),
                            s.configure(text=f"Erro: {e}"),
                            s.pack(pady=4)
                        ))

                threading.Thread(target=thread_func, daemon=True).start()

            if nome_formatado in roms_existentes:
                btn = ctk.CTkButton(linha, text="", image=icon_verificado, width=40, height=28, fg_color="transparent", state="disabled")
            else:
                btn = ctk.CTkButton(linha, text="", image=icon_download, width=40, height=28, fg_color="transparent")
                btn.configure(command=lambda j=jogo, s=status, p=progress, b=btn: baixar_jogo(j, s, p, b))

            btn.pack(side="right", padx=5)
            status.pack(pady=4)

    def filtrar_jogos_download(*args):
        termo = search_var.get().lower()
        jogos_filtrados = [j for j in jogos_remotos if termo in j["nome"].lower()]
        renderizar_lista(jogos_filtrados)

    search_var.trace_add("write", filtrar_jogos_download)
    renderizar_lista(jogos_remotos)




def verificar_ou_criar_cfg_hle():
    cfg_path = get_emulator_path("epsxe001.cfg")
    if not os.path.exists(cfg_path):
        conteudo_cfg = "1\nepsxe -nogui\n!Runbios HLE\n!Fullscreen 1\n"
        with open(cfg_path, "w") as f:
            f.write(conteudo_cfg)

def encontrar_jogos():
    jogos = []
    rom_dir = get_rom_path('')
    os.makedirs(rom_dir, exist_ok=True)

    for arquivo in os.listdir(rom_dir):
        if arquivo.lower().endswith(('.bin', '.iso', '.cue', '.img')):
            nome_jogo = os.path.splitext(arquivo)[0]
            capa = f"{nome_jogo}.png"
            if not os.path.isfile(get_capa_path(capa)):
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

    scroll_frame = ctk.CTkScrollableFrame(game_frame, fg_color="#121212", corner_radius=10)
    scroll_frame.pack(fill="both", expand=True)

    moldura_path = get_asset_path("moldura_transparente.png")
    moldura_base = Image.open(moldura_path).convert("RGBA")
    moldura_w, moldura_h = 100, 110
    moldura_base = moldura_base.resize((moldura_w, moldura_h), Image.LANCZOS)

    inner_x, inner_y = 5, 0
    inner_w, inner_h = 90, 100



    if not lista_jogos:
        ctk.CTkLabel(scroll_frame, text="Nenhum jogo encontrado!", font=("Segoe UI", 16, "bold"), text_color="gray").pack(pady=50)
        return

    for idx, jogo in enumerate(lista_jogos):
        nome_jogo = jogo["title"]
        is_default = jogo["image"] == "default.png"

        if is_default:
            imagem_final = Image.open(get_asset_path("default.png")).convert("RGBA").resize((moldura_w, moldura_h))
        else:
            try:
                capa_original = Image.open(get_capa_path(jogo["image"])).convert("RGBA")
                ratio_w = inner_w / capa_original.width
                ratio_h = inner_h / capa_original.height
                scale = max(ratio_w, ratio_h)
                new_size = (int(capa_original.width * scale), int(capa_original.height * scale))
                capa_ajustada = capa_original.resize(new_size, Image.LANCZOS)

                left = (capa_ajustada.width - inner_w) // 2
                top = (capa_ajustada.height - inner_h) // 2
                right = left + inner_w
                bottom = top + inner_h
                capa_crop = capa_ajustada.crop((left, top, right, bottom))

                imagem_fundo = Image.new("RGBA", (moldura_w, moldura_h), (0, 0, 0, 0))
                imagem_fundo.paste(capa_crop, (inner_x, inner_y))
                imagem_fundo.paste(moldura_base, (0, 0), mask=moldura_base)
                imagem_final = imagem_fundo
            except:
                imagem_final = Image.open(get_asset_path("default.png")).convert("RGBA").resize((moldura_w, moldura_h))

        img_tk = ImageTk.PhotoImage(imagem_final)
        imagens.append(img_tk)

        frame_item = ctk.CTkFrame(scroll_frame, fg_color="#121212", corner_radius=8)
        titulo_quebrado = '\n'.join(nome_jogo.split()[:3])

        ctk.CTkButton(
            frame_item, image=img_tk, text=titulo_quebrado, compound="top",
            width=moldura_w, height=moldura_h + 20,
            fg_color="#121212", text_color="white", font=("Segoe UI", 12, "bold"),
            hover_color="#2a2a3d",
            command=lambda i=jogos.index(jogo): selecionar_jogo(i)
        ).pack()

        try:
            icone_editar = load_icon("icon_edit.png", size=(20, 20))
            def editar_capa(nome=nome_jogo):
                caminho = filedialog.askopenfilename(filetypes=[("Imagens", "*.png *.jpg *.jpeg")])
                if caminho and os.path.splitext(caminho)[-1].lower() in [".png", ".jpg", ".jpeg"]:
                    try:
                        nova = Image.open(caminho).convert("RGB")
                        nova.save(get_capa_path(f"{nome}.png"))
                        atualizar_lista()
                    except Exception as e:
                        messagebox.showerror("Erro", f"Erro ao atualizar a capa:\n{e}")
            ctk.CTkButton(
                frame_item, text="", image=icone_editar, width=18, height=18,
                fg_color="transparent", hover_color="#444", corner_radius=6,
                command=editar_capa
            ).place(x=moldura_w - 24, y=4)
        except:
            pass

        frame_item.grid(row=idx // 4, column=idx % 4, padx=10, pady=10)

       
# === UI ===
verificar_ou_criar_cfg_hle()
baixar_json_jogos()
root = ctk.CTk()
root.title("One Launcher")
root.geometry("560x520")

progress_bar = ctk.CTkProgressBar(root, mode="indeterminate", height=5)
progress_bar.set(0)
progress_label = ctk.CTkLabel(root, text="", font=("Segoe UI", 12), text_color="white")

try: root.iconbitmap(get_asset_path("icone.ico"))
except: pass

main_content = ctk.CTkFrame(root, fg_color="#1e1e1e")
main_content.pack(fill="both", expand=True)

header = ctk.CTkFrame(main_content, fg_color="#1e1e1e")
header.pack(fill="x", padx=10, pady=5)

def load_icon(name, size=(36, 36)):
    path = get_asset_path(name)
    try:
        return ImageTk.PhotoImage(Image.open(path).resize(size))
    except:
        return None

icon_refresh = load_icon("icon_refresh.png")
icon_config = load_icon("icon_settings.png")
icon_lupa = load_icon("icon_search.png", size=(28, 28))
icon_logo = load_icon("icone.png", size=(32, 32))
icon_download = load_icon("icon_download.png")
icon_verificado = load_icon("icon_check.png")

def create_icon_button(icon, command):
    btn = ctk.CTkLabel(header, text="", image=icon, fg_color="transparent", cursor="hand2")
    btn.pack(side="right", padx=5)
    btn.bind("<Button-1>", lambda e: command())
    return btn

create_icon_button(icon_config, configurar_controles)
create_icon_button(icon_refresh, atualizar_lista)
create_icon_button(icon_download, abrir_janela_de_downloads)

search_wrapper = ctk.CTkFrame(header, corner_radius=20, fg_color="#2f2f2f", width=260, height=32)
search_wrapper.pack(side="left", padx=10, pady=4)

ctk.CTkLabel(search_wrapper, text="", image=icon_lupa, fg_color="transparent", width=24).pack(side="left", padx=(10, 0), pady=4)

search_var = ctk.StringVar()
search_entry = ctk.CTkEntry(
    master=search_wrapper, textvariable=search_var, placeholder_text="Buscar jogo...",
    font=("Segoe UI", 14), text_color="white", placeholder_text_color="#aaaaaa",
    border_color="#2f2f2f", fg_color="#2f2f2f", border_width=0,
    width=200, height=30
)
search_entry.pack(side="left", padx=(6, 8), pady=4, fill="x", expand=True)

if icon_logo:
    ctk.CTkLabel(header, text="", image=icon_logo, fg_color="transparent").pack(side="left", padx=(5, 0))

ctk.CTkLabel(main_content, text="Jogos", font=("Segoe UI", 16, "bold"), text_color="white").pack(anchor="w", padx=20, pady=(5, 6))

def filtrar_jogos(*args):
    termo = search_var.get().lower()
    for widget in game_frame.winfo_children():
        widget.destroy()
    jogos_filtrados = [j for j in jogos if termo in j["title"].lower()]
    exibir_jogos(jogos_filtrados)

search_var.trace_add("write", filtrar_jogos)

game_frame = ctk.CTkFrame(main_content, fg_color="#1e1e1e")
game_frame.pack(fill="both", expand=True, padx=10, pady=(0, 5))

footer = ctk.CTkLabel(root, text="Created by Thiago Aciole © 2025", text_color="#aaaaaa", font=("Segoe UI", 12))
footer.pack(side="bottom", pady=5)

carregar_jogos()

root.mainloop()
