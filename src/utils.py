
import os, sys, gdown, json, threading, requests
from PIL import Image, ImageTk

SUPABASE_URL = "https://dyueheomajwunmblzpeh.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImR5dWVoZW9tYWp3dW5tYmx6cGVoIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTI4NTI5MDksImV4cCI6MjA2ODQyODkwOX0.IYmNsPSpNoMKGDf9lb7mG2q3sdSMgV8sJ1MrTMuxaHU"

def get_base_path():
    if getattr(sys, 'frozen', False):
        return os.path.dirname(sys.executable)
    return os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

def get_asset_path(name):
    if getattr(sys, 'frozen', False):
        return os.path.join(sys._MEIPASS, 'assets', name)
    return os.path.join(os.path.dirname(__file__), 'assets', name)

def get_emulator_path(name):
    base = getattr(sys, '_MEIPASS', get_base_path())
    return os.path.join(base, 'game', name)

def get_rom_path(name):
    if getattr(sys, 'frozen', False):
        return os.path.join(os.path.dirname(sys.executable), 'roms', name)
    return os.path.join(get_base_path(), 'roms', name)

def get_capa_path(name):
    if getattr(sys, 'frozen', False):
        return os.path.join(os.path.dirname(sys.executable), 'capas', name)
    return os.path.join(get_base_path(), 'capas', name)

def gerar_link_direct(link):
    try:
        file_id = link.split("/d/")[1].split("/")[0]
        return f"https://drive.google.com/uc?id={file_id}"
    except:
        return None

def buscar_jogos():
    url = f"{SUPABASE_URL}/rest/v1/games"
    headers = {
        "apikey": SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}",
        "Content-Type": "application/json"
    }
    params = {
        "select": "name,link"  # campos que você quer buscar
    }

    try:
        response = requests.get(url, headers=headers, params=params)
        if response.ok:
            return True, response.json()
        else:
            print(f"Erro HTTP {response.status_code}: {response.text}")
            return False, []
    except Exception as e:
        print(f"Erro na requisição: {e}")
        return False, []

def verificar_ou_criar_cfg_hle():
    cfg = get_emulator_path('epsxe001.cfg')
    if not os.path.exists(cfg):
        with open(cfg, 'w') as f:
            f.write('1\nepsxe -nogui\n!Runbios HLE\n!Fullscreen 1\n')

def setup_launcher():
    verificar_ou_criar_cfg_hle()

def load_icon(name, size=(24, 24), make_white=False):
    try:
        img = Image.open(get_asset_path(name)).resize(size)
        if make_white:
            img = img.convert("RGBA")
            r, g, b, a = img.split()
            white_img = Image.new("RGBA", img.size, (255, 255, 255, 255))
            img = Image.composite(white_img, img, a)
        return ImageTk.PhotoImage(img)
    except:
        return None

def load_icons():
    return {
        "download": load_icon('icon_download.png', (32, 32)),
        "refresh":  load_icon('icon_refresh.png', (32, 32)),
        "config":   load_icon('icon_settings.png', (32, 32)),
        "search":   load_icon('icon_search.png', (32, 32)),
        "logo":     load_icon('icone.png', (32, 32)),
        "check":    load_icon('icon_check.png', (40, 40)),
        "edit":     load_icon('icon_edit.png', (20, 20), make_white=True),
    }
