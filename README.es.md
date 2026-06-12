# WPS Office 12 en Español en Linux

Español | **[English](README.md)**

Guía completa para instalar **WPS Office v12** (12.1.2.25882) en Linux basado en Debian/Ubuntu con la interfaz en **español**, incluyendo correcciones de crashes verificadas por la comunidad.

> WPS Office v12 para Linux solo existe como build chino. El build internacional fue abandonado en v11. El botón de cambio de idioma fue **eliminado en v12**, así que la única forma de cambiar el idioma es el procedimiento manual documentado aquí.

## Resultado

| Componente | Idioma | Estado |
|---|---|---|
| Writer / Hojas de cálculo / Presentaciones (editores) | **Español (100%)** | Menús, ribbon, diálogos, barra de estado |
| Corrector ortográfico | Español (20+ variantes regionales) | es_ES, es_MX, es_CO, es_AR, ... |
| Launcher / página de inicio | Inglés | Limitación: `prometheus_kso_res.rcc` solo existe para en_US |
| Webview de configuración central | Chino | Limitación: HTML embebido del build chino |

Esto coincide con la traducción máxima alcanzable (~85-90% de la UI total) reportada por la comunidad. Los editores -- donde realmente trabajas -- están completamente en español.

## Requisitos

- Distro basada en Debian/Ubuntu (probado en Ubuntu 26.04 LTS, KDE Plasma, Wayland)
- ~1.5 GB de espacio libre en disco
- `wget`, `git`, `sudo`

## Instalación rápida

```bash
git clone https://github.com/andresgarcia0313/wps-office-12-spanish-linux.git
cd wps-office-12-spanish-linux
./install.sh
```

## Instalación manual (paso a paso)

### 1. Descargar e instalar WPS Office v12

Usa el [repack de Rongronggg9](https://github.com/Rongronggg9/wps-office-repack) (recomendado para Wayland/KDE -- incluye parches Fcitx5/XWayland y tiene URLs estables en GitHub, a diferencia del CDN oficial chino cuyos enlaces expiran):

```bash
wget -O /tmp/wps-office-v12.deb \
  "https://github.com/Rongronggg9/wps-office-repack/releases/download/v12.1.2.25882/wps-office_12.1.2.25882.AK.preread.sw%2Bfcitx5xwayland_amd64.deb"
sudo dpkg -i /tmp/wps-office-v12.deb
sudo apt-get install -f -y
```

> Si tienes WPS v11 instalado, este paquete lo reemplaza (mismo nombre de paquete).

### 2. Instalar el MUI español (archivos de traducción)

El proyecto [mmvill/WPS_Office_12x_Es](https://github.com/mmvill/WPS_Office_12x_Es) provee los archivos de traducción Qt (`.qm`) específicamente para v12:

```bash
git clone --depth 1 https://github.com/mmvill/WPS_Office_12x_Es.git /tmp/WPS_Office_12x_Es
sudo cp -r /tmp/WPS_Office_12x_Es/mui/* /opt/kingsoft/wps-office/office6/mui/
sudo cp -r /tmp/WPS_Office_12x_Es/spellcheck/* /opt/kingsoft/wps-office/office6/dicts/spellcheck/
```

### 3. Instalar el registro de idiomas (paso crítico no documentado)

Los binarios de WPS (`libmisc_linux.so`, `libkrt.so`) buscan `mui/lang_list/lang_list.json` para registrar los idiomas disponibles. **Sin este archivo la UI cae a inglés** aunque el MUI y la configuración estén correctos. El archivo viene de [wachin/wps-office-all-mui-win-language](https://github.com/wachin/wps-office-all-mui-win-language):

```bash
wget -O /tmp/lang_list_community.json \
  "https://github.com/wachin/wps-office-all-mui-win-language/releases/download/v11.1.0.11704/lang_list_community.json"
sudo mkdir -p /opt/kingsoft/wps-office/office6/mui/lang_list/
sudo cp /tmp/lang_list_community.json /opt/kingsoft/wps-office/office6/mui/lang_list/lang_list_community.json
sudo cp /tmp/lang_list_community.json /opt/kingsoft/wps-office/office6/mui/lang_list/lang_list.json
```

### 4. Generar el archivo de configuración

Lanza WPS una vez para que cree `~/.config/Kingsoft/Office.conf`, luego ciérralo:

```bash
timeout 10 wps; pkill -f wpsoffice
```

### 5. Configurar el idioma en Office.conf

Edita `~/.config/Kingsoft/Office.conf`:

```ini
[General]
languages=es_ES

[6.0]
common\DefaultLanguage=3082
common\Local\UILanguage=3082
common\do_not_detect_file_association_while_startup=true
```

Códigos LCID: `3082` = Español (España), `2058` = Español (México), `1033` = Inglés (US).

La línea `do_not_detect_file_association_while_startup` evita que WPS pelee con tu entorno de escritorio por las asociaciones de archivos.

### 6. Correcciones de crashes (muy recomendado)

**Desactivar `wpscloudsvr`** -- el daemon de sincronización cloud crashea constantemente con SIGSEGV en `libqingbangong.so` (ampliamente reportado). No se necesita para uso local:

```bash
sudo chmod -x /opt/kingsoft/wps-office/office6/wpscloudsvr
rm -rf ~/.local/share/Kingsoft/daemon/
```

**Crear el symlink `libtiff.so.5`** -- las distros modernas solo traen `libtiff.so.6`, y WPS necesita el soname viejo para exportar PDF:

```bash
sudo ln -s /usr/lib/x86_64-linux-gnu/libtiff.so.6 /usr/lib/x86_64-linux-gnu/libtiff.so.5
sudo ldconfig
```

### 7. Listo

Abre WPS Writer y verifica que los menús estén en español (Inicio, Insertar, Diseño de página, Referencias, Revisar, Vista). Activa el corrector en **Revisar > Revisión ortográfica** y elige tu diccionario regional.

## Limitaciones conocidas

- **El launcher / página de inicio queda en inglés.** Al MUI es_ES le falta `prometheus_kso_res.rcc` (recursos de la UI Prometheus); solo en_US lo trae. Es un recurso Qt compilado -- no traducible por la comunidad.
- **El webview de configuración central queda en chino.** Es HTML embebido dentro del build chino renderizado por CEF; los `.pak` de locale no lo afectan.
- **No hay botón de idioma.** Eliminado por Kingsoft en v12. Solo configuración por archivo.
- **Las actualizaciones borran el MUI.** Tras cualquier actualización de WPS, repite los pasos 2, 3 y 6.

## Errores comunes a evitar

| Error | Consecuencia |
|---|---|
| Usar los archivos MUI del [repo de wachin](https://github.com/wachin/wps-office-all-mui-win-language) para v12 | Apuntan a v11; el mantenedor advierte explícitamente contra v12. Usa el repo de mmvill para el MUI, el de wachin solo para `lang_list_community.json` |
| Saltarse `lang_list.json` | La UI cae a inglés aunque el MUI + Office.conf estén correctos |
| Descargar el deb del CDN oficial chino con una URL guardada | Las URLs del CDN llevan tokens que expiran -> 403 Forbidden. Usa los releases de GitHub del repack o consigue un enlace fresco en [linux.wps.cn](https://linux.wps.cn/) |
| Dejar `wpscloudsvr` activo | Crashes SIGSEGV recurrentes; pueden propagarse a los editores |
| Editar Office.conf con WPS abierto | WPS reescribe el archivo al salir, descartando tus cambios |

## Créditos

- [mmvill/WPS_Office_12x_Es](https://github.com/mmvill/WPS_Office_12x_Es) -- MUI español para v12 (GPL-3.0)
- [wachin/wps-office-all-mui-win-language](https://github.com/wachin/wps-office-all-mui-win-language) -- `lang_list_community.json` e investigación MUI
- [Rongronggg9/wps-office-repack](https://github.com/Rongronggg9/wps-office-repack) -- repack v12 con parches Wayland/Fcitx5
- [ArchWiki - WPS Office](https://wiki.archlinux.org/title/WPS_Office) -- documentación de correcciones de crashes

## Licencia

GPL-3.0 -- consistente con el proyecto MUI upstream.
