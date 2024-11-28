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
from PIL import Image as PILImage

# Variabile globale per tenere traccia dello stato dell'esecuzione continua
continua = False
mode = 0
DALAY = 0.15
FILE_INFO = 'led_info.dat'

# Crea una finestra principale
root = tk.Tk()
root.title("Controllo led")
root.geometry("400x300")
root.resizable(False, False)

# Variabili globali
ser = ''
new_width = tk.StringVar()
new_height = tk.StringVar()
width = tk.StringVar()
height = tk.StringVar()
bar_value = tk.StringVar()
bar_value.set(30)
baudrate = 115200 #9600

# Dimensione schemo da analizza (la somma dei bordi deve essere pari al numero di led)
new_width.set(18)
new_height.set(10)

com_arduino = ''


# Creo il primo effetto
matrix_eff_0 = []

def file_esiste(nome_file):
    return os.path.isfile(nome_file)

def send_data_serial(data):
    global ser
    dataToSend = ''
    alpha = int(bar_value.get())/100

    for led in data:
        for color in led:
            dataToSend += str(round(int(color)*alpha))+';'
    ser.write(bytes(dataToSend, 'utf-8'))
    time.sleep(DALAY)


def get_screen_colors(px_width, px_height, width, height):
    # Cattura lo schermo
    screenshot = pyautogui.screenshot(region=(0, 0, width, height))

    resized_screenshot = screenshot.resize((px_width, px_height))

    image_np = np.array(resized_screenshot)
    top_border = image_np[0:1, :, :]
    bottom_border = image_np[-1:, :, :]
    left_border = image_np[:, 0:1, :]
    right_border = image_np[:, -1:, :]

    size = (2*px_width) + (2*px_height)
    list_color = np.zeros((size, 3))

    for k in range(px_width):
        list_color[k] = bottom_border[0][k]

    for k in range(px_height):
        list_color[k+px_width] = right_border[px_height-k-1][0]

    for k in range(px_width):
        list_color[k+px_width+px_height] = top_border[0][px_width-k-1]

    for k in range(px_height):
        list_color[k+2*px_width+px_height] = left_border[k][0]

    return list_color


def change_mode(new_mode):
    global mode, button_mode_0, button_mode_1, button_mode_2
    mode = new_mode

    button_mode_0.config(bg='SystemButtonFace')
    button_mode_1.config(bg='SystemButtonFace')
    button_mode_2.config(bg='SystemButtonFace')
    button_test.config(bg='SystemButtonFace')

    if mode == 0 and continua == True:
        button_mode_0.config(bg='green')
    elif mode == 1:
        button_test.config(bg='green')
    elif mode == 2:
        button_mode_1.config(bg='green')
    elif mode == 3:
        button_mode_2.config(bg='green')


def test_led_matrix(w, h):
    matrix_led = np.zeros(((2*h+2*w), 3))

    matrix_led[0] = [255, 0, 255]
    matrix_led[2*w+2*h-1] = [255, 0, 255]

    matrix_led[w-1] = [0, 0, 255]
    matrix_led[w] = [0, 0, 255]

    matrix_led[w+h-1] = [255, 0, 0]
    matrix_led[w+h] = [255, 0, 0]

    matrix_led[2*w+h-1] = [255, 255, 0]
    matrix_led[2*w+h] = [255, 255, 0]

    time.sleep(0.15)
    return matrix_led


def eff_led_0(w, h):
    global matrix_eff_0

    if len(matrix_eff_0) == 0:
        matrix_eff_0 = np.zeros(((2*h+2*w), 3))
        # for i in range(len(matrix_eff_0)):
        #     val = int(255*math.pow(i/len(matrix_eff_0), 2))
        #     matrix_eff_0[i] = [val, 0, int(val*0.9)]
        L = len(matrix_eff_0)
        L2 = L // 2
        array_gaussiano = np.zeros(L2)
        for j in range(L2):
            array_gaussiano[j] = math.exp(-math.pow(j, 2)/(L2*5))
        metà_sinistra = np.sort(array_gaussiano)
        metà_destra = metà_sinistra[::-1]
        array_ordinato = np.concatenate((metà_sinistra, metà_destra))
        for i in range(len(matrix_eff_0)):
            val = int(255*array_ordinato[i])
            matrix_eff_0[i] = [val, 0, int(val*0.5)]

    dim = len(matrix_eff_0)
    temp = matrix_eff_0[0]
    for k in range(dim-1):
        matrix_eff_0[k] = matrix_eff_0[k+1]

    matrix_eff_0[dim-1] = temp

    time.sleep(0.05)
    return matrix_eff_0


def one_color(w, h):
    matrix_color = np.full(((2*w+2*h), 3), 255)
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


# Funzione chiamata quando il bottone viene premuto
def toggle_funzione():
    # Dichiaro la variabile continua come globale
    global continua, ser, mode

    if continua:
        # Disabilita l'esecuzione continua
        continua = False
        button.config(text="ON")
        scale.config(state="disabled")
        button_test.config(state="disabled")
        button_mode_0.config(state="disabled")
        button_mode_1.config(state="disabled")
        button_mode_2.config(state="disabled")
        change_mode(0)
    else:
        # Abilita l'esecuzione continua
        continua = True
        button.config(text="OFF")
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
            for riga in file:
                # Rimuovi eventuali spazi bianchi e separa chiave e valore
                chiave, valore = riga.strip().split('\t')
                # Aggiungi al dizionario
                info[chiave] = valore
    else:
        with open(FILE_INFO, 'w') as file:
            file.write('hwid_arduino\tVID:PID=1A86:7523')
            print(f"Il file {FILE_INFO} è stato creato con contenuto predefinito.")
    return info


def main():
    global ser, new_width, new_height, width, height, com_arduino, bar_value, button, scale, button_test
    global button_mode_0, button_mode_1, button_mode_2
    porte_seriali = serial.tools.list_ports.comports()

    info = load_info()
    hwid_arduino = info['hwid_arduino']
    for porta in porte_seriali:

        if (hwid_arduino in porta.hwid):
            com_arduino = porta.device
    
    if (len(com_arduino) != 0):
        ser = serial.Serial(com_arduino, baudrate=baudrate, timeout=2)

    # Dimesione schermo attuale
    width.set(root.winfo_screenwidth())
    height.set(root.winfo_screenheight())

    port_label = tk.StringVar()

    if (len(com_arduino) == 0):
        port_label.set('---')
    else:
        port_label.set(com_arduino)

    frame0 = tk.Frame(root)
    # Posiziona il frame nella parte superiore della finestra principale
    frame0.pack(side=tk.TOP, fill=tk.X, padx=10, pady=10)

    button_test = tk.Button(
        frame0, text="Test", command=lambda: change_mode(1), state='disabled')
    button_test.pack(side=tk.RIGHT, padx=10)

    text_sp = 'Cerco il dispositivo: ' + hwid_arduino + ' - '
    if (len(com_arduino) == 0):
        text_sp += 'Non connesso!'
    else:
        text_sp += 'Connesso!'
    search_port_label = tk.Label(frame0, text=text_sp)
    search_port_label.pack(side=tk.LEFT)

    frame1 = tk.Frame(root)
    # Posiziona il frame nella parte superiore della finestra principale
    frame1.pack(side=tk.TOP, fill=tk.X)

    frame_port = tk.Frame(frame1)
    frame_port.pack(side=tk.LEFT, padx=10)
    # Etichetta e campo di inserimento per il parametro
    label1 = tk.Label(frame_port, text="Porta:")
    label1.pack()
    entry1 = tk.Entry(frame_port, textvariable=port_label,
                      width=10, state='readonly')
    entry1.pack()

    frame_size = tk.Frame(frame1)
    frame_size.pack(side=tk.LEFT, fill=tk.X, expand=True)
    # Etichetta e campo di inserimento per il parametro
    label2 = tk.Label(frame_size, text="Size:")
    label2.pack()
    screen_size = tk.StringVar()
    screen_size.set(str(width.get()) + 'x'+str(height.get()))
    entry = tk.Entry(frame_size, textvariable=screen_size,
                     width=15, state='readonly')

    entry.pack()

    frame_led = tk.Frame(frame1)
    frame_led.pack(side=tk.RIGHT, padx=10)
    # Etichetta e campo di inserimento per il parametro
    n_led = tk.StringVar()
    n_led.set(2*int(new_width.get()) + 2*int(new_height.get()))

    label4 = tk.Label(frame_led, text="Numero LED:")
    label4.pack()
    entry4 = tk.Entry(frame_led, textvariable=n_led,
                      width=10, state='readonly')
    entry4.pack()

    # ---------
    # Creazione del Canvas per disegnare la linea
    canvas = tk.Canvas(root, bg="gray", height=1, highlightthickness=0)
    # Riempi il Canvas orizzontalmente e aggiungi del padding
    canvas.pack(fill=tk.X, padx=10, pady=10)
    # ---------

    frame_mode = tk.Frame(root)
    # Posiziona il frame nella parte superiore della finestra principale
    frame_mode.pack(side=tk.TOP, fill=tk.X, padx=10, pady=5)
    button_mode_0 = tk.Button(
        frame_mode, text="Screen", command=lambda: change_mode(0), state='disabled')
    button_mode_0.pack(side=tk.LEFT, padx=10)
    button_mode_1 = tk.Button(
        frame_mode, text="Snake", command=lambda: change_mode(2), state='disabled')
    button_mode_1.pack(side=tk.LEFT, padx=10)

    button_mode_2 = tk.Button(
        frame_mode, text="White", command=lambda: change_mode(3), state='disabled')
    button_mode_2.pack(side=tk.LEFT, padx=10)

    # ---------
    # Creazione del Canvas per disegnare la linea
    canvas = tk.Canvas(root, bg="gray", height=1, highlightthickness=0)
    # Riempi il Canvas orizzontalmente e aggiungi del padding
    canvas.pack(fill=tk.X, padx=10, pady=10)
    # ---------

    def on_scale_change(value):
        bar_value.set(value)

    # Costanti per definire l'intervallo consentito
    MIN = 0
    MAX = 100

    frame3 = tk.Frame(root)
    frame3.pack(side=tk.TOP, fill=tk.X, padx=10)

    # Etichetta per visualizzare il valore corrente
    label_bar_text = tk.Label(frame3, text='Luminosità:')
    label_bar_text.pack(side=tk.LEFT)

    # Barra di scorrimento
    frame4 = tk.Frame(root)
    frame4.pack(side=tk.TOP, fill=tk.X, padx=10)
    scale = tk.Scale(frame4, from_=MIN, to=MAX,
                     orient="horizontal", command=on_scale_change)
    scale.set(int(bar_value.get()))
    if (len(com_arduino) == 0 or continua == False):
        scale.config(state="disabled")
    scale.pack(fill=tk.X, padx=10)

    # Bottone per avviare o interrompere l'esecuzione continua

    button = tk.Button(root, text="ON",
                       command=toggle_funzione)
    if (len(com_arduino) == 0):
        button.config(state="disabled")
    button.pack(pady=5)

    # Funzione per chiudere correttamente la finestra
    def on_closing():
        # Dichiaro la variabile continua come globale
        global continua
        continua = False  # Assicura che l'esecuzione continua si interrompa prima della chiusura
        root.destroy()

    # Associa la funzione di chiusura alla chiusura della finestra
    root.protocol("WM_DELETE_WINDOW", on_closing)
    root.mainloop()


if __name__ == "__main__":
    main()