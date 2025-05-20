# 🖥️ Sistema Predictivo de Mantenimiento de Computadoras

Este sistema permite predecir el próximo mantenimiento ideal para equipos de cómputo a partir de datos técnicos como el uso acumulado, la carga promedio y las condiciones ambientales. Genera reportes automáticos en PDF y recordatorios en formato `.ics`, además de ofrecer recomendaciones personalizadas.
---

## 📌 Características principales

- Interfaz moderna con Flet (Python)
- Predicción basada en modelo de machine learning (`scikit-learn`)
- Validación estricta de entradas
- Reporte PDF con encabezado, logo y recomendaciones inteligentes
- Envío de correo electrónico con adjuntos (PDF + evento calendario)
- Exportación del sistema como ejecutable `.exe`
- Manual de usuario descargable
- Soporte para accesibilidad visual y mensajes personalizados

---

## 🚀 Requisitos

- Python 3.10 o superior (si usas el código fuente)
- Librerías necesarias:
  - `flet`
  - `joblib`
  - `scikit-learn`
  - `reportlab`
  - `python-dotenv`
  - `ics`

Instálalas con:

```bash
pip install -r requirements.txt
```

---

## 🛠️ Uso

1. Clona el repositorio:

```bash
git clone https://github.com/manucueto/Sistema-predictivo-basado-en-ciencia-de-datos-para-el-mantenimiento-de-computadoras.git
cd Sistema-predictivo-basado-en-ciencia-de-datos-para-el-mantenimiento-de-computadoras
```

2. Configura tus variables de entorno:

Crea un archivo `.env` (que no se sube a GitHub) con tu correo y clave de aplicación de Gmail:

```dotenv
CORREO_REMITENTE=tu_correo@gmail.com
CLAVE_CORREO=clave_generada
```

> ✅ Puedes guiarte por `.env.example` incluido en el proyecto.

3. Ejecuta la aplicación:

```bash
python main.py
```

---

## 🔐 Seguridad

- No se almacena tu contraseña en el código.
- `.env` está excluido con `.gitignore`.

---

## 📦 Crear ejecutable

Si deseas generar un `.exe`:

```bash
pyinstaller --noconfirm --onefile --windowed main.py ^
--add-data "modelo_mantenimiento.pkl;." ^
--add-data "fondo.png;." ^
--add-data "manual_usuario.pdf;." ^
--add-data "ujap_imagen_n1-removebg-preview.png;." ^
--add-data "Poppins-Regular.ttf;." ^
--hidden-import sklearn
```

El ejecutable estará en `dist/main.exe`.

---

## 📄 Manual de usuario

Puedes descargar el manual directamente desde la app o verlo aquí:  
👉 [`manual_usuario.pdf`](manual_usuario.pdf)

---

## 🧑‍💻 Autor

Desarrollado por **Manuel Cueto**  
📧 manuelcueto2004@gmail.com

---

## 🏛️ Universidad

Proyecto desarrollado como parte del trabajo de grado en la  
**Universidad José Antonio Páez**

---

## 📃 Licencia

Este proyecto se distribuye bajo licencia MIT. Puedes usarlo, modificarlo y distribuirlo libremente.
