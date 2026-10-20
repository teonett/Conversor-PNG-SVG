"""Interface gráfica em português, com conversão fora da thread da interface."""
from pathlib import Path
from queue import Queue, Empty
from threading import Thread
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

from .service import run_conversion


class App:
    def __init__(self, root):
        self.root = root
        self.files = []
        self.busy = False
        self.events = Queue()
        self.folder = tk.StringVar()
        self.quality = tk.StringVar(value="alta")
        self.colors = tk.StringVar(value="8")
        self.overwrite = tk.BooleanVar(value=False)
        root.title("PNG para SVG — Conversor local")
        root.geometry("820x650")
        root.minsize(700, 570)
        root.protocol("WM_DELETE_WINDOW", self.close)
        frame = ttk.Frame(root, padding=20)
        frame.pack(fill="both", expand=True)
        ttk.Label(frame, text="PNG para SVG", font=("Segoe UI", 22, "bold")).pack(anchor="w")
        ttk.Label(frame, text="Vetorização local para logotipos, ícones e ilustrações de cores sólidas.").pack(anchor="w", pady=(2, 14))
        self.choose = ttk.Button(frame, text="Selecionar arquivos PNG…", command=self.select)
        self.choose.pack(anchor="w")
        self.listbox = tk.Listbox(frame, height=6, selectmode="extended")
        self.listbox.pack(fill="x", pady=8)
        ttk.Label(frame, text="Pasta de saída (vazia = mesma pasta de cada PNG)").pack(anchor="w")
        folder_row = ttk.Frame(frame)
        folder_row.pack(fill="x", pady=(4, 12))
        self.entry = ttk.Entry(folder_row, textvariable=self.folder)
        self.entry.pack(side="left", fill="x", expand=True)
        self.browse = ttk.Button(folder_row, text="Escolher…", command=self.select_folder)
        self.browse.pack(side="left", padx=(8, 0))
        options = ttk.Frame(frame)
        options.pack(fill="x")
        ttk.Label(options, text="Qualidade").grid(row=0, column=0, sticky="w")
        self.combo = ttk.Combobox(options, textvariable=self.quality,
                                  values=["rapida", "equilibrada", "alta"], state="readonly", width=16)
        self.combo.grid(row=1, column=0, sticky="w", pady=4)
        ttk.Label(options, text="Máximo de cores").grid(row=0, column=1, sticky="w", padx=20)
        self.spin = ttk.Spinbox(options, from_=1, to=32, textvariable=self.colors, width=8)
        self.spin.grid(row=1, column=1, sticky="w", padx=20)
        self.check = ttk.Checkbutton(frame, text="Sobrescrever SVGs existentes após validar a nova saída", variable=self.overwrite)
        self.check.pack(anchor="w", pady=10)
        self.start = ttk.Button(frame, text="Converter arquivos", command=self.convert)
        self.start.pack(anchor="w")
        self.progress = ttk.Progressbar(frame, mode="determinate")
        self.progress.pack(fill="x", pady=12)
        self.status = ttk.Label(frame, text="Selecione os arquivos para começar.")
        self.status.pack(anchor="w")
        self.log = tk.Text(frame, height=8, wrap="word", state="disabled", font=("Consolas", 10))
        self.log.pack(fill="both", expand=True, pady=(8, 0))
        ttk.Label(frame, text="Fundo transparente preservado. Fotografias, degradês e sombras serão simplificados.").pack(anchor="w", pady=(8, 0))
        root.after(150, self.poll)

    def select(self):
        files = filedialog.askopenfilenames(title="Selecione arquivos PNG", filetypes=[("Imagens PNG", "*.png *.PNG")])
        if files:
            self.files = [Path(name) for name in files]
            self.listbox.delete(0, "end")
            for path in self.files:
                self.listbox.insert("end", str(path))
            self.status.configure(text=f"{len(self.files)} arquivo(s) selecionado(s).")

    def select_folder(self):
        folder = filedialog.askdirectory(title="Escolha a pasta dos SVGs")
        if folder:
            self.folder.set(folder)

    def set_busy(self, busy):
        self.busy = busy
        for control in [self.choose, self.entry, self.browse, self.spin, self.check, self.start]:
            control.configure(state="disabled" if busy else "normal")
        self.combo.configure(state="disabled" if busy else "readonly")

    def convert(self):
        if not self.files:
            messagebox.showinfo("Selecione os arquivos", "Selecione pelo menos um arquivo PNG.")
            return
        try:
            colors = int(self.colors.get())
            if not 1 <= colors <= 32:
                raise ValueError()
        except ValueError:
            messagebox.showerror("Cores inválidas", "Informe de 1 a 32 cores.")
            return
        folder = Path(self.folder.get()).expanduser().resolve() if self.folder.get().strip() else None
        settings = (list(self.files), folder, self.quality.get(), colors, self.overwrite.get())
        self.progress.configure(value=0, maximum=len(self.files))
        self.set_busy(True)
        self.status.configure(text="Convertendo…")
        Thread(target=self.process, args=settings, daemon=True).start()

    def process(self, files, folder, quality, colors, overwrite):
        failures = 0
        for index, source in enumerate(files, 1):
            output = (folder or source.parent) / (source.stem + ".svg")
            try:
                result = run_conversion(source, output, quality, colors, overwrite)
                text = f"OK: {output}\n    {result['paths']} formas; {result['colors']} cores; {result['bytes']:,} bytes."
            except Exception as error:
                failures += 1
                text = f"ERRO: {source.name}: {error}"
            self.events.put(("progress", index, text))
        self.events.put(("done", len(files) - failures, failures))

    def poll(self):
        try:
            while True:
                kind, first, second = self.events.get_nowait()
                if kind == "progress":
                    self.progress.configure(value=first)
                    self.log.configure(state="normal")
                    self.log.insert("end", second + "\n")
                    self.log.see("end")
                    self.log.configure(state="disabled")
                else:
                    self.set_busy(False)
                    self.status.configure(text=f"Concluído: {first} convertido(s), {second} erro(s).")
        except Empty:
            pass
        self.root.after(150, self.poll)

    def close(self):
        if self.busy:
            messagebox.showinfo("Conversão em andamento", "Aguarde o término antes de fechar.")
        else:
            self.root.destroy()


def launch():
    root = tk.Tk()
    App(root)
    root.mainloop()
