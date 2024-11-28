import pyautogui
from PIL import Image, ImageDraw
import time
import numpy as np
import tkinter as tk
from tkinter import ttk
from tkinter import messagebox
import serial
import serial.tools.list_ports
import threading
import math
import os
import pystray
from PIL import Image, ImageTk
import asyncio

# pyinstaller map_led.py --noconsole --onefile

# Variabile globale per tenere traccia dello stato dell'esecuzione continua
continua = False
mode = 0
DELAY = 0.15
FILE_INFO = 'led_info.dat'
list_color_temp = []

#min e max della luminosità
MIN_LUX = 0
MAX_LUX = 100

# Crea una finestra principale
root = tk.Tk()
root.title("Controllo LED migliorato")
root.geometry("500x480")
root.resizable(False, False)
root.configure(bg='#2C3E50')  # Sfondo più scuro per un look più moderno

# Carica l'immagine dell'icona
icon_image = Image.open("icon.png")  # Inserisci il percorso corretto del tuo file immagine
icon_photo = ImageTk.PhotoImage(icon_image)

# Imposta l'icona della finestra principale
root.iconphoto(False, icon_photo)

# Variabili globali
ser = ''
new_width = tk.StringVar(value="18")
new_height = tk.StringVar(value="10")
width = tk.StringVar(value="56")
height = tk.StringVar(value="56")
bar_value = tk.StringVar(value="10")
baudrate = 115200  #9600

com_arduino = ''
mode_rest = False

# Creo il primo effetto
matrix_eff_0 = []

# Colori
BACKGROUND_COLOR = '#2C3E50'
FOREGROUND_COLOR = '#ECF0F1'
FOREGROUND_COLOR_ERROR = 'red'
BUTTON_COLOR = '#3498DB'
BUTTON_HOVER_COLOR = '#2980B9'
TEXT_COLOR = '#FFFFFF'
HIGHLIGHT_COLOR = '#1ABC9C'


def hide_window():
    root.withdraw()  # Nasconde la finestra principale

def show_window():
    root.deiconify()  # Mostra la finestra principale
    root.after(0, root.lift)  # Porta la finestra in primo piano

def on_quit(state_conn, icon=''):
    if state_conn == True: icon.stop()  # Ferma l'icona della tray
    root.destroy() # Chiude l'applicazione

def create_image():
    # Crea un'immagine 64x64 pixel
    width = 64
    height = 64
    image = Image.new('RGB', (width, height))

    # Crea un array di pixel per un gradiente in stile "Matrix"
    d = ImageDraw.Draw(image)

    for x in range(width):
        for y in range(height):
            # Calcola un colore arcobaleno con predominanza verde
            r = int((x / width) * 255)
            g = int(((height - y) / height) * 255)  # Colore verde decrescente verso il basso
            b = int((y / height) * 128)  # Aggiunge un tocco blu/viola

            # Diminuisce la componente verde per alcune righe per simulare l'effetto "Matrix"
            if y % 4 == 0:
                g = max(0, g - 50)

            # Imposta il pixel con il colore calcolato
            d.point((x, y), (r, g, b))

    # Posizione dei quadrati centrali
    square_size = 18  # Nuova dimensione del lato dei quadrati (triplicato)
    corner_radius = 6  # Raggio degli angoli arrotondati
    center_x, center_y = width // 2, height // 2  # Coordinate del centro dell'immagine
    
    # Calcola la posizione dei tre quadrati ai vertici di un triangolo equilatero
    triangle_radius = 14  # Distanza dal centro al vertice del triangolo

    # Coordinate dei tre quadrati (vertici del triangolo)
    square1 = (center_x, center_y - triangle_radius)  # Vertice superiore
    square2 = (center_x - triangle_radius, center_y + triangle_radius // 2)  # Vertice in basso a sinistra
    square3 = (center_x + triangle_radius, center_y + triangle_radius // 2)  # Vertice in basso a destra

    # Disegna i quadrati rossi, blu e verdi (dimensione 18x18 pixel, con bordi arrotondati)
    d.rounded_rectangle([square1[0] - square_size // 2, square1[1] - square_size // 2,
                         square1[0] + square_size // 2, square1[1] + square_size // 2], 
                        fill=(255, 0, 0), radius=corner_radius)  # Rosso

    d.rounded_rectangle([square2[0] - square_size // 2, square2[1] - square_size // 2,
                         square2[0] + square_size // 2, square2[1] + square_size // 2], 
                        fill=(0, 255, 0), radius=corner_radius)  # Verde

    d.rounded_rectangle([square3[0] - square_size // 2, square3[1] - square_size // 2,
                         square3[0] + square_size // 2, square3[1] + square_size // 2], 
                        fill=(0, 0, 255), radius=corner_radius)  # Blu
    image.save('icon.ico')
    return image

def setup_tray_icon():
    global tray_icon

    # Crea l'icona della tray
    icon_image = create_image()

    # Definisci le azioni disponibili nel menu della tray
    tray_icon = pystray.Icon("LED Control", icon_image, menu=pystray.Menu(
        pystray.MenuItem('Mostra', lambda: show_window()),  # Permette di ripristinare la finestra
        pystray.MenuItem('Esci', on_quit)  # Opzione per chiudere definitivamente
    ))

    # Avvia l'icona della tray in un thread separato
    threading.Thread(target=tray_icon.run, daemon=True).start()

def on_closing(state_conn):
    if state_conn==True:
        hide_window()
    else:
        on_quit(state_conn)

def file_esiste(nome_file):
    return os.path.isfile(nome_file)

def send_data_serial(data):
    global ser
    dataToSend = ''
    alpha = int(bar_value.get()) / 100

    for led in data:
        for color in led:
            dataToSend += str(round(int(color) * alpha)) + ';'
    ser.write(bytes(dataToSend, 'utf-8'))
    time.sleep(DELAY)

def get_screen_colors(px_width, px_height, width, height):
    global list_color_temp
    # Cattura lo schermo
    screenshot = pyautogui.screenshot(region=(0, 0, width, height))

    resized_screenshot = screenshot.resize((px_width, px_height))

    image_np = np.array(resized_screenshot)
    top_border = image_np[0:1, :, :]
    bottom_border = image_np[-1:, :, :]
    left_border = image_np[:, 0:1, :]
    right_border = image_np[:, -1:, :]

    size = (2 * px_width) + (2 * px_height)
    list_color = np.zeros((size, 3))

    for k in range(px_width):
        list_color[k] = bottom_border[0][k]

    for k in range(px_height):
        list_color[k + px_width] = right_border[px_height - k - 1][0]

    for k in range(px_width):
        list_color[k + px_width + px_height] = top_border[0][px_width - k - 1]

    for k in range(px_height):
        list_color[k + 2 * px_width + px_height] = left_border[k][0]
    
    s = 10
    if len(list_color_temp)>0:
        list_color = (list_color_temp+ s*list_color)/(s+1)
    list_color_temp = list_color
    return list_color

def change_mode(new_mode):
    global mode, button_mode_0, button_mode_1, button_mode_2, button_test
    mode = new_mode

    style_button(button_mode_0)
    style_button(button_mode_1)
    style_button(button_mode_2)
    style_button(button_test)

    if mode == 0 and continua==True:
        button_mode_0.config(bg='green')
    elif mode == 1:
        button_test.config(bg='green')
    elif mode == 2:
        button_mode_1.config(bg='green')
    elif mode == 3:
        button_mode_2.config(bg='green')

def test_led_matrix(w, h):
    matrix_led = np.zeros(((2 * h + 2 * w), 3))

    matrix_led[0] = [255, 0, 255]
    matrix_led[2 * w + 2 * h - 1] = [255, 0, 255]

    matrix_led[w - 1] = [0, 0, 255]
    matrix_led[w] = [0, 0, 255]

    matrix_led[w + h - 1] = [255, 0, 0]
    matrix_led[w + h] = [255, 0, 0]

    matrix_led[2 * w + h - 1] = [255, 255, 0]
    matrix_led[2 * w + h] = [255, 255, 0]

    time.sleep(0.15)
    return matrix_led

def eff_led_0(w, h):
    global matrix_eff_0

    if len(matrix_eff_0) == 0:
        matrix_eff_0 = np.zeros(((2 * h + 2 * w), 3))
        L = len(matrix_eff_0)
        L2 = L // 2
        array_gaussiano = np.zeros(L2)
        for j in range(L2):
            array_gaussiano[j] = math.exp(-math.pow(j, 2) / (L2 * 5))
        metà_sinistra = np.sort(array_gaussiano)
        metà_destra = metà_sinistra[::-1]
        array_ordinato = np.concatenate((metà_sinistra, metà_destra))
        for i in range(len(matrix_eff_0)):
            val = int(255 * array_ordinato[i])
            matrix_eff_0[i] = [val, 0, int(val * 0.5)]

    dim = len(matrix_eff_0)
    temp = matrix_eff_0[0]
    for k in range(dim - 1):
        matrix_eff_0[k] = matrix_eff_0[k + 1]

    matrix_eff_0[dim - 1] = temp

    time.sleep(0.05)
    return matrix_eff_0

def one_color(w, h):
    matrix_color = np.full(((2 * w + 2 * h), 3), 255)
    time.sleep(0.15)
    return matrix_color

def control_led():
    # Dichiaro le variabili globali
    global continua, new_width, new_height, width, height

    while continua:
        nw = int(new_width.get())
        nh = int(new_height.get())
        w = int(width.get())
        h = int(height.get())
        list_color = np.zeros(((2 * nh + 2 * nw), 3))

        def switch_case(case):
            if case == 0:  # Ossereva il monitor
                return get_screen_colors(nw, nh, w, h)
            elif case == 1:
                return test_led_matrix(nw, nh)
            elif case == 2:
                return eff_led_0(nw, nh)
            elif case == 3:
                return one_color(nw, nh)
            else:
                return np.zeros(((2 * nh + 2 * nw), 3))

        list_color = switch_case(mode)

        send_data_serial(list_color)

def on_scale_change(value):
        global bar_value
        bar_value.set(value)

def toggle_funzione():
    # Dichiaro la variabile continua come globale
    global continua, ser, mode, button_mode_0, button_mode_1, button_mode_2, button_test
    
    if continua:
        # Disabilita l'esecuzione continua
        continua = False
        button.config(text="Start")
        button.config(bg='#2ecc71')
        scale.config(state="disabled")
        button_test.config(state="disabled")
        button_mode_0.config(state="disabled")
        button_mode_1.config(state="disabled")
        button_mode_2.config(state="disabled")
        change_mode(0)
    else:
        # Abilita l'esecuzione continua
        continua = True
        button.config(text="Stop")
        button.config(bg='#e74c3c')
        scale.config(state="active")
        button_test.config(state="active")
        button_mode_0.config(state="active")
        button_mode_1.config(state="active")
        button_mode_2.config(state="active")
        change_mode(0)
        # Avvia una thread per eseguire la funzione in modo continuo con i parametri specificati
        threading.Thread(target=control_led, daemon=True).start()

def load_info():
    info = {}
    if file_esiste(FILE_INFO):
        with open(FILE_INFO, 'r') as file:
            for righe in file:
                for riga in righe.strip().split('\n'):
                    # Rimuovi eventuali spazi bianchi e separa chiave e valore
                    chiave, valore = riga.strip().split('\t')
                    # Aggiungi al dizionario
                    info[chiave] = valore
    else:
        with open(FILE_INFO, 'w') as file:
            file.write('hwid_arduino\tVID:PID=1A86:7523\n')
            file.write('LUX\t30\n')
            print(f"Il file {FILE_INFO} è stato creato con contenuto predefinito.")
    return info

def connect():
    try:
        global ser, baudrate, com_arduino, bar_value
        porte_seriali = serial.tools.list_ports.comports()
        state_conn = False

        info = load_info()
        hwid_arduino = info['hwid_arduino']
        bar_value = tk.StringVar(value=info['LUX'])
        for porta in porte_seriali:

            if (hwid_arduino in porta.hwid):
                com_arduino = porta.device
        
        if (len(com_arduino) != 0):
            ser = serial.Serial(com_arduino, baudrate=baudrate, timeout=2)

        if (len(com_arduino) != 0):
            state_conn = True

        return state_conn
    except:
        return False

# Aggiorna lo stile dei pulsanti per un look moderno
def style_button(button):
    button.config(
        bg=BUTTON_COLOR,
        fg=TEXT_COLOR,
        activebackground=BUTTON_HOVER_COLOR,
        activeforeground=TEXT_COLOR,
        bd=0,
        font=("Helvetica", 12, "bold"),
        relief="flat"
    )

# Esegue il reset 
def reset():
    for widget in root.winfo_children():  # Elimina tutti i widget
        widget.destroy()
    setup_ui()

# Provo ad connettermi ongi secondo in modo asincrono
async def run_rest(sleep=1):
    global mode_rest
    mode_rest = True
    while not connect():
        
        await reset()
        await asyncio.sleep(sleep)

def setup_ui():
    global ser, width, height, bar_value, MIN_LUX, MAX_LUX, continua
    global button, scale, button_test
    global button_mode_0, button_mode_1, button_mode_2
    global mode_rest
    state_conn = connect()
    if not state_conn and mode_rest==False:
        asyncio.run(run_rest())
    elif state_conn:
        mode_rest = False
        
    # Sezione superiore (titolo e stato dispositivo)
    frame_top = tk.Frame(root, bg=BACKGROUND_COLOR)
    frame_top.pack(fill=tk.X, pady=20)

    title_label = tk.Label(frame_top, text="Controllo LED", font=("Helvetica", 20, "bold"), fg=HIGHLIGHT_COLOR, bg=BACKGROUND_COLOR)
    title_label.pack()

    if state_conn: status_label = tk.Label(frame_top, text="Stato dispositivo: Connesso", fg=HIGHLIGHT_COLOR, bg=BACKGROUND_COLOR)
    else: status_label = tk.Label(frame_top, text="Stato dispositivo: Non connesso", fg=FOREGROUND_COLOR_ERROR, bg=BACKGROUND_COLOR)
    status_label.pack()

    # Frame per le impostazioni principali
    frame_settings = tk.Frame(root, bg=BACKGROUND_COLOR)
    frame_settings.pack(fill=tk.X, padx=20, pady=20, anchor='w')

    # Sezione per porta e dimensione schermo
    port_label = tk.Label(frame_settings, text="Porta:", fg=FOREGROUND_COLOR, bg=BACKGROUND_COLOR)
    port_label.grid(row=0, column=0, padx=10, pady=5, sticky='w')
    port_text = ser.port if state_conn == True else '---'
    port_value = tk.Entry(frame_settings, textvariable=tk.StringVar(value=port_text), state="readonly", width=15)
    port_value.grid(row=0, column=1, padx=10, pady=5, sticky='w')

    # Dimesione schermo attuale
    width.set(root.winfo_screenwidth())
    height.set(root.winfo_screenheight())
    size_label = tk.Label(frame_settings, text="Dimensione schermo:", fg=FOREGROUND_COLOR, bg=BACKGROUND_COLOR)
    size_label.grid(row=1, column=0, padx=10, pady=5, sticky='w')
    size_value = tk.Entry(frame_settings, textvariable=tk.StringVar(value=str(width.get()) + 'x'+str(height.get())), state="readonly", width=15)
    size_value.grid(row=1, column=1, padx=10, sticky='w')

    # Numero di LED
    led_label = tk.Label(frame_settings, text="Numero LED:", fg=FOREGROUND_COLOR, bg=BACKGROUND_COLOR)
    led_label.grid(row=2, column=0, padx=10, pady=5, sticky='w')
    led_value = tk.Entry(frame_settings, textvariable=tk.StringVar(value="56"), state="readonly", width=15)
    led_value.grid(row=2, column=1, padx=10, sticky='w')
    
    if not state_conn:
        reset_btn = tk.Button(frame_settings, text="Rest conn.", command=lambda : reset())
        reset_btn.grid(row=3, column=1, padx=10, sticky='w')
    
    
    # ------------
    # Separatore
    separator = ttk.Separator(root, orient='horizontal')
    separator.pack(fill=tk.X, padx=10, pady=20)
    # ------------
    
    
    # Sezione pulsanti modalità
    frame_mode = tk.Frame(root, bg=BACKGROUND_COLOR)
    frame_mode.pack(padx=20, fill=tk.X)
  
    button_mode_0 = tk.Button(frame_mode, text="Screen Mode", command=lambda: change_mode(0), state='disabled')
    button_mode_1 = tk.Button(frame_mode, text="Snake Mode", command=lambda: change_mode(2), state='disabled')
    button_mode_2 = tk.Button(frame_mode, text="White Mode", command=lambda: change_mode(3), state='disabled')
    button_test = tk.Button(frame_mode, text="Test", command=lambda: change_mode(1), state='disabled')

    for button in [button_mode_0, button_mode_1, button_mode_2, button_test]:
        style_button(button)
        # button.pack(side=tk.LEFT, padx=10, pady=5)
    
    button_mode_0.grid(row=0, column=0, padx=5, pady=5, sticky='ew')
    button_mode_1.grid(row=0, column=1, padx=5, pady=5, sticky='ew')
    button_mode_2.grid(row=0, column=2, padx=5, pady=5, sticky='ew')
    button_test.grid(row=0, column=3, padx=5, pady=5, sticky='ew')

    # Configura le colonne della griglia per espandersi
    frame_mode.grid_columnconfigure(0, weight=1)
    frame_mode.grid_columnconfigure(1, weight=1)
    frame_mode.grid_columnconfigure(2, weight=1)
    frame_mode.grid_columnconfigure(3, weight=1)

    # Luminosità Slider
    frame_brightness = tk.Frame(root, bg=BACKGROUND_COLOR)
    frame_brightness.pack(padx=20, fill=tk.X, pady=20)

    brightness_label = tk.Label(frame_brightness, text="Luminosità:", fg=FOREGROUND_COLOR, bg=BACKGROUND_COLOR)
    # brightness_label.pack(side=tk.LEFT, anchor='w')
    brightness_label.grid(row=0, column=0, sticky='w')

    frame_brightness.grid_columnconfigure(0, weight=1)
    scale = tk.Scale(frame_brightness, from_=MIN_LUX, to=MAX_LUX, orient="horizontal", bg=BACKGROUND_COLOR, fg=TEXT_COLOR, command=on_scale_change)
    scale.set(int(bar_value.get()))
    if (state_conn==False or continua == False): scale.config(state="disabled")
    # scale.pack(side=tk.LEFT, fill=tk.X, padx=(20, 0), expand=True)
    scale.grid(row=1, column=0, pady=5,padx=10, sticky='ew')

    # Bottone per ON/OFF
    button_frame = tk.Frame(root, bg=BACKGROUND_COLOR)
    button_frame.pack(pady=0)

    button = tk.Button(button_frame, text="Start", command=toggle_funzione, width=15)
    style_button(button)
    button.config(bg='#2ecc71')
    if state_conn==False: button.config(state="disabled")
    else: 
        toggle_funzione()
        on_closing(state_conn)
    
    button.pack()
    
    root.protocol("WM_DELETE_WINDOW", lambda: on_closing(state_conn))

def main():
    setup_tray_icon()
    setup_ui()
    root.mainloop()

if __name__ == "__main__":
    main()
