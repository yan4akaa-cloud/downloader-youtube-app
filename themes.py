# -*- coding: utf-8 -*-
"""
Модуль тем оформления для Video Downloader
"""

import tkinter as tk
from tkinter import ttk


def apply_theme(root, theme='default'):
    """
    Применить тему оформления
    
    Args:
        root: корневое окно Tk
        theme: название темы ('default' или 'dark')
    """
    if theme == 'dark':
        apply_dark_theme(root)
    else:
        apply_default_theme(root)


def apply_default_theme(root):
    """Применить светлую тему (по умолчанию)"""
    style = ttk.Style(root)
    
    # Используем стандартную тему
    try:
        style.theme_use('vista')  # Windows
    except:
        try:
            style.theme_use('clam')  # Linux/Mac
        except:
            pass


def apply_dark_theme(root):
    """Применить тёмную тему"""
    style = ttk.Style(root)
    
    # Базовая тема
    style.theme_use('clam')
    
    # Цвета тёмной темы
    bg_color = '#2b2b2b'
    fg_color = '#ffffff'
    select_bg = '#404040'
    select_fg = '#ffffff'
    
    # Настройка стилей
    style.configure('TFrame', background=bg_color)
    style.configure('TLabel', background=bg_color, foreground=fg_color)
    style.configure('TButton', background='#404040', foreground=fg_color)
    style.map('TButton',
             background=[('active', '#505050')])
    
    style.configure('TEntry', fieldbackground='#404040', foreground=fg_color)
    style.configure('TCheckbutton', background=bg_color, foreground=fg_color)
    style.configure('TRadiobutton', background=bg_color, foreground=fg_color)
    style.configure('TCombobox', fieldbackground='#404040', foreground=fg_color)
    style.configure('TNotebook', background=bg_color)
    style.configure('TNotebook.Tab', background='#404040', foreground=fg_color)
    style.map('TNotebook.Tab',
             background=[('selected', '#505050')])
    
    style.configure('TLabelframe', background=bg_color, foreground=fg_color)
    style.configure('TLabelframe.Label', background=bg_color, foreground=fg_color)
    
    # Настройка корневого окна
    root.configure(bg=bg_color)

