import os
import psutil
import threading
import time
import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
from datetime import datetime
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
import ctypes

# ====== CONFIGURABLE SETTINGS ======
SUSPICIOUS_KEYWORDS = ["keylogger", "pynput", "pyxhook", "keyboardhook", "keycapture"]
LOG_FILE = "keylogger_detections.log"
CHECK_INTERVAL = 5  # seconds
ALERT_EMAIL = "youremail@example.com"
SENDER_EMAIL = "sender@example.com"
SENDER_PASSWORD = "your_password"
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587

# ====== DETECTION FUNCTION ======
def is_suspicious(proc):
    try:
        name = proc.name().lower()
        cmdline = ' '.join(proc.cmdline()).lower()
        for keyword in SUSPICIOUS_KEYWORDS:
            if keyword in name or keyword in cmdline:
                return True
        return False
    except (psutil.AccessDenied, psutil.NoSuchProcess):
        return False

def log_detection(proc):
    with open(LOG_FILE, 'a') as log:
        log.write(f"[{datetime.now()}] Detected: {proc.name()} | PID: {proc.pid} | Path: {proc.exe()}\n")

def send_email_alert():
    try:
        msg = MIMEMultipart()
        msg['From'] = SENDER_EMAIL
        msg['To'] = ALERT_EMAIL
        msg['Subject'] = "⚠️ Keylogger Detected!"

        body = "A suspicious keylogger process has been detected and logged."
        msg.attach(MIMEText(body, 'plain'))

        attachment = open(LOG_FILE, 'rb')
        part = MIMEBase('application', 'octet-stream')
        part.set_payload(attachment.read())
        encoders.encode_base64(part)
        part.add_header('Content-Disposition', f"attachment; filename= {LOG_FILE}")
        msg.attach(part)

        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.starttls()
        server.login(SENDER_EMAIL, SENDER_PASSWORD)
        text = msg.as_string()
        server.sendmail(SENDER_EMAIL, ALERT_EMAIL, text)
        server.quit()
    except Exception as e:
        print("Failed to send email:", e)

def show_alert(proc):
    ctypes.windll.user32.MessageBoxW(0, f"Suspicious keylogger process detected:\n{proc.name()} (PID: {proc.pid})", "Keylogger Alert!", 0x30)

# ====== BACKGROUND MONITORING ======
def monitor_processes(gui_callback):
    while True:
        for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
            if is_suspicious(proc):
                log_detection(proc)
                send_email_alert()
                show_alert(proc)
                try:
                    proc.terminate()
                except Exception:
                    pass
                gui_callback(f"[{datetime.now()}] Blocked {proc.name()} (PID: {proc.pid})")
        time.sleep(CHECK_INTERVAL)

# ====== GUI COMPONENT ======
class KeyloggerBlockerGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Keylogger Blocker")
        self.root.geometry("600x400")

        self.status_label = ttk.Label(root, text="Status: Monitoring...", font=("Segoe UI", 12))
        self.status_label.pack(pady=10)

        self.log_box = scrolledtext.ScrolledText(root, height=15, width=70)
        self.log_box.pack(pady=10)

        self.scan_button = ttk.Button(root, text="Manual Scan", command=self.manual_scan)
        self.scan_button.pack(pady=5)

        self.load_logs()

        # Start background thread
        threading.Thread(target=monitor_processes, args=(self.add_log,), daemon=True).start()

    def manual_scan(self):
        found = False
        for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
            if is_suspicious(proc):
                log_detection(proc)
                self.add_log(f"[{datetime.now()}] Manually found: {proc.name()} (PID: {proc.pid})")
                try:
                    proc.terminate()
                    self.add_log(f"[{datetime.now()}] Terminated {proc.name()} manually")
                except:
                    self.add_log(f"[{datetime.now()}] Could not terminate {proc.name()}")
                send_email_alert()
                show_alert(proc)
                found = True
        if not found:
            self.add_log(f"[{datetime.now()}] Manual scan: No suspicious processes found")

    def add_log(self, text):
        self.log_box.insert(tk.END, text + '\n')
        self.log_box.see(tk.END)

    def load_logs(self):
        if os.path.exists(LOG_FILE):
            with open(LOG_FILE, 'r') as file:
                self.log_box.insert(tk.END, file.read())

# ====== MAIN ENTRY POINT ======
if __name__ == "__main__":
    root = tk.Tk()
    app = KeyloggerBlockerGUI(root)
    root.mainloop()
