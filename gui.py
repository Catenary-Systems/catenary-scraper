# ...existing code...
import threading
import tkinter as tk
from tkinter import filedialog, messagebox
import sv_ttk
import os
import scraper
from tkinter import ttk
import graph as g
import codegen

VERSION=codegen.ver()


def browse_file(entry_var):
    path = filedialog.askopenfilename(
        title="Select links file",
        filetypes=[("Text files", "*.txt"), ("All files", "*.*")]
    )
    if path:
        entry_var.set(path)

def run_scraper(filepath_var, run_btn, status_var, log_text):
    path = filepath_var.get().strip()
    if not path:
        messagebox.showwarning("No file", "Please choose an input file.")
        return

    if not os.path.exists(path):
        messagebox.showerror("File not found", f"File does not exist:\n{path}")
        return

    def worker():
        try:
            run_btn.config(state="disabled")
            status_var.set("Running...")
            log_text.configure(state="normal")
            log_text.delete("1.0", "end")
            log_text.insert("end", f"Catenary Systems Scraper v{VERSION}\n")
            log_text.insert("end", f"Starting scraper for: {path}\n")
            log_text.configure(state="disabled")

            result = scraper.main(path)

            messagebox.showinfo("Done", f"Scraping finished.")
            status_var.set(f"Done")
            log_text.configure(state="normal")
            log_text.insert("end", f"Saved to: out.json\n")
            log_text.configure(state="disabled")
        finally:
            run_btn.config(state="normal")
            os.system("python graph.py")  # Open the viewer


    threading.Thread(target=worker, daemon=True).start()

def build_gui():
    root = tk.Tk()
    root.title("Scraper GUI")
    root.geometry("600x300")
    root.resizable(width=False, height=False)
    sv_ttk.set_theme("dark")

    frame = ttk.Frame(root)
    frame.pack(fill="both", expand=True, padx=12, pady=12)

    filepath_var = tk.StringVar()
    status_var = tk.StringVar(value="Idle")

    # input row
    row = ttk.Frame(frame)
    row.pack(fill="x", pady=12)
    ttk.Label(row, text="Links file:", width=10, anchor="w").pack(side="left")
    entry = ttk.Entry(row, textvariable=filepath_var)
    entry.pack(side="left", fill="x", expand=True, padx=(6,6), pady=(2,0))
    ttk.Button(row, text="Browse", command=lambda: browse_file(filepath_var)).pack(side="left")

    # run button and status
    row2 = ttk.Frame(frame)
    row2.pack(fill="x", pady=6)
    run_btn = ttk.Button(row2, text="Run", width=12,
                        command=lambda: run_scraper(filepath_var, run_btn, status_var, log_text))
    run_btn.pack(side="left")
    ttk.Label(row2, textvariable=status_var, anchor="w").pack(side="left", padx=12)

    # log area
    from tkinter.scrolledtext import ScrolledText
    log_text = ScrolledText(frame, height=10, state="disabled")
    log_text.pack(fill="both", expand=True, pady=(6,0))

    root.mainloop()

if __name__ == "__main__":
    build_gui()
# ...existing code...