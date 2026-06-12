#!/usr/bin/env python3
"""Safely translate Chinese UI strings in WPS settings webview JS/HTML.

Strategy:
 - Only replace QUOTED string literals ("中文" or '中文'), so quotes act as
   boundaries and substrings of longer phrases are never corrupted.
 - Replace consistently everywhere (visible text AND logic comparisons stay
   in sync, since both sides use the same quoted literal).
 - Apply longest phrases first.
 - Validate each JS file with `node --check` before writing; revert on failure.
"""
import json, subprocess, sys, re, shutil, os

TRANSLATIONS = {
    "界面": "Interfaz",
    "外观设置": "Configuración de apariencia",
    "工作环境": "Entorno de trabajo",
    "文档云同步": "Sincronización de documentos en la nube",
    "可以从自己的手机或其他电脑访问这台电脑打开过的文档":
        "Acceda desde su teléfono u otro equipo a los documentos abiertos aquí",
    "使用鼠标双击关闭标签": "Cerrar pestañas con doble clic",
    "网页浏览设置": "Configuración de navegación web",
    "打开备份中心": "Abrir centro de copias de seguridad",
    "其他": "Otros",
    "切换窗口管理模式": "Cambiar modo de gestión de ventanas",
    "切换为经典界面": "Cambiar a interfaz clásica",
    "恢复初始默认设置": "Restaurar configuración predeterminada",
    "设置中心": "Centro de configuración",
    "经典皮肤": "Temas clásicos",
    "桌面图标": "Icono del escritorio",
    "首页布局": "Disposición de la página principal",
    "首页主导航栏名称隐藏": "Ocultar nombres de la barra de navegación",
    "自定义外观": "Apariencia personalizada",
    "背景图像和颜色": "Imagen de fondo y color",
    "背景透明度": "Transparencia del fondo",
    "窗口半透明效果": "Efecto de ventana translúcida",
    "界面字体": "Fuente de la interfaz",
    "恢复默认值": "Restaurar valores predeterminados",
    "下载目录": "Carpeta de descargas",
    "下载前询问每个文件的保存位置": "Preguntar ubicación antes de cada descarga",
    "下载完成记录": "Registro de descargas completadas",
    "上报应用诊断信息": "Enviar información de diagnóstico",
    "云文档默认启用自动保存": "Activar autoguardado en documentos de la nube",
    "会员特权提示": "Aviso de privilegios de membresía",
    "缓存的图像和文件": "Imágenes y archivos en caché",
    "浏览数据": "Datos de navegación",
    "安全性": "Seguridad",
    "PDF预览": "Vista previa de PDF",
    "Chrome下载路径": "Ruta de descargas de Chrome",
    "Firefox下载路径": "Ruta de descargas de Firefox",
    "Thunderbird邮件的下载文件夹": "Carpeta de descargas de Thunderbird",
    "Cookie及其他网站数据": "Cookies y datos de sitios web",
}


def translate_file(path):
    if not os.path.exists(path):
        return None
    orig = open(path, encoding='utf-8').read()
    text = orig
    # Longest first to avoid any phrase/substring ambiguity
    for zh in sorted(TRANSLATIONS, key=len, reverse=True):
        es = TRANSLATIONS[zh]
        # Only quoted literals: "..." and '...'
        text = text.replace(f'"{zh}"', f'"{es}"')
        text = text.replace(f"'{zh}'", f"'{es}'")
    if text == orig:
        return 0
    # Validate if JS
    if path.endswith('.js'):
        tmp = f"/tmp/wps_check_{os.getpid()}.js"
        open(tmp, 'w', encoding='utf-8').write(text)
        r = subprocess.run(['node', '--check', tmp], capture_output=True, text=True)
        os.remove(tmp)
        if r.returncode != 0:
            print(f"  VALIDATION FAILED for {path}: {r.stderr.strip()[:120]}")
            return -1
    open(path, 'w', encoding='utf-8').write(text)
    return text.count('  ') if False else 1


if __name__ == "__main__":
    for p in sys.argv[1:]:
        res = translate_file(p)
        print(f"{p}: {'OK' if res == 1 else ('no-change' if res == 0 else 'FAILED/skip')}")
