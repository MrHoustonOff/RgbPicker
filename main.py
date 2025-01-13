import pyautogui
import keyboard
from PIL import Image
import tkinter as tk
from ctypes import windll
from screeninfo import get_monitors
import mss  # Новая библиотека для захвата экрана


class ColorPickerApp:
    def __init__(self):
        self.root = tk.Tk()
        self.canvas = tk.Toplevel(self.root)
        self.monitors = self.get_monitors_info()
        self.sct = mss.mss()  # Инициализация mss
        self.setup_windows()
        self.update_label()

    def get_monitors_info(self):
        """Получить информацию обо всех мониторах."""
        return get_monitors()

    def get_current_monitor(self, x, y):
        """Определить, на каком мониторе находится курсор."""
        for monitor in self.monitors:
            if (
                monitor.x <= x < monitor.x + monitor.width
                and monitor.y <= y < monitor.y + monitor.height
            ):
                return monitor
        return None

    def setup_windows(self):
        """Настройка основных окон."""
        self.root.overrideredirect(True)
        self.root.attributes("-topmost", True)
        self.root.withdraw()

        self.frame = tk.Frame(self.root, bg="black", padx=5, pady=5)
        self.frame.pack()

        # Задаём фиксированный размер для лейбла
        self.label = tk.Label(
            self.frame,
            text="",
            font=("Consolas", 12),
            bg="black",
            fg="white",
            padx=5,
            pady=5,
            width=20,
            height=2,
            anchor="center",
            justify="center",
        )
        self.label.pack(side=tk.LEFT)

        # Фиксированный размер квадрата для превью цвета
        self.color_preview = tk.Canvas(
            self.frame, width=30, height=30, bg="black", highlightthickness=0
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

    def get_pixel_color(self, x, y):
        """Получить цвет пикселя на указанных координатах."""
        monitor = self.get_current_monitor(x, y)
        if not monitor:
            return 0, 0, 0  # Если монитор не найден, возвращаем черный цвет

        # Настраиваем область для mss
        monitor_region = {
            "top": y,
            "left": x,
            "width": 1,
            "height": 1,
        }

        # Захватываем пиксель
        sct_img = self.sct.grab(monitor_region)
        return sct_img.pixel(0, 0)  # Получаем цвет пикселя

    def move_window_safe(self, window, x, y, dx=0, dy=0):
        """Переместить окно на корректное место на экране с учетом всех мониторов."""
        monitor = self.get_current_monitor(x, y)
        if not monitor:
            return  # Если монитор не найден, ничего не делаем

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
        """Скрыть все окна."""
        self.root.withdraw()
        self.canvas.withdraw()

    def update_label(self):
        """Обновление информации в режиме реального времени."""
        if not (keyboard.is_pressed("ctrl") and keyboard.is_pressed("shift")):
            self.hide_windows()
            self.root.after(100, self.update_label)
            return

        try:
            x, y = pyautogui.position()
            r, g, b = self.get_pixel_color(x, y)
            r_percentage = r / 255
            new_text = f"R: {r:<3} G: {g:<3} B: {b:<3}\nMap: {r_percentage:.2%}"

            if self.label["text"] != new_text:
                self.label.config(text=new_text)

            self.color_preview.delete("all")
            self.color_preview.create_rectangle(
                5, 5, 25, 25, fill=f"#{r:02x}{g:02x}{b:02x}", outline=""
            )

            self.move_window_safe(self.root, x, y, dx=20, dy=20)
            self.root.deiconify()

            self.move_window_safe(self.canvas, x, y, dx=-3, dy=-3)
            self.canvas.deiconify()
        except Exception as e:
            print(f"Ошибка обновления: {e}")

        self.root.after(50, self.update_label)


if __name__ == "__main__":
    app = ColorPickerApp()
    app.root.mainloop()
