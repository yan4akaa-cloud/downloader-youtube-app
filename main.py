import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
import threading
import os
import sys
from pathlib import Path
import yt_dlp


class VideoDownloaderApp:
    def __init__(self, root):
        self.root = root
        self.root.title("YouTube & Pinterest Video Downloader")
        self.root.geometry("800x600")
        self.root.resizable(False, False)
        
        # Переменные
        self.download_path = tk.StringVar(value=str(Path.home() / "Downloads"))
        self.url = tk.StringVar()
        self.quality = tk.StringVar(value="best")
        self.is_downloading = False
        
        self.setup_ui()
        
    def setup_ui(self):
        # Основной контейнер
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Заголовок
        title_label = ttk.Label(main_frame, text="Загрузчик видео с YouTube и Pinterest", 
                               font=("Arial", 16, "bold"))
        title_label.grid(row=0, column=0, columnspan=3, pady=10)
        
        # URL ввод
        url_label = ttk.Label(main_frame, text="URL видео:", font=("Arial", 10))
        url_label.grid(row=1, column=0, sticky=tk.W, pady=5)
        
        url_entry = ttk.Entry(main_frame, textvariable=self.url, width=70)
        url_entry.grid(row=2, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=5)
        
        # Качество видео
        quality_label = ttk.Label(main_frame, text="Качество:", font=("Arial", 10))
        quality_label.grid(row=3, column=0, sticky=tk.W, pady=5)
        
        quality_frame = ttk.Frame(main_frame)
        quality_frame.grid(row=4, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=5)
        
        qualities = [
            ("Лучшее (best)", "best"),
            ("4K (2160p)", "2160"),
            ("Full HD (1080p)", "1080"),
            ("HD (720p)", "720"),
            ("SD (480p)", "480"),
            ("Только аудио (mp3)", "audio")
        ]
        
        for idx, (text, value) in enumerate(qualities):
            rb = ttk.Radiobutton(quality_frame, text=text, variable=self.quality, value=value)
            rb.grid(row=0, column=idx, padx=5)
        
        # Путь сохранения
        path_label = ttk.Label(main_frame, text="Папка сохранения:", font=("Arial", 10))
        path_label.grid(row=5, column=0, sticky=tk.W, pady=5)
        
        path_frame = ttk.Frame(main_frame)
        path_frame.grid(row=6, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=5)
        
        path_entry = ttk.Entry(path_frame, textvariable=self.download_path, width=60)
        path_entry.grid(row=0, column=0, sticky=(tk.W, tk.E), padx=(0, 5))
        
        browse_button = ttk.Button(path_frame, text="Обзор...", command=self.browse_folder)
        browse_button.grid(row=0, column=1)
        
        path_frame.columnconfigure(0, weight=1)
        
        # Кнопки действий
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=7, column=0, columnspan=3, pady=15)
        
        self.download_button = ttk.Button(button_frame, text="Скачать видео", 
                                         command=self.start_download, width=20)
        self.download_button.grid(row=0, column=0, padx=5)
        
        self.info_button = ttk.Button(button_frame, text="Получить информацию", 
                                     command=self.get_video_info, width=20)
        self.info_button.grid(row=0, column=1, padx=5)
        
        clear_button = ttk.Button(button_frame, text="Очистить", 
                                 command=self.clear_log, width=15)
        clear_button.grid(row=0, column=2, padx=5)
        
        # Прогресс бар
        self.progress = ttk.Progressbar(main_frame, mode='indeterminate')
        self.progress.grid(row=8, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=5)
        
        # Лог
        log_label = ttk.Label(main_frame, text="Лог операций:", font=("Arial", 10))
        log_label.grid(row=9, column=0, sticky=tk.W, pady=5)
        
        self.log_text = scrolledtext.ScrolledText(main_frame, height=15, width=90, 
                                                  wrap=tk.WORD, state='disabled')
        self.log_text.grid(row=10, column=0, columnspan=3, sticky=(tk.W, tk.E, tk.N, tk.S), pady=5)
        
        # Информация внизу
        info_label = ttk.Label(main_frame, 
                              text="Поддерживаются: YouTube, YouTube Music, Pinterest и другие сайты",
                              font=("Arial", 8), foreground="gray")
        info_label.grid(row=11, column=0, columnspan=3, pady=5)
        
        # Конфигурация весов
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(0, weight=1)
        main_frame.rowconfigure(10, weight=1)
    
    def browse_folder(self):
        folder = filedialog.askdirectory(initialdir=self.download_path.get())
        if folder:
            self.download_path.set(folder)
    
    def log(self, message):
        self.log_text.config(state='normal')
        self.log_text.insert(tk.END, f"{message}\n")
        self.log_text.see(tk.END)
        self.log_text.config(state='disabled')
        self.root.update()
    
    def clear_log(self):
        self.log_text.config(state='normal')
        self.log_text.delete(1.0, tk.END)
        self.log_text.config(state='disabled')
    
    def progress_hook(self, d):
        if d['status'] == 'downloading':
            try:
                percent = d.get('_percent_str', 'N/A')
                speed = d.get('_speed_str', 'N/A')
                eta = d.get('_eta_str', 'N/A')
                self.log(f"Загрузка: {percent} | Скорость: {speed} | Осталось: {eta}")
            except:
                pass
        elif d['status'] == 'finished':
            self.log("Загрузка завершена! Обработка файла...")
    
    def get_ydl_opts(self):
        output_template = os.path.join(self.download_path.get(), '%(title)s.%(ext)s')
        
        opts = {
            'outtmpl': output_template,
            'progress_hooks': [self.progress_hook],
            'quiet': False,
            'no_warnings': False,
        }
        
        quality = self.quality.get()
        
        if quality == "audio":
            opts['format'] = 'bestaudio/best'
            opts['postprocessors'] = [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }]
        elif quality == "best":
            opts['format'] = 'bestvideo+bestaudio/best'
            opts['merge_output_format'] = 'mp4'
        else:
            # Для конкретного разрешения
            opts['format'] = f'bestvideo[height<={quality}]+bestaudio/best[height<={quality}]'
            opts['merge_output_format'] = 'mp4'
        
        return opts
    
    def download_video(self):
        url = self.url.get().strip()
        
        if not url:
            messagebox.showwarning("Предупреждение", "Пожалуйста, введите URL видео!")
            return
        
        if not os.path.exists(self.download_path.get()):
            messagebox.showerror("Ошибка", "Указанная папка не существует!")
            return
        
        try:
            self.is_downloading = True
            self.download_button.config(state='disabled')
            self.info_button.config(state='disabled')
            self.progress.start(10)
            
            self.log(f"Начало загрузки: {url}")
            self.log(f"Качество: {self.quality.get()}")
            self.log(f"Сохранение в: {self.download_path.get()}")
            self.log("-" * 80)
            
            ydl_opts = self.get_ydl_opts()
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([url])
            
            self.log("-" * 80)
            self.log("✓ Видео успешно загружено!")
            messagebox.showinfo("Успех", "Видео успешно загружено!")
            
        except Exception as e:
            self.log(f"✗ Ошибка: {str(e)}")
            messagebox.showerror("Ошибка", f"Не удалось загрузить видео:\n{str(e)}")
        
        finally:
            self.is_downloading = False
            self.download_button.config(state='normal')
            self.info_button.config(state='normal')
            self.progress.stop()
    
    def start_download(self):
        if not self.is_downloading:
            thread = threading.Thread(target=self.download_video, daemon=True)
            thread.start()
    
    def get_info(self):
        url = self.url.get().strip()
        
        if not url:
            messagebox.showwarning("Предупреждение", "Пожалуйста, введите URL видео!")
            return
        
        try:
            self.download_button.config(state='disabled')
            self.info_button.config(state='disabled')
            self.progress.start(10)
            
            self.log(f"Получение информации о: {url}")
            self.log("-" * 80)
            
            ydl_opts = {
                'quiet': True,
                'no_warnings': True,
            }
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)
                
                self.log(f"Название: {info.get('title', 'N/A')}")
                self.log(f"Автор: {info.get('uploader', 'N/A')}")
                self.log(f"Длительность: {info.get('duration', 0)} секунд")
                self.log(f"Просмотров: {info.get('view_count', 'N/A')}")
                self.log(f"Описание: {info.get('description', 'N/A')[:200]}...")
                
                if 'formats' in info:
                    self.log(f"\nДоступные форматы: {len(info['formats'])}")
                    
                    # Показываем топ форматы
                    video_formats = [f for f in info['formats'] if f.get('vcodec') != 'none']
                    if video_formats:
                        self.log("\nТоп видео форматы:")
                        for fmt in video_formats[-5:]:
                            resolution = fmt.get('resolution', 'N/A')
                            ext = fmt.get('ext', 'N/A')
                            filesize = fmt.get('filesize', 0)
                            size_mb = filesize / (1024*1024) if filesize else 0
                            self.log(f"  - {resolution} ({ext}) - {size_mb:.1f} MB")
            
            self.log("-" * 80)
            self.log("✓ Информация получена успешно!")
            
        except Exception as e:
            self.log(f"✗ Ошибка: {str(e)}")
            messagebox.showerror("Ошибка", f"Не удалось получить информацию:\n{str(e)}")
        
        finally:
            self.download_button.config(state='normal')
            self.info_button.config(state='normal')
            self.progress.stop()
    
    def get_video_info(self):
        thread = threading.Thread(target=self.get_info, daemon=True)
        thread.start()


def main():
    root = tk.Tk()
    app = VideoDownloaderApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()

