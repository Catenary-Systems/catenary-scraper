import json
import os
import threading
import webbrowser
import io
import requests
import tkinter as tk
from tkinter import filedialog, messagebox
from tkinter.scrolledtext import ScrolledText
from PIL import Image, ImageTk
import sv_ttk
import codegen

OUT_JSON = os.path.join(os.path.dirname(__file__), "out.json")

THUMB_W, THUMB_H = 320, 240

def load_json(path):
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        messagebox.showerror("Error", f"Cannot load JSON: {e}")
        return []

class JsonViewer(tk.Tk):
    def __init__(self, json_path=None):
        super().__init__()
        self.title("out.json Visualizer")
        self.geometry("900x750")
        self.resizable(width=False, height=False)
        sv_ttk.set_theme("dark")
        self.json_path = json_path or OUT_JSON
        self.data = []
        self.image_cache = {}
        self._build_ui()
        self.load(self.json_path)

    def _build_ui(self):
        top = tk.Frame(self)
        top.pack(fill="x", padx=8, pady=6)

        tk.Label(top, text="JSON file:").pack(side="left")
        self.path_var = tk.StringVar(value=self.json_path)
        tk.Entry(top, textvariable=self.path_var, width=60).pack(side="left", padx=6)
        tk.Button(top, text="Browse", command=self.browse).pack(side="left", padx=4)
        tk.Button(top, text="Reload", command=lambda: self.load(self.path_var.get())).pack(side="left", padx=4)

        main = tk.PanedWindow(self, orient="horizontal")
        main.pack(fill="both", expand=True, padx=8, pady=6)

        # Left: list
        left_frame = tk.Frame(main)
        tk.Label(left_frame, text="Entries").pack(anchor="w")
        self.listbox = tk.Listbox(left_frame, width=45)
        self.listbox.pack(fill="both", expand=True, side="left")
        self.listbox.bind("<<ListboxSelect>>", self.on_select)
        scrollbar = tk.Scrollbar(left_frame, command=self.listbox.yview)
        scrollbar.pack(side="right", fill="y")
        self.listbox.config(yscrollcommand=scrollbar.set)

        main.add(left_frame)

        # Right: details + image
        right_frame = tk.Frame(main)
        info_frame = tk.Frame(right_frame)
        info_frame.pack(fill="x", pady=(0,6))

        self.url_var = tk.StringVar()
        self.price_var = tk.StringVar()
        self.code_var = tk.StringVar()
        self.bed_var = tk.StringVar()
        self.bath_var = tk.StringVar()
        self.floor_var = tk.StringVar()
        self.err_var = tk.StringVar()

        def label_row(parent, label, var):
            row = tk.Frame(parent)
            row.pack(fill="x")
            tk.Label(row, text=label, width=10, anchor="w").pack(side="left")
            tk.Label(row, textvariable=var, anchor="w", wraplength=420).pack(side="left", fill="x", expand=True)

        label_row(info_frame, "URL:", self.url_var)
        label_row(info_frame, "Price:", self.price_var)
        label_row(info_frame, "Code:", self.code_var)
        label_row(info_frame, "Beds:", self.bed_var)
        label_row(info_frame, "Baths:", self.bath_var)
        label_row(info_frame, "Floor:", self.floor_var)
        label_row(info_frame, "Error:", self.err_var)

        btn_row = tk.Frame(right_frame)
        btn_row.pack(fill="x", pady=(0,6))
        tk.Button(btn_row, text="Open URL", command=self.open_url).pack(side="left")
        tk.Button(btn_row, text="Show all images", command=self.show_images).pack(side="left", padx=6)

        # image area + description
        self.image_label = tk.Label(right_frame, text="No image", width=THUMB_W, height=THUMB_H, bg="#222")
        self.image_label.pack(pady=6)

        tk.Label(right_frame, text="Description:").pack(anchor="w")
        self.desc_text = ScrolledText(right_frame, height=8, wrap="word")
        self.desc_text.pack(fill="both", expand=True)

        main.add(right_frame)

    def browse(self):
        p = filedialog.askopenfilename(title="Select out.json", filetypes=[("JSON files","*.json"),("All files","*.*")])
        if p:
            self.path_var.set(p)
            self.load(p)

    def load(self, path):
        if not path or not os.path.exists(path):
            messagebox.showerror("Error", f"File not found: {path}")
            return
        self.json_path = path
        self.data = load_json(path) or []
        self.listbox.delete(0, "end")
        for i, entry in enumerate(self.data):
            label = entry.get("code") or entry.get("price") or entry.get("url") or f"entry {i}"
            # include error marker
            if "error" in entry:
                label = f"[ERR] {label}"
            self.listbox.insert("end", f"{i+1}. {label}")
        if self.data:
            self.listbox.selection_set(0)
            self.on_select()

    def on_select(self, *ev):
        sel = self.listbox.curselection()
        if not sel:
            return
        idx = sel[0]
        entry = self.data[idx]
        self.url_var.set(entry.get("url", ""))
        self.price_var.set(entry.get("price", ""))
        self.code_var.set(entry.get("code", ""))
        self.bed_var.set(entry.get("bedrooms", ""))
        self.bath_var.set(entry.get("bathrooms", ""))
        self.floor_var.set(entry.get("floor", ""))
        self.err_var.set(entry.get("error", ""))
        self.desc_text.delete("1.0", "end")
        self.desc_text.insert("end", entry.get("description", ""))
        # load first image if present
        imgs = entry.get("images") or []
        if imgs:
            self._show_thumbnail(imgs[0])
        else:
            self._clear_image()

    def _clear_image(self):
        self.image_label.config(image="", text="No image")

    def _show_thumbnail(self, url):
        if url in self.image_cache:
            tkimg = self.image_cache[url]
            self.image_label.config(image=tkimg, text="")
            return

        self.image_label.config(text="Loading...")
        def worker():
            try:
                resp = requests.get(url, timeout=8)
                resp.raise_for_status()
                img = Image.open(io.BytesIO(resp.content)).convert("RGBA")
                img.thumbnail((THUMB_W, THUMB_H), Image.LANCZOS)
                tkimg = ImageTk.PhotoImage(img)
                self.image_cache[url] = tkimg
                # update on main thread
                self.image_label.after(0, lambda: self.image_label.config(image=tkimg, text=""))
            except Exception:
                self.image_label.after(0, lambda: self.image_label.config(text="Failed to load"))
        threading.Thread(target=worker, daemon=True).start()

    def show_images(self):
        sel = self.listbox.curselection()
        if not sel:
            return
        entry = self.data[sel[0]]
        imgs = entry.get("images") or []
        if not imgs:
            messagebox.showinfo("Images", "No images for this entry")
            return
        # open simple gallery window
        win = tk.Toplevel(self)
        win.title("Images")
        win.geometry("800x600")
        win.resizable(width=False, height=False)
        frame = tk.Frame(win)
        frame.pack(fill="both", expand=True)
        canvas = tk.Canvas(frame, bg="#111")
        canvas.pack(fill="both", expand=True, side="left")
        sb = tk.Scrollbar(frame, command=canvas.yview)
        sb.pack(side="right", fill="y")
        canvas.configure(yscrollcommand=sb.set)
        inner = tk.Frame(canvas)
        canvas.create_window((0,0), window=inner, anchor="nw")

        def populate():
            for u in imgs:
                lbl = tk.Label(inner, text="Loading...", bg="#222", fg="#fff")
                lbl.pack(padx=6, pady=6)
                def load_label(url=u, label=lbl):
                    try:
                        r = requests.get(url, timeout=8)
                        r.raise_for_status()
                        img = Image.open(io.BytesIO(r.content)).convert("RGBA")
                        img.thumbnail((700, 700), Image.LANCZOS)
                        tkimg = ImageTk.PhotoImage(img)
                        label.config(image=tkimg, text="")
                        # keep ref
                        label.image = tkimg
                    except Exception:
                        label.config(text="Failed to load")
                threading.Thread(target=load_label, daemon=True).start()

        def on_config(event):
            canvas.configure(scrollregion=canvas.bbox("all"))
        inner.bind("<Configure>", on_config)
        populate()

    def open_url(self):
        url = self.url_var.get()
        if url:
            webbrowser.open(url)

def veiwer():
    app = JsonViewer()
    app.mainloop()

if __name__ == "__main__":
    veiwer()

