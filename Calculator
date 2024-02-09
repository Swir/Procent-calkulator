import tkinter as tk
from tkinter import ttk
from tkinter import messagebox

def oblicz_procent():
    try:
        wartosc = float(entry_wartosc.get())
        procent = float(entry_procent.get())
        
        czesc = (procent / 100) * wartosc
        wynik = wartosc - czesc
        
        label_wynik.config(text=f"{procent}% liczby {wartosc} to {czesc}, pozostało {wynik}.", foreground="blue")
    except ValueError:
        messagebox.showerror("Błąd", "Podaj poprawne liczby.")

# Tworzenie okna głównego
root = tk.Tk()
root.title("Obliczanie procentów")
root.geometry("350x150")  # Ustawienie początkowego rozmiaru okna

# Stylizacja
style = ttk.Style()
style.theme_use('clam')  # Możesz zmienić nazwę stylu na inne, np. 'default', 'alt', 'classic', 'vista', 'xpnative'

style.configure('TButton', background='#4CAF50', foreground='white', font=('Helvetica', 10))
style.configure('TLabel', background='#f0f0f0', foreground='black', font=('Helvetica', 10))
style.configure('TEntry', fieldbackground='white', font=('Helvetica', 10))

# Etykiety i pola tekstowe dla wartości oraz procentu
label_wartosc = ttk.Label(root, text="Wartość:")
label_wartosc.grid(row=0, column=0, padx=10, pady=5)
entry_wartosc = ttk.Entry(root)
entry_wartosc.grid(row=0, column=1, padx=10, pady=5)

label_procent = ttk.Label(root, text="Procent:")
label_procent.grid(row=1, column=0, padx=10, pady=5)
entry_procent = ttk.Entry(root)
entry_procent.grid(row=1, column=1, padx=10, pady=5)

# Przycisk do obliczania procentów
button_oblicz = ttk.Button(root, text="Oblicz", command=oblicz_procent)
button_oblicz.grid(row=2, column=0, columnspan=2, padx=10, pady=5)

# Etykieta na wynik
label_wynik = ttk.Label(root, text="", foreground="blue")
label_wynik.grid(row=3, column=0, columnspan=2, padx=10, pady=5)

# Uruchomienie głównej pętli programu
root.mainloop()
