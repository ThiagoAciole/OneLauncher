import customtkinter as ctk
from tkinter import StringVar, messagebox
import threading, zipfile, os
from utils import get_rom_path, get_capa_path, gerar_link_direct, buscar_jogos
import home
import requests

# === Variáveis Globais ===
drawer = None
drawer_visible = False
icon_check = None
icon_search = None
icon_download = None
icon_refresh = None
icon_trash = None
jogos_remotos = []
loading_label = None
loading_progress = None

# === Funções ===
def toggle_drawer():
    global drawer_visible
    if drawer_visible:
        drawer.pack_forget()
    else:
        drawer.pack(side='right', fill='y')
        build_drawer(drawer)
    drawer_visible = not drawer_visible

def inject_drawer(frame, icons):
    global drawer, icon_search, icon_check, icon_download, icon_refresh, icon_trash
    drawer = frame
    icon_search = icons.get("search")
    icon_check = icons.get("check")
    icon_download = icons.get("download")
    icon_refresh = icons.get("refresh")
    icon_trash = icons.get("trash")

def build_drawer(frame):
    global loading_label

    for w in frame.winfo_children():
        w.destroy()

    ctk.CTkLabel(
        frame,
        text="Loja de Jogos",
        font=("Segoe UI", 18, "bold"),
        text_color="white"
    ).pack(pady=(16, 0))

    search_var = StringVar()
    search_wrapper = ctk.CTkFrame(frame, corner_radius=20, fg_color="#2f2f2f", width=400, height=32)
    search_wrapper.pack(padx=10, pady=(16, 8))
    search_wrapper.pack_propagate(False)

    ctk.CTkLabel(search_wrapper, text="", image=icon_search, fg_color="transparent", width=24).pack(side="left", padx=(10, 0), pady=4)

    search_entry = ctk.CTkEntry(
        master=search_wrapper,
        textvariable=search_var,
        placeholder_text="Buscar jogo...",
        font=("Segoe UI", 14),
        text_color="white",
        placeholder_text_color="#aaaaaa",
        border_color="#2f2f2f",
        fg_color="#2f2f2f",
        border_width=0
    )
    search_entry.pack(side="left", fill="both", expand=True, padx=(6, 4), pady=4)

    frame_scroll = ctk.CTkScrollableFrame(frame, fg_color="#121212", corner_radius=12)
    frame_scroll.pack(fill='both', expand=True, padx=10, pady=5)

    loading_container = ctk.CTkFrame(frame_scroll, fg_color="transparent")
    loading_container.pack(pady=20)

    loading_label = ctk.CTkLabel(
        loading_container,
        text="Carregando jogos...",
        font=("Segoe UI", 14),
        text_color="gray"
    )
    loading_label.pack(pady=(0, 8))

    global loading_progress
    loading_progress = ctk.CTkProgressBar(loading_container, mode="indeterminate", width=200)
    loading_progress.pack()

    def renderizar_lista(jogos_filtrados):
        for widget in frame_scroll.winfo_children():
            widget.destroy()

        roms_existentes = set()
        for arquivo in os.listdir(get_rom_path('')):
            nome, ext = os.path.splitext(arquivo)
            if ext.lower() in [".bin", ".iso", ".img", ".cue"]:
                roms_existentes.add(nome)

        for jogo in jogos_filtrados:
            nome_formatado = jogo["name"]
            linha = ctk.CTkFrame(frame_scroll, fg_color="#222222", corner_radius=8, height=60)
            linha.pack(fill="x", pady=8, padx=10)
            linha.pack_propagate(False)

            ctk.CTkLabel(linha, text=nome_formatado, font=("Segoe UI", 14, "bold"), anchor="w").pack(side="left", padx=15)
            container = ctk.CTkFrame(linha, fg_color="transparent")
            container.pack(side="left", padx=10)

            status = ctk.CTkLabel(container, text="", anchor="w", font=("Segoe UI", 12))
            progress = ctk.CTkProgressBar(container, mode="indeterminate", height=5, width=140)

            def baixar_jogo(j, s, p, b, nome_formatado, linha):
                def thread_func():
                    linha.after(0, lambda: (s.pack_forget(), p.pack(pady=4)))
                    p.start()
                    try:
                        direct_link = gerar_link_direct(j["link"])
                        destino = get_rom_path(f"{nome_formatado}.zip")

                        import gdown
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
                            home.carregar_jogos(),
                            renderizar_lista(jogos_remotos)
                        ))
                    except Exception as e:
                        linha.after(0, lambda: (
                            p.stop(), p.pack_forget(),
                            s.configure(text=f"Erro: {e}"),
                            s.pack(pady=4)
                        ))

                threading.Thread(target=thread_func, daemon=True).start()

            def apagar_jogo(nome, s, b):
                confirm = messagebox.askyesno("Confirmar", f"Deseja apagar '{nome}'?")
                if confirm:
                    for ext in [".bin", ".iso", ".img", ".cue", ".zip"]:
                        rom_path = get_rom_path(f"{nome}{ext}")
                        if os.path.exists(rom_path):
                            os.remove(rom_path)
                    for ext in [".png", ".jpg", ".jpeg"]:
                        capa_path = get_capa_path(f"{nome}{ext}")
                        if os.path.exists(capa_path):
                            os.remove(capa_path)
                    s.configure(text="🗑️ Jogo apagado")
                    b.configure(state="normal", image=icon_download)
                    home.carregar_jogos()
                    renderizar_lista(jogos_remotos)

            baixado = nome_formatado in roms_existentes

            btn_download = ctk.CTkButton(linha, text="", image=icon_check if baixado else icon_download, width=40, height=28, fg_color="transparent")
            btn_download.pack(side="right", padx=(0, 5))

            if not baixado:
                btn_download.configure(
                    command=lambda j=jogo, s=status, p=progress, b=btn_download, n=nome_formatado, l=linha: baixar_jogo(j, s, p, b, n, l)
                )

            if baixado:
                btn_delete = ctk.CTkButton(linha, text="", image=icon_trash, width=40, height=28, fg_color="transparent", hover_color="#ff4444")
                btn_delete.configure(command=lambda nome=nome_formatado, s=status, b=btn_download: apagar_jogo(nome, s, b))
                btn_delete.pack(side="right", padx=(0, 5))

            status.pack(pady=4)

        if loading_label and loading_label.winfo_exists():
            loading_label.destroy()

    def filtrar_jogos(*args):
        termo = search_var.get().lower()
        jogos_filtrados = [j for j in jogos_remotos if termo in j["name"].lower()]
        renderizar_lista(jogos_filtrados)

    status_label = ctk.CTkLabel(
        frame,
        text="",
        font=("Segoe UI", 12),
        text_color="gray"
    )
    status_label.pack(pady=(0, 8))

    def atualizar_jogos_remotos():
        status_label.configure(text="🔄 Buscando jogos...")
        loading_container.pack(pady=20)
        loading_progress.start()

        def buscar():
            sucesso, data = buscar_jogos()
            global jogos_remotos
            jogos_remotos = data

            def atualizar_interface():
                loading_progress.stop()
                loading_container.pack_forget()

                if not jogos_remotos:
                    status_label.configure(text="⚠️ Nenhum jogo encontrado ou erro ao carregar.")
                    loading_label.configure(text="Nenhum jogo encontrado.")
                else:
                    status_label.configure(text=f"✅ {len(jogos_remotos)} jogos carregados.")
                    renderizar_lista(jogos_remotos)

            frame.after(0, atualizar_interface)

        threading.Thread(target=buscar, daemon=True).start()

    atualizar_jogos_remotos()
    search_var.trace_add("write", filtrar_jogos)