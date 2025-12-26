# -*- coding: utf-8 -*-
"""
YouTube & Pinterest Video Downloader - Enhanced Edition
Version 3.0 - All Features Included
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
from tkinterdnd2 import DND_FILES, TkinterDnD  # Для Drag & Drop
import threading
import os
import sys
from pathlib import Path
import yt_dlp
import subprocess
import multiprocessing
import sqlite3
import json
from datetime import datetime
from queue import Queue
import urllib.request
from PIL import Image, ImageTk
import io
from themes import apply_theme


class DownloadHistory:
    """Класс для работы с историей загрузок"""
    
    def __init__(self):
        self.db_path = Path.home() / ".videodownloader" / "history.db"
        self.db_path.parent.mkdir(exist_ok=True)
        self.init_database()
    
    def init_database(self):
        """Инициализация базы данных"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute('''
                CREATE TABLE IF NOT EXISTS downloads (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    url TEXT NOT NULL,
                    title TEXT,
                    quality TEXT,
                    filename TEXT,
                    size INTEGER,
                    download_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    status TEXT DEFAULT 'completed'
                )
            ''')
            conn.commit()
    
    def add_download(self, url, title, quality, filename, size=0):
        """Добавить запись о загрузке"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                'INSERT INTO downloads (url, title, quality, filename, size) VALUES (?, ?, ?, ?, ?)',
                (url, title, quality, filename, size)
            )
            conn.commit()
    
    def get_history(self, limit=100):
        """Получить историю загрузок"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                'SELECT * FROM downloads ORDER BY download_date DESC LIMIT ?',
                (limit,)
            )
            return cursor.fetchall()
    
    def clear_history(self):
        """Очистить историю"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute('DELETE FROM downloads')
            conn.commit()


class Config:
    """Класс для работы с конфигурацией и пресетами"""
    
    def __init__(self):
        self.config_path = Path.home() / ".videodownloader" / "config.json"
        self.config_path.parent.mkdir(exist_ok=True)
        self.default_config = {
            'theme': 'default',
            'last_download_path': str(Path.home() / "Downloads"),
            'speed_limit': 0,
            'download_subtitles': False,
            'subtitle_language': 'en',
            'auto_update': True,
            'presets': {
                '4K Video': {'quality': '2160', 'subtitles': False},
                'HD Video': {'quality': '1080', 'subtitles': False},
                'Audio Only': {'quality': 'audio', 'subtitles': False},
                'With Subtitles': {'quality': 'best', 'subtitles': True}
            }
        }
        self.config = self.load_config()
    
    def load_config(self):
        """Загрузить конфигурацию"""
        if self.config_path.exists():
            try:
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    # Добавляем недостающие ключи
                    for key, value in self.default_config.items():
                        if key not in config:
                            config[key] = value
                    return config
            except:
                return self.default_config.copy()
        return self.default_config.copy()
    
    def save_config(self):
        """Сохранить конфигурацию"""
        try:
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, ensure_ascii=False, indent=4)
        except Exception as e:
            print(f"Error saving config: {e}")
    
    def get(self, key, default=None):
        """Получить значение"""
        return self.config.get(key, default)
    
    def set(self, key, value):
        """Установить значение"""
        self.config[key] = value
        self.save_config()


class VideoDownloaderApp:
    """Главный класс приложения с ВСЕМИ функциями"""
    
    def __init__(self, root):
        self.root = root
        self.root.title("YouTube Video Downloader - Enhanced Edition")
        self.root.geometry("900x700")
        self.root.resizable(True, True)
        
        # Инициализация компонентов
        self.config = Config()
        self.history = DownloadHistory()
        self.download_queue = Queue()
        
        # Переменные
        self.download_path = tk.StringVar(value=self.config.get('last_download_path'))
        self.url = tk.StringVar()
        self.quality = tk.StringVar(value="best")
        self.is_downloading = False
        self.current_preset = tk.StringVar(value="Нет")
        
        # Опции
        self.download_subtitles = tk.BooleanVar(value=self.config.get('download_subtitles'))
        self.subtitle_language = tk.StringVar(value=self.config.get('subtitle_language'))
        self.speed_limit = tk.IntVar(value=self.config.get('speed_limit'))
        self.use_cookies = tk.BooleanVar(value=False)
        self.cookies_file = tk.StringVar()
        
        # Применяем тему
        apply_theme(self.root, self.config.get('theme', 'default'))
        
        # UI
        self.setup_ui()
        self.setup_dragdrop()
        
        # Автообновление ОТКЛЮЧЕНО для совместимости с PyInstaller
        # Используйте кнопку "Обновить yt-dlp" для обновления
    
    def setup_ui(self):
        """Настройка интерфейса"""
        # Создаём вкладки
        notebook = ttk.Notebook(self.root)
        notebook.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Вкладка: Загрузка
        download_tab = ttk.Frame(notebook)
        notebook.add(download_tab, text="📥 Загрузка")
        self.setup_download_tab(download_tab)
        
        # Вкладка: История
        history_tab = ttk.Frame(notebook)
        notebook.add(history_tab, text="📜 История")
        self.setup_history_tab(history_tab)
        
        # Вкладка: Настройки
        settings_tab = ttk.Frame(notebook)
        notebook.add(settings_tab, text="⚙️ Настройки")
        self.setup_settings_tab(settings_tab)
        
        # Вкладка: Очередь
        queue_tab = ttk.Frame(notebook)
        notebook.add(queue_tab, text="🔄 Очередь")
        self.setup_queue_tab(queue_tab)
    
    def setup_download_tab(self, parent):
        """Вкладка загрузки"""
        main_frame = ttk.Frame(parent, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Заголовок
        title_label = ttk.Label(main_frame, text="YouTube Video Downloader", 
                               font=("Arial", 16, "bold"))
        title_label.grid(row=0, column=0, columnspan=4, pady=10)
        
        # URL ввод с Drag & Drop
        url_label = ttk.Label(main_frame, text="URL видео (можно перетащить ссылку):", 
                             font=("Arial", 10))
        url_label.grid(row=1, column=0, sticky=tk.W, pady=5, columnspan=4)
        
        self.url_entry = ttk.Entry(main_frame, textvariable=self.url, width=80)
        self.url_entry.grid(row=2, column=0, columnspan=4, sticky=(tk.W, tk.E), pady=5)
        
        # Пресеты
        preset_frame = ttk.Frame(main_frame)
        preset_frame.grid(row=3, column=0, columnspan=4, sticky=(tk.W, tk.E), pady=5)
        
        ttk.Label(preset_frame, text="Пресет:").pack(side=tk.LEFT, padx=5)
        preset_combo = ttk.Combobox(preset_frame, textvariable=self.current_preset,
                                    values=["Нет"] + list(self.config.get('presets', {}).keys()),
                                    width=20)
        preset_combo.pack(side=tk.LEFT, padx=5)
        preset_combo.bind('<<ComboboxSelected>>', self.apply_preset)
        
        # Качество
        quality_label = ttk.Label(main_frame, text="Качество:", font=("Arial", 10))
        quality_label.grid(row=4, column=0, sticky=tk.W, pady=5, columnspan=4)
        
        quality_frame = ttk.Frame(main_frame)
        quality_frame.grid(row=5, column=0, columnspan=4, sticky=(tk.W, tk.E), pady=5)
        
        qualities = [
            ("Лучшее", "best"),
            ("4K (2160p)", "2160"),
            ("Full HD (1080p)", "1080"),
            ("HD (720p)", "720"),
            ("SD (480p)", "480"),
            ("Только аудио (mp3)", "audio")
        ]
        
        for idx, (text, value) in enumerate(qualities):
            rb = ttk.Radiobutton(quality_frame, text=text, variable=self.quality, value=value)
            rb.grid(row=0, column=idx, padx=5)
        
        # Опции
        options_frame = ttk.LabelFrame(main_frame, text="Дополнительные опции", padding="10")
        options_frame.grid(row=6, column=0, columnspan=4, sticky=(tk.W, tk.E), pady=10)
        
        ttk.Checkbutton(options_frame, text="Скачать субтитры", 
                       variable=self.download_subtitles).grid(row=0, column=0, sticky=tk.W)
        ttk.Label(options_frame, text="Язык:").grid(row=0, column=1, padx=(20,5))
        ttk.Entry(options_frame, textvariable=self.subtitle_language, width=5).grid(row=0, column=2)
        
        ttk.Checkbutton(options_frame, text="Использовать cookies", 
                       variable=self.use_cookies).grid(row=1, column=0, sticky=tk.W)
        ttk.Button(options_frame, text="Выбрать файл cookies", 
                  command=self.browse_cookies).grid(row=1, column=1, padx=5)
        
        ttk.Label(options_frame, text="Ограничение скорости (KB/s, 0=без ограничений):").grid(
            row=2, column=0, sticky=tk.W, columnspan=2)
        ttk.Entry(options_frame, textvariable=self.speed_limit, width=10).grid(row=2, column=2)
        
        # Путь сохранения
        path_label = ttk.Label(main_frame, text="Папка сохранения:", font=("Arial", 10))
        path_label.grid(row=7, column=0, sticky=tk.W, pady=5, columnspan=4)
        
        path_frame = ttk.Frame(main_frame)
        path_frame.grid(row=8, column=0, columnspan=4, sticky=(tk.W, tk.E), pady=5)
        
        path_entry = ttk.Entry(path_frame, textvariable=self.download_path, width=70)
        path_entry.grid(row=0, column=0, sticky=(tk.W, tk.E), padx=(0, 5))
        
        browse_button = ttk.Button(path_frame, text="Обзор...", command=self.browse_folder)
        browse_button.grid(row=0, column=1)
        
        path_frame.columnconfigure(0, weight=1)
        
        # Кнопки действий
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=9, column=0, columnspan=4, pady=15)
        
        self.download_button = ttk.Button(button_frame, text="Скачать видео", 
                                         command=self.start_download, width=20)
        self.download_button.grid(row=0, column=0, padx=5)
        
        ttk.Button(button_frame, text="Добавить в очередь", 
                  command=self.add_to_queue, width=20).grid(row=0, column=1, padx=5)
        
        self.info_button = ttk.Button(button_frame, text="Получить информацию", 
                                     command=self.get_video_info, width=20)
        self.info_button.grid(row=0, column=2, padx=5)
        
        ttk.Button(button_frame, text="Очистить", 
                  command=self.clear_log, width=15).grid(row=0, column=3, padx=5)
        
        self.update_button = ttk.Button(button_frame, text="Обновить yt-dlp", 
                                       command=self.manual_update_ytdlp, width=15)
        self.update_button.grid(row=0, column=4, padx=5)
        
        # Прогресс
        self.progress = ttk.Progressbar(main_frame, mode='indeterminate')
        self.progress.grid(row=10, column=0, columnspan=4, sticky=(tk.W, tk.E), pady=5)
        
        # Предпросмотр
        preview_frame = ttk.LabelFrame(main_frame, text="Предпросмотр", padding="5")
        preview_frame.grid(row=11, column=0, columnspan=4, sticky=(tk.W, tk.E), pady=5)
        
        self.preview_label = ttk.Label(preview_frame, text="Нет предпросмотра")
        self.preview_label.pack()
        
        # Лог
        log_label = ttk.Label(main_frame, text="Лог операций:", font=("Arial", 10))
        log_label.grid(row=12, column=0, sticky=tk.W, pady=5, columnspan=4)
        
        self.log_text = scrolledtext.ScrolledText(main_frame, height=10, width=100, 
                                                  wrap=tk.WORD, state='disabled')
        self.log_text.grid(row=13, column=0, columnspan=4, sticky=(tk.W, tk.E, tk.N, tk.S), pady=5)
        
        # Информация
        info_label = ttk.Label(main_frame, 
                              text="Поддерживаются: YouTube, Pinterest, TikTok, Instagram и 1000+ других сайтов",
                              font=("Arial", 8), foreground="gray")
        info_label.grid(row=14, column=0, columnspan=4, pady=5)
        
        # Конфигурация весов
        main_frame.columnconfigure(0, weight=1)
        main_frame.rowconfigure(13, weight=1)
    
    def setup_history_tab(self, parent):
        """Вкладка истории"""
        frame = ttk.Frame(parent, padding="10")
        frame.pack(fill=tk.BOTH, expand=True)
        
        # Заголовок
        ttk.Label(frame, text="История загрузок", font=("Arial", 14, "bold")).pack(pady=10)
        
        # Кнопки
        btn_frame = ttk.Frame(frame)
        btn_frame.pack(fill=tk.X, pady=5)
        
        ttk.Button(btn_frame, text="Обновить", command=self.refresh_history).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Очистить историю", command=self.clear_history_confirm).pack(side=tk.LEFT, padx=5)
        
        # Таблица истории
        tree_frame = ttk.Frame(frame)
        tree_frame.pack(fill=tk.BOTH, expand=True)
        
        scrollbar = ttk.Scrollbar(tree_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.history_tree = ttk.Treeview(tree_frame, columns=('date', 'title', 'quality', 'size'),
                                        show='headings', yscrollcommand=scrollbar.set)
        scrollbar.config(command=self.history_tree.yview)
        
        self.history_tree.heading('date', text='Дата')
        self.history_tree.heading('title', text='Название')
        self.history_tree.heading('quality', text='Качество')
        self.history_tree.heading('size', text='Размер')
        
        self.history_tree.column('date', width=150)
        self.history_tree.column('title', width=400)
        self.history_tree.column('quality', width=100)
        self.history_tree.column('size', width=100)
        
        self.history_tree.pack(fill=tk.BOTH, expand=True)
        
        # Загружаем историю
        self.refresh_history()
    
    def setup_settings_tab(self, parent):
        """Вкладка настроек"""
        frame = ttk.Frame(parent, padding="10")
        frame.pack(fill=tk.BOTH, expand=True)
        
        ttk.Label(frame, text="Настройки приложения", font=("Arial", 14, "bold")).pack(pady=10)
        
        # Информация об обновлении
        info_frame = ttk.Frame(frame)
        info_frame.pack(fill=tk.X, pady=10)
        ttk.Label(info_frame, text="ℹ️ Для обновления yt-dlp используйте кнопку 'Обновить yt-dlp' на главной вкладке",
                 wraplength=400, foreground="blue").pack(anchor=tk.W, padx=10)
        
        # Тема (placeholder для будущей реализации)
        ttk.Label(frame, text="Тема интерфейса:", font=("Arial", 10, "bold")).pack(anchor=tk.W, pady=(20,5))
        theme_var = tk.StringVar(value=self.config.get('theme', 'default'))
        theme_combo = ttk.Combobox(frame, textvariable=theme_var, values=['default', 'dark'], width=20)
        theme_combo.pack(anchor=tk.W, padx=20)
        
        ttk.Label(frame, text="(Перезапустите приложение для применения темы)", 
                 foreground="gray").pack(anchor=tk.W, padx=20)
        
        # Сохранить настройки
        ttk.Button(frame, text="Сохранить настройки", 
                  command=lambda: [self.config.set('theme', theme_var.get()), 
                                  messagebox.showinfo("Успех", "Настройки сохранены!")]).pack(pady=20)
    
    def setup_queue_tab(self, parent):
        """Вкладка очереди"""
        frame = ttk.Frame(parent, padding="10")
        frame.pack(fill=tk.BOTH, expand=True)
        
        ttk.Label(frame, text="Очередь загрузок", font=("Arial", 14, "bold")).pack(pady=10)
        
        # Кнопки управления
        btn_frame = ttk.Frame(frame)
        btn_frame.pack(fill=tk.X, pady=5)
        
        self.start_queue_button = ttk.Button(btn_frame, text="Начать загрузку очереди", 
                                            command=self.start_queue_processing)
        self.start_queue_button.pack(side=tk.LEFT, padx=5)
        
        ttk.Button(btn_frame, text="Очистить очередь", command=self.clear_queue).pack(side=tk.LEFT, padx=5)
        
        # Список очереди
        self.queue_listbox = tk.Listbox(frame, height=20)
        self.queue_listbox.pack(fill=tk.BOTH, expand=True, pady=10)
        
        ttk.Label(frame, text=f"Элементов в очереди: 0", font=("Arial", 10)).pack()
    
    def setup_dragdrop(self):
        """Настройка Drag & Drop"""
        try:
            self.url_entry.drop_target_register(DND_FILES)
            self.url_entry.dnd_bind('<<Drop>>', self.on_drop)
        except:
            # Если tkinterdnd2 не установлен, просто пропускаем
            pass
    
    def on_drop(self, event):
        """Обработка Drag & Drop"""
        data = event.data
        # Извлекаем URL из данных
        if data.startswith('http'):
            self.url.set(data)
            self.log("✓ URL добавлен через Drag & Drop")
    
    # ============= МЕТОДЫ ЗАГРУЗКИ =============
    
    def get_ydl_opts(self):
        """Получить опции для yt-dlp"""
        output_template = os.path.join(self.download_path.get(), '%(title)s.%(ext)s')
        
        opts = {
            'outtmpl': output_template,
            'progress_hooks': [self.progress_hook],
            'quiet': False,
            'no_warnings': False,
        }
        
        # Качество
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
            opts['format'] = f'bestvideo[height<={quality}]+bestaudio/best[height<={quality}]'
            opts['merge_output_format'] = 'mp4'
        
        # Субтитры
        if self.download_subtitles.get():
            opts['writesubtitles'] = True
            opts['subtitleslangs'] = [self.subtitle_language.get()]
        
        # Ограничение скорости
        if self.speed_limit.get() > 0:
            opts['ratelimit'] = self.speed_limit.get() * 1024
        
        # Cookies
        if self.use_cookies.get() and self.cookies_file.get():
            opts['cookiefile'] = self.cookies_file.get()
        
        return opts
    
    def download_video(self):
        """Загрузка видео"""
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
                info = ydl.extract_info(url, download=True)
                title = info.get('title', 'Unknown')
                
                # Добавляем в историю
                self.history.add_download(url, title, self.quality.get(), 
                                         info.get('_filename', ''), 
                                         info.get('filesize', 0))
            
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
        """Запуск загрузки в отдельном потоке"""
        if not self.is_downloading:
            thread = threading.Thread(target=self.download_video, daemon=True)
            thread.start()
    
    def progress_hook(self, d):
        """Обработка прогресса загрузки"""
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
    
    # ============= ВСПОМОГАТЕЛЬНЫЕ МЕТОДЫ =============
    
    def browse_folder(self):
        """Выбор папки для сохранения"""
        folder = filedialog.askdirectory(initialdir=self.download_path.get())
        if folder:
            self.download_path.set(folder)
            self.config.set('last_download_path', folder)
    
    def browse_cookies(self):
        """Выбор файла cookies"""
        file = filedialog.askopenfilename(filetypes=[("Text files", "*.txt"), ("All files", "*.*")])
        if file:
            self.cookies_file.set(file)
    
    def log(self, message):
        """Добавить сообщение в лог"""
        self.log_text.config(state='normal')
        self.log_text.insert(tk.END, f"{message}\n")
        self.log_text.see(tk.END)
        self.log_text.config(state='disabled')
        self.root.update()
    
    def clear_log(self):
        """Очистить лог"""
        self.log_text.config(state='normal')
        self.log_text.delete(1.0, tk.END)
        self.log_text.config(state='disabled')
    
    def apply_preset(self, event=None):
        """Применить пресет настроек"""
        preset_name = self.current_preset.get()
        if preset_name != "Нет":
            preset = self.config.get('presets', {}).get(preset_name, {})
            if preset:
                self.quality.set(preset.get('quality', 'best'))
                self.download_subtitles.set(preset.get('subtitles', False))
                self.log(f"✓ Применён пресет: {preset_name}")
    
    # ============= МЕТОДЫ ИНФОРМАЦИИ =============
    
    def get_info(self):
        """Получить информацию о видео"""
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
            
            ydl_opts = {'quiet': True, 'no_warnings': True}
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)
                
                self.log(f"Название: {info.get('title', 'N/A')}")
                self.log(f"Автор: {info.get('uploader', 'N/A')}")
                self.log(f"Длительность: {info.get('duration', 0)} секунд")
                self.log(f"Просмотров: {info.get('view_count', 'N/A')}")
                
                # Показываем превью
                thumbnail_url = info.get('thumbnail')
                if thumbnail_url:
                    try:
                        with urllib.request.urlopen(thumbnail_url) as u:
                            raw_data = u.read()
                        image = Image.open(io.BytesIO(raw_data))
                        image = image.resize((200, 150), Image.Resampling.LANCZOS)
                        photo = ImageTk.PhotoImage(image)
                        self.preview_label.config(image=photo, text="")
                        self.preview_label.image = photo
                    except:
                        self.preview_label.config(text="Не удалось загрузить превью")
            
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
        """Запуск получения информации в потоке"""
        thread = threading.Thread(target=self.get_info, daemon=True)
        thread.start()
    
    # ============= МЕТОДЫ ОЧЕРЕДИ =============
    
    def add_to_queue(self):
        """Добавить в очередь"""
        url = self.url.get().strip()
        if url:
            self.download_queue.put({
                'url': url,
                'quality': self.quality.get(),
                'subtitles': self.download_subtitles.get()
            })
            self.queue_listbox.insert(tk.END, url)
            self.log(f"✓ Добавлено в очередь: {url}")
            self.url.set("")
    
    def start_queue_processing(self):
        """Начать обработку очереди"""
        if self.download_queue.empty():
            messagebox.showinfo("Информация", "Очередь пуста!")
            return
        
        def process_queue():
            while not self.download_queue.empty():
                item = self.download_queue.get()
                self.url.set(item['url'])
                self.quality.set(item['quality'])
                self.download_subtitles.set(item['subtitles'])
                self.download_video()
            
            self.log("✓ Очередь обработана!")
            messagebox.showinfo("Успех", "Все видео из очереди загружены!")
        
        thread = threading.Thread(target=process_queue, daemon=True)
        thread.start()
    
    def clear_queue(self):
        """Очистить очередь"""
        while not self.download_queue.empty():
            self.download_queue.get()
        self.queue_listbox.delete(0, tk.END)
        self.log("Очередь очищена")
    
    # ============= МЕТОДЫ ИСТОРИИ =============
    
    def refresh_history(self):
        """Обновить историю"""
        for item in self.history_tree.get_children():
            self.history_tree.delete(item)
        
        history = self.history.get_history(100)
        for row in history:
            date = row[6] if len(row) > 6 else "N/A"
            title = row[2] if len(row) > 2 else "N/A"
            quality = row[3] if len(row) > 3 else "N/A"
            size = f"{row[5] / (1024*1024):.1f} MB" if len(row) > 5 and row[5] else "N/A"
            
            self.history_tree.insert('', 'end', values=(date, title, quality, size))
    
    def clear_history_confirm(self):
        """Подтверждение очистки истории"""
        if messagebox.askyesno("Подтверждение", "Вы уверены, что хотите очистить историю?"):
            self.history.clear_history()
            self.refresh_history()
            self.log("История очищена")
    
    # ============= АВТООБНОВЛЕНИЕ YT-DLP =============
    
    def update_ytdlp(self):
        """Обновление yt-dlp"""
        try:
            self.log("Проверка обновлений yt-dlp...")
            
            result = subprocess.run(
                [sys.executable, "-m", "pip", "install", "--upgrade", "yt-dlp"],
                capture_output=True,
                text=True,
                timeout=60
            )
            
            if result.returncode == 0:
                version_result = subprocess.run(
                    [sys.executable, "-m", "yt_dlp", "--version"],
                    capture_output=True,
                    text=True,
                    timeout=10
                )
                version = version_result.stdout.strip() if version_result.returncode == 0 else "unknown"
                
                self.log(f"✓ yt-dlp успешно обновлён до версии {version}")
                return True
            else:
                self.log(f"✗ Ошибка обновления: {result.stderr}")
                return False
                
        except subprocess.TimeoutExpired:
            self.log("✗ Превышено время ожидания при обновлении")
            return False
        except Exception as e:
            self.log(f"✗ Ошибка при обновлении: {str(e)}")
            return False
    
    def auto_update_ytdlp(self):
        """Автоматическое обновление yt-dlp при запуске"""
        def update_thread():
            try:
                self.log("=== Автопроверка обновлений yt-dlp ===")
                success = self.update_ytdlp()
                
                if success:
                    self.log("Приложение готово к работе!")
                else:
                    self.log("Приложение готово, но обновление не удалось")
                    
                self.log("-" * 80)
                
            except Exception as e:
                self.log(f"Ошибка автообновления: {str(e)}")
        
        thread = threading.Thread(target=update_thread, daemon=True)
        thread.start()
    
    def manual_update_ytdlp(self):
        """Ручное обновление yt-dlp по кнопке"""
        def update_thread():
            try:
                self.update_button.config(state='disabled')
                self.download_button.config(state='disabled')
                self.info_button.config(state='disabled')
                self.progress.start(10)
                
                self.log("=== Ручное обновление yt-dlp ===")
                success = self.update_ytdlp()
                
                if success:
                    messagebox.showinfo("Успех", "yt-dlp успешно обновлён!")
                else:
                    messagebox.showwarning("Предупреждение", "Не удалось обновить yt-dlp.")
                
                self.log("-" * 80)
                
            except Exception as e:
                self.log(f"✗ Ошибка: {str(e)}")
                messagebox.showerror("Ошибка", f"Произошла ошибка:\n{str(e)}")
            finally:
                self.update_button.config(state='normal')
                self.download_button.config(state='normal')
                self.info_button.config(state='normal')
                self.progress.stop()
        
        thread = threading.Thread(target=update_thread, daemon=True)
        thread.start()


def main():
    """Главная функция"""
    # КРИТИЧЕСКИ ВАЖНО для PyInstaller!
    multiprocessing.freeze_support()
    
    try:
        # Пробуем использовать TkinterDnD для Drag & Drop
        root = TkinterDnD.Tk()
    except:
        # Если не получается, используем обычный Tk
        root = tk.Tk()
    
    app = VideoDownloaderApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
