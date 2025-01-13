import sys

import pyautogui
import keyboard
import tkinter as tk
from ctypes import windll
from screeninfo import get_monitors
import mss
import json
import os
import platform
from typing import Optional, Tuple
from tkinter import messagebox
import pystray
from pystray import MenuItem as item
from PIL import Image, ImageDraw

PREVIEW_SIZE = 30
LABEL_WIDTH = 20
LABEL_HEIGHT = 2
DEFAULT_CONFIG = {
    "update_interval": 16,
    "main_hotkey": ["ctrl", "shift"],
    "settings_hotkey": ["ctrl", "alt", "i"]
}

def get_config_path() -> str:
    if platform.system() == "Windows":
        app_data_dir = os.getenv("LOCALAPPDATA", os.path.expanduser("~\\AppData\\Local"))
    elif platform.system() == "Darwin":  # macOS
        app_data_dir = os.path.expanduser("~/Library/Application Support")
    else:
        app_data_dir = os.getenv("XDG_CONFIG_HOME", os.path.expanduser("~/.config"))

    app_folder = os.path.join(app_data_dir, "BestRgbPicker")
    os.makedirs(app_folder, exist_ok=True)
    return os.path.join(app_folder, "config.json")

CONFIG_FILE = get_config_path()

class ColorPickerApp:
    def __init__(self):
        self.iconPath = icon_path = os.path.join(os.path.dirname(__file__), 'favicon.ico')
        self.config = self.load_config()
        self.update_interval = self.config["update_interval"]
        self.main_hotkey = set(self.config["main_hotkey"])

        self.root = tk.Tk()
        self.canvas = tk.Toplevel(self.root)
        self.monitors = self.get_monitors_info()
        self.sct = mss.mss()
        self.current_color = None

        self.setup_windows()
        self.create_settings_window()
        self.update_label()

        # Инициализация трея
        self.icon = self.create_tray_icon()
        self.icon.run_detached()  # Запускаем трей в отдельном потоке

    def create_tray_icon(self):
        icon_image = Image.open(self.iconPath)  # Замените на путь к вашему файлу
        icon_image = icon_image.resize((32, 32))

        menu = (item('Settings', self.show_settings_window),
                item('Exit', self.exit_program))

        icon = pystray.Icon("RGB Picker", icon_image, menu=menu)
        return icon

    def exit_program(self, icon, item):
        icon.stop()  # Останавливаем pystray
        self.root.quit()  # Завершаем главный цикл tkinter
        sys.exit()  # Завершаем процесс

    def load_config(self):
        if not os.path.exists(CONFIG_FILE):
            self.save_config(DEFAULT_CONFIG)
            return DEFAULT_CONFIG
        try:
            with open(CONFIG_FILE, "r") as file:
                return json.load(file)
        except (json.JSONDecodeError, IOError):
            print("Ошибка загрузки конфигурации. Используются настройки по умолчанию.")
            return DEFAULT_CONFIG

    def save_config(self, config):
        try:
            with open(CONFIG_FILE, "w") as file:
                json.dump(config, file, indent=4)
        except IOError:
            print("Ошибка сохранения конфигурации.")

    def get_monitors_info(self):
        return get_monitors()

    def get_current_monitor(self, x: int, y: int) -> Optional[object]:
        for monitor in self.monitors:
            if monitor.x <= x < monitor.x + monitor.width and monitor.y <= y < monitor.y + monitor.height:
                return monitor
        return self.monitors[0]  # Fallback: основной монитор

    def setup_windows(self):
        self.root.overrideredirect(True)
        self.root.attributes("-topmost", True)
        self.root.withdraw()

        self.frame = tk.Frame(self.root, bg="black", padx=5, pady=5)
        self.frame.pack()

        self.label = tk.Label(
            self.frame,
            text="",
            font=("Consolas", 12),
            bg="black",
            fg="white",
            padx=5,
            pady=5,
            width=LABEL_WIDTH,
            height=LABEL_HEIGHT,
            anchor="center",
            justify="center",
        )
        self.label.pack(side=tk.LEFT)

        self.color_preview = tk.Canvas(
            self.frame, width=PREVIEW_SIZE, height=PREVIEW_SIZE, bg="black", highlightthickness=0
        )
        self.color_preview.pack(side=tk.LEFT, padx=5)

        self.canvas.overrideredirect(True)
        self.canvas.attributes("-topmost", True, "-transparentcolor", "white")
        self.canvas.withdraw()

        frame = tk.Canvas(self.canvas, width=7, height=7, bg="white", highlightthickness=0)
        frame.pack()

        frame.create_rectangle(0, 0, 7, 1, fill="red", outline="")
        frame.create_rectangle(0, 6, 7, 7, fill="red", outline="")
        frame.create_rectangle(0, 0, 1, 7, fill="red", outline="")
        frame.create_rectangle(6, 0, 7, 7, fill="red", outline="")

        hwnd = windll.user32.GetParent(self.canvas.winfo_id())
        windll.user32.SetLayeredWindowAttributes(hwnd, 0x00FFFFFF, 0, 1)

    def create_settings_window(self):
        if hasattr(self, "settings_window") and self.settings_window.winfo_exists():
            self.settings_window.destroy()

        self.settings_window = tk.Toplevel(self.root)
        self.settings_window.title("Settings")
        self.settings_window.geometry("300x350")
        self.settings_window.configure(bg="black")
        self.settings_window.withdraw()

        tk.Label(self.settings_window, text="Update Interval (ms):", bg="black", fg="white").pack(pady=5)
        self.update_interval_slider = tk.Scale(
            self.settings_window, from_=1, to=100, orient=tk.HORIZONTAL, bg="black", fg="white", troughcolor="gray"
        )
        self.update_interval_slider.set(self.update_interval)
        self.update_interval_slider.pack(pady=5)

        tk.Label(self.settings_window, text="Main Hotkey (e.g., ctrl+shift):", bg="black", fg="white").pack(pady=5)
        self.main_hotkey_entry = tk.Entry(self.settings_window, bg="gray", fg="white", insertbackground="white")
        self.main_hotkey_entry.insert(0, "+".join(self.config["main_hotkey"]))
        self.main_hotkey_entry.pack(pady=5)

        tk.Label(self.settings_window, text="Made By MrHouston", bg="black", fg="white", anchor="e").pack(
            side=tk.BOTTOM, pady=5, padx=5)

        save_button = tk.Button(
            self.settings_window, text="Save Settings", command=self.save_settings, bg="gray", fg="white"
        )
        save_button.pack(pady=10)

    def save_settings(self):
        try:
            update_interval = int(self.update_interval_slider.get())
            main_hotkey = self.main_hotkey_entry.get().split("+")

            if not self.validate_hotkey(main_hotkey):
                messagebox.showerror("Invalid Input", "Invalid main hotkey. Please check the format.")
                return

            self.config.update({
                "update_interval": update_interval,
                "main_hotkey": main_hotkey
            })

            self.save_config(self.config)

            self.update_interval = update_interval
            self.main_hotkey = set(main_hotkey)

            print("Settings saved successfully.")
            self.settings_window.withdraw()

        except ValueError:
            print("Invalid settings. Please check your input.")

    def validate_hotkey(self, hotkey: list) -> bool:
        if not hotkey or any(not key.strip() for key in hotkey):
            return False
        try:
            keyboard.parse_hotkey("+".join(hotkey))
            return True
        except ValueError:
            return False

    def show_settings_window(self):
        try:
            if not self.settings_window.winfo_exists():
                self.create_settings_window()
            self.settings_window.deiconify()
            self.settings_window.focus_set()
        except tk.TclError as e:
            print(f"Ошибка показа окна настроек: {e}")

    def get_pixel_color(self, x: int, y: int) -> Tuple[int, int, int]:
        monitor = self.get_current_monitor(x, y)
        if not monitor:
            return 0, 0, 0

        monitor_region = {"top": y, "left": x, "width": 1, "height": 1}
        sct_img = self.sct.grab(monitor_region)
        return sct_img.pixel(0, 0)

    def move_window_safe(self, window, x: int, y: int, dx: int = 0, dy: int = 0):
        monitor = self.get_current_monitor(x, y)
        if not monitor:
            return

        screen_x, screen_y, screen_width, screen_height = (
            monitor.x,
            monitor.y,
            monitor.width,
            monitor.height,
        )

        window_width = window.winfo_reqwidth()
        window_height = window.winfo_reqheight()

        x += dx
        y += dy

        if x + window_width > screen_x + screen_width:
            x -= (window_width + 20)
        if y + window_height > screen_y + screen_height:
            y -= (window_height + 20)
        if x < screen_x:
            x = screen_x + 20
        if y < screen_y:
            y = screen_y + 20

        window.geometry(f"+{x}+{y}")

    def hide_windows(self):
        self.root.withdraw()
        self.canvas.withdraw()

    def update_label(self):
        if not all(keyboard.is_pressed(k) for k in self.main_hotkey):
            self.hide_windows()
            self.root.after(self.update_interval, self.update_label)
            return

        try:
            x, y = pyautogui.position()
            r, g, b = self.get_pixel_color(x, y)
            r_percentage = r / 255
            new_text = f"R: {r:<3} G: {g:<3} B: {b:<3}\nMap: {r_percentage:.2%}"

            if self.label["text"] != new_text:
                self.label.config(text=new_text)

            if self.current_color != (r, g, b):
                self.color_preview.delete("all")
                self.color_preview.create_rectangle(
                    5, 5, 25, 25, fill=f"#{r:02x}{g:02x}{b:02x}", outline=""
                )
                self.current_color = (r, g, b)

            self.move_window_safe(self.root, x, y, dx=20, dy=20)
            self.root.deiconify()

            self.move_window_safe(self.canvas, x, y, dx=-3, dy=-3)
            self.canvas.deiconify()
        except Exception as e:
            print(f"Ошибка обновления (X: {x}, Y: {y}): {e}")

        self.root.after(self.update_interval, self.update_label)


if __name__ == "__main__":
    app = ColorPickerApp()
    keyboard.add_hotkey("+".join(DEFAULT_CONFIG["settings_hotkey"]), app.show_settings_window)
    app.root.mainloop()
