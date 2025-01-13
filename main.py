import pyautogui
import keyboard
from PIL import ImageGrab
import tkinter as tk
from ctypes import windll


class ColorPickerApp:
    def __init__(self):
        self.root = tk.Tk()
        self.canvas = tk.Toplevel(self.root)
        self.setup_windows()
        self.update_label()

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
            width=20,  # Фиксированная ширина в символах
            height=2,  # Фиксированная высота в строках
            anchor="w",  # Выравнивание текста по левому краю
            justify="left",
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
        return ImageGrab.grab(bbox=(x, y, x + 1, y + 1)).getpixel((0, 0))

    def move_window_safe(self, window, x, y, dx=0, dy=0):
        """Переместить окно, чтобы оно оставалось видимым и не перекрывало курсор."""
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()

        window_width = window.winfo_reqwidth()
        window_height = window.winfo_reqheight()

        x += dx
        y += dy

        if x + window_width > screen_width:
            x -= (window_width + 20)
        if y + window_height > screen_height:
            y -= (window_height + 20)
        if x < 0:
            x = 20
        if y < 0:
            y = 20

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
