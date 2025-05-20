import flet as ft
import joblib
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from datetime import datetime
from ics import Calendar, Event
from datetime import datetime, timedelta
from email.mime.application import MIMEApplication
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import smtplib
from email.header import Header
import re
from email.utils import encode_rfc2231
from reportlab.lib import colors
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
import sys
import os
from dotenv import load_dotenv


load_dotenv()

# Cargar variables de entorno desde el archivo .env
correo = os.getenv("CORREO_REMITENTE")
contrasena = os.getenv("CLAVE_CORREO")

def obtener_ruta_recurso(nombre_archivo):
    if hasattr(sys, '_MEIPASS'):
        return os.path.join(sys._MEIPASS, nombre_archivo)
    return os.path.join(os.path.abspath("."), nombre_archivo)


# Cargar el modelo entrenado
modelo = joblib.load(obtener_ruta_recurso('modelo_mantenimiento.pkl'))

def main(page: ft.Page):
    # Configuración general de la ventana
    page.title = "Sistema Predictivo de Mantenimiento de Computadoras"
    page.fonts = {
        "Poppins": "https://raw.githubusercontent.com/google/fonts/main/ofl/poppins/Poppins-Regular.ttf",
        "Poppins-Bold": "https://raw.githubusercontent.com/google/fonts/main/ofl/poppins/Poppins-Bold.ttf",
    }
    page.bgcolor = ft.colors.TRANSPARENT
    page.theme = ft.Theme(font_family="Poppins")
    page.window.min_height = 800
    page.window.min_width = 650
    page.window.height = 800   
    page.window.width = 1500  
    page.scroll = ft.ScrollMode.ALWAYS


    # Decoración de fondo
    page.decoration = ft.BoxDecoration(
        image=ft.DecorationImage(
            src=obtener_ruta_recurso("fondo1.PNG"),
            fit=ft.ImageFit.COVER,
        )
    )
    # === Componente FilePicker para descarga ===
    file_picker = ft.FilePicker()
    page.overlay.append(file_picker)

    # Ruta del manual
    manual_path = obtener_ruta_recurso("manual_usuario.pdf")

    boton_descargar_manual = ft.TextButton(
        text="📄 Descargar Manual de Usuario",
        icon=ft.icons.DOWNLOAD,
        style=ft.ButtonStyle(color="#12FFD1"),
        on_click=lambda _: page.launch_url("file://" + manual_path)
    )



    # Función para validar que algunos los campos sean numeros enteros

    # Validación para numero entero
    def validate_integer(e):
        try:
            value = int(e.control.value)
            if value < 0:
                e.control.error_text = "Debe ser un número positivo."
            else:
                e.control.error_text = None
        except ValueError:
            e.control.error_text = "Por favor, ingresa un número válido."
        e.control.update()

    # Validación para carga promedio
    def validate_carga_promedio(e):
        try:
            value = int(e.control.value)
            if value < 0:
                e.control.error_text = "Debe ser un número positivo."
            else:
                e.control.error_text = None
        except ValueError:
            e.control.error_text = "Por favor, ingresa un número válido."
        e.control.update()
        try:
            value = int(e.control.value)
            if value < 1 or value > 100:
                e.control.error_text = "Carga promedio debe estar entre 1 y 100."
            else:
                e.control.error_text = None
        except ValueError:
            e.control.error_text = "Por favor, ingresa un número válido."
        e.control.update()

# Validación para campos requeridos
    def validar_campos_requeridos():
        campos_invalidos = False

        if meses_input.value.strip() == "":
            meses_input.error_text = "Campo obligatorio."
            meses_input.update()
            campos_invalidos = True
        else:
            meses_input.error_text = None
            meses_input.update()

        if horas_input.value is None:
            horas_input.error_text = "Selecciona una opción."
            horas_input.update()
            campos_invalidos = True
        else:
            horas_input.error_text = None
            horas_input.update()

        if ciclos_input.value is None:
            ciclos_input.error_text = "Selecciona una opción."
            ciclos_input.update()
            campos_invalidos = True
        else:
            ciclos_input.error_text = None
            ciclos_input.update()

        if carga_input.value.strip() == "":
            carga_input.error_text = "Campo obligatorio."
            carga_input.update()
            campos_invalidos = True
        else:
            carga_input.error_text = None
            carga_input.update()

        if ambiente_dropdown.value is None:
            ambiente_dropdown.error_text = "Selecciona una opción."
            ambiente_dropdown.update()
            campos_invalidos = True
        else:
            ambiente_dropdown.error_text = None
            ambiente_dropdown.update()

        if recursos_dropdown.value is None:
            recursos_dropdown.error_text = "Selecciona una opción."
            recursos_dropdown.update()
            campos_invalidos = True
        else:
            recursos_dropdown.error_text = None
            recursos_dropdown.update()

        return not campos_invalidos


    def validar_horas_y_ciclos(horas_control, ciclos_control):
        try:
            # Usamos limpiar_valor para procesar strings como "3000+"
            horas = limpiar_valor(horas_control.value)
            ciclos = limpiar_valor(ciclos_control.value)

            if ciclos <= 0:
                ciclos_control.error_text = "Los ciclos deben ser mayores que 0."
                ciclos_control.update()
                return False

            horas_por_ciclo = horas / ciclos
            if horas_por_ciclo < 0.5 or horas_por_ciclo > 72:
                horas_control.error_text = f"Promedio poco realista: {horas_por_ciclo:.1f} hrs/ciclo."
                ciclos_control.error_text = f"Verifica tus ciclos: {horas_por_ciclo:.1f} hrs/ciclo."
                horas_control.update()
                ciclos_control.update()
                return False
            else:
                horas_control.error_text = None
                ciclos_control.error_text = None
                horas_control.update()
                ciclos_control.update()
                return True
        except (ValueError, TypeError):
            horas_control.error_text = ciclos_control.error_text = "Selecciona valores válidos."
            horas_control.update()
            ciclos_control.update()
            return False

        
#
    def validar_valores_numericos_finales():
        campos_invalidos = False

        def validar_numero(control, nombre):
            nonlocal campos_invalidos
            try:
                valor = int(control.value)
                control.error_text = None
            except (ValueError, TypeError):
                control.error_text = f"{nombre} debe ser un número válido."
                campos_invalidos = True
            control.update()

        # Campos numéricos
        validar_numero(meses_input, "Meses")
        validar_numero(carga_input, "Carga promedio")

        # Solo si horas/ciclos son TextFields (usa limpiar_valor si son dropdowns)
        try:
            limpiar_valor(horas_input.value)
            horas_input.error_text = None
        except:
            horas_input.error_text = "Selecciona un valor válido."
            campos_invalidos = True
        horas_input.update()

        try:
            limpiar_valor(ciclos_input.value)
            ciclos_input.error_text = None
        except:
            ciclos_input.error_text = "Selecciona un valor válido."
            campos_invalidos = True
        ciclos_input.update()

        return not campos_invalidos

# Validar correo electrónico
    def validar_correo(correo):
        patron = r'^[\w\.-]+@[\w\.-]+\.\w{2,}$'
        return re.match(patron, correo) is not None
    
    def validar_correo_input(e):
        correo = e.control.value
        if validar_correo(correo):
            e.control.error_text = None
        else:
            e.control.error_text = "Correo electrónico no válido."
        e.control.update()

    # Texto para conseguir info
    texto_ayuda = ft.Text("¿Dónde conseguir la información?",tooltip=ft.Tooltip(message="¿Dónde encontrar la información solicitada?\nPara completar este formulario, necesitarás algunos datos técnicos de tu equipo, como las horas de uso totales, los ciclos de encendido y apagado, y la carga de trabajo promedio.\nPuedes obtener esta información utilizando las herramientas estándar que ofrece tu sistema operativo:\nWindows: Utiliza el Visor de eventos y el Monitor de rendimiento para consultar registros de actividad y el uso promedio del procesador\nLinux: Puedes revisar los registros del sistema y los comandos de monitoreo habituales para obtener los datos de actividad y carga.\nMac: Los registros del sistema y las utilidades de monitoreo te permiten ver tanto el historial de encendidos como el uso promedio del equipo\nSi tienes dudas sobre cómo acceder a estas herramientas, consulta la documentación de tu sistema operativo o solicita asistencia técnica.",
                                                   padding=12,
                                                   bgcolor=ft.colors.WHITE,
                                                   text_style=ft.TextStyle(color=ft.colors.BLACK, size=13),
                                                   wait_duration=400,border_radius=8),
    size=16,
    color='#12FFD1',
    weight="bold",
    text_align=ft.TextAlign.CENTER,
    )

    

    # Opciones dropdowns
    def get_options_recursos():
        return [
            ft.DropdownOption(key="De bajo consumo de recursos", content=ft.Text("De bajo consumo de recursos")),
            ft.DropdownOption(key="De mediano consumo de recursos", content=ft.Text("De mediano consumo de recursos")),
            ft.DropdownOption(key="De alto consumo de recursos", content=ft.Text("De alto consumo de recursos")),
        ]

    def get_options_ambiente():
        return [
            ft.DropdownOption(key="Crítico", content=ft.Text("Críticas")),
            ft.DropdownOption(key="Aceptable", content=ft.Text("Aceptables")),
            ft.DropdownOption(key="Óptimo", content=ft.Text("Óptimas")),
        ]
    
    # Horas de uso total (acumuladas)
    horas_options = [
        ft.dropdown.Option("100"),
        ft.dropdown.Option("250"),
        ft.dropdown.Option("500"),
        ft.dropdown.Option("1000"),
        ft.dropdown.Option("1500"),
        ft.dropdown.Option("2000"),
        ft.dropdown.Option("3000+"),
    ]

    # Ciclos de encendido/apagado
    ciclos_options = [
        ft.dropdown.Option("50"),
        ft.dropdown.Option("100"),
        ft.dropdown.Option("250"),
        ft.dropdown.Option("500"),
        ft.dropdown.Option("750"),
        ft.dropdown.Option("1000"),
        ft.dropdown.Option("1500+"),
    ]
    
    # Función para generar el evento .ics
    def generar_evento_ics(nombre_equipo, prediccion_meses):
        c = Calendar()
        e = Event()
        e.name = f"Mantenimiento: {nombre_equipo}"
        
        fecha_evento = datetime.now() + timedelta(days=prediccion_meses * 30)
        e.begin = fecha_evento.strftime('%Y-%m-%d 09:00:00')
        e.end = fecha_evento.strftime('%Y-%m-%d 10:00:00')
        e.description = f"Recordatorio de mantenimiento preventivo para el equipo '{nombre_equipo}'."

        c.events.add(e)

        nombre_archivo = f"evento_mantenimiento_{nombre_equipo.replace(' ', '_').replace('ñ', 'n')}.ics"
        with open(nombre_archivo, 'w') as f:
            f.writelines(c)
        
        return nombre_archivo
    
    def generar_recomendaciones(prediccion, condiciones_ambiente, carga_promedio):
        recomendaciones = []

        if prediccion <= 1:
            recomendaciones.append(" Riesgo alto de falla. Se recomienda mantenimiento inmediato.")
        elif prediccion <= 2:
            recomendaciones.append(" Mantenimiento próximo. Agenda una revisión en las próximas semanas.")
        else:
            recomendaciones.append(" No se detectan urgencias inmediatas. Continúa con monitoreo mensual.")

        if condiciones_ambiente.lower() == "critico":
            recomendaciones.append(" Las condiciones ambientales son críticas. Considera mejorar ventilación o reducir exposición a polvo/humedad.")

        if int(carga_promedio) >= 80:
            recomendaciones.append(" El equipo opera bajo alta carga. Revisa sistema de refrigeración y realiza mantenimiento preventivo.")

        recomendaciones.extend([
            " Limpia ventiladores y disipadores si ha pasado más de 6 meses.",
            " Verifica temperatura interna con herramientas de monitoreo.",
            " Realiza copias de seguridad antes de cualquier intervención técnica."
        ])

        return recomendaciones
    
    def generar_reporte_pdf(nombre_equipo, datos_equipo, prediccion):
        filename = f"reporte_mantenimiento_{nombre_equipo}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
        c = canvas.Canvas(filename, pagesize=letter)
        width, height = letter

        # === Registrar fuente Poppins ===
        pdfmetrics.registerFont(TTFont("Poppins", obtener_ruta_recurso("Poppins-Regular.ttf")))

        # === HEADER ===
        c.setFillColorRGB(8/255, 73/255, 79/255)  # Color: #08494F
        c.rect(0, height - 80, width, 80, fill=1, stroke=0)

        # Logo en el encabezado
        c.drawImage(
            obtener_ruta_recurso("ujap_imagen_n1-removebg-preview.png"),  # Nombre exacto del archivo
            x=width - 120,                          # Distancia desde la izquierda
            y=height - 70,                          # Altura desde abajo
            width=60,                               # Ancho en puntos
            height=60,                              # Alto en puntos
            preserveAspectRatio=True,
            mask='auto'
        )

        # Título
        c.setFont("Poppins", 16)
        c.setFillColor(colors.white)
        c.drawString(40, height - 50, "Sistema Predictivo de Mantenimiento")

        # === FOOTER ===
        c.setStrokeColorRGB(11/255, 150/255, 146/255)  # Línea superior en #0B9692
        c.line(40, 40, width - 40, 40)
        c.setFont("Helvetica", 9)
        c.setFillColor(colors.black)
        c.drawString(40, 25, "Generado automáticamente por el sistema")
        c.drawRightString(width - 40, 25, f"{datetime.now().strftime('%d/%m/%Y')}")

        # === CUERPO ===
        y = height - 110

        # Sección: Resumen general
        c.setFont("Poppins", 14)
        c.setFillColor(colors.black)
        c.drawString(50, y, " Resumen del equipo")
        y -= 25

        c.setFont("Helvetica", 11)
        c.drawString(50, y, f"Equipo: {nombre_equipo}")
        y -= 18
        c.drawString(50, y, f"Fecha de generación: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
        y -= 30

        # Sección: Datos ingresados
        c.setFont("Poppins", 14)
        c.drawString(50, y, " Datos Ingresados")
        y -= 25

        c.setFont("Helvetica", 11)
        for key, value in datos_equipo.items():
            c.drawString(70, y, f"• {key}: {value}")
            y -= 18
            if y < 80:
                c.showPage()
                y = height - 100

        y -= 10
        # Sección: Resultado
        c.setFont("Poppins", 14)
        c.drawString(50, y, " Resultado de la predicción")
        y -= 25

        c.setFont("Helvetica-Bold", 12)
        c.drawString(50, y, f"Próximo mantenimiento estimado: {prediccion} meses")
        

        # === Sección: Recomendaciones y alertas ===
        y -= 30
        c.setFont("Poppins", 14)
        c.drawString(50, y, " Recomendaciones y alertas")
        y -= 20

        recomendaciones = generar_recomendaciones(
            prediccion=prediccion,
            condiciones_ambiente=datos_equipo["Condiciones ambientales"],
            carga_promedio=datos_equipo["Carga promedio (%)"]
        )

        c.setFont("Helvetica", 11)
        for rec in recomendaciones:
            if y < 80:
                c.showPage()
                y = height - 100
                c.setFont("Helvetica", 11)
            c.drawString(70, y, f"- {rec}")
            y -= 18

        c.save()
        return filename

    # Función para enviar correo con el PDF y archivo .ics adjunto
    # filepath: c:\Users\manue\Desktop\Universidad\10mo Semestre\Pasantía o Trabajo de Grado 2\Sistema\main.py
    def enviar_correo_con_pdf(destinatario, equipo, archivo_pdf, archivo_ics):
        # Crear mensaje de correo
        msg = MIMEMultipart()
        msg['From'] = "manuelcueto2004@gmail.com"
        msg['To'] = destinatario

        # Asunto codificado correctamente (soporta ñ, tildes, etc.)
        msg['Subject'] = Header(f"Reporte y recordatorio de mantenimiento - {equipo}", 'utf-8')

        # Cuerpo del mensaje codificado en UTF-8
        cuerpo = f"""Hola,

        Adjunto encontrarás el reporte PDF generado automáticamente para el equipo '{equipo}'.

        También se adjunta un archivo de evento de calendario (.ics) que puedes abrir para agendar la fecha estimada de mantenimiento en tu Google Calendar u otra app.

        -- Sistema Predictivo de Mantenimiento
        """
        msg.attach(MIMEText(cuerpo, 'plain', 'utf-8'))

        # Adjuntar PDF
        with open(archivo_pdf, "rb") as file:
            part = MIMEApplication(file.read(), Name=archivo_pdf)
            part.add_header('Content-Disposition', 'attachment', filename=encode_rfc2231(archivo_pdf, 'utf-8'))
            msg.attach(part)

        # Adjuntar archivo .ics
        with open(archivo_ics, "rb") as file:
            part_ics = MIMEApplication(file.read(), Name=archivo_ics)
            part_ics.add_header('Content-Disposition', 'attachment', filename=encode_rfc2231(archivo_ics, 'utf-8'))
            msg.attach(part_ics)

        # Enviar correo
        try:
            with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
                smtp.login(correo, contrasena)
                smtp.send_message(msg)
                mensaje_status_correo.value = "Correo enviado exitosamente."
                mensaje_status_correo.update()
                print(" Correo con PDF y evento ICS enviado exitosamente.")
        except Exception as e:
            print(f" Error al enviar el correo: {e}")



    # Campos de entrada individuales
    nombre_equipo_input = ft.TextField(hint_text="Nombre del equipo", width=300, border_color=ft.colors.WHITE,  )
    correo_input = ft.TextField(hint_text="Correo electrónico", keyboard_type=ft.KeyboardType.EMAIL, width=300, border_color=ft.colors.WHITE, on_change=validar_correo_input)
    meses_input = ft.TextField(hint_text="Escribe un número...", keyboard_type=ft.KeyboardType.NUMBER, border_color=ft.colors.WHITE, on_change=validate_integer, width=300)
    horas_input = ft.Dropdown(
    label="Horas de uso total",
    options=horas_options,
    width=300,
    border_color=ft.colors.WHITE
    )
    ciclos_input = ft.Dropdown(
        label="Ciclos de encendido/apagado",
        options=ciclos_options,
        width=300,
        border_color=ft.colors.WHITE
    )
    carga_input = ft.TextField(hint_text="Escribe un número...", keyboard_type=ft.KeyboardType.NUMBER, border_color=ft.colors.WHITE, on_change=validate_carga_promedio, width=300)
    ambiente_dropdown = ft.Dropdown(options=get_options_ambiente(), width=300, border_color=ft.colors.WHITE, label="Condiciones ambientales")
    recursos_dropdown = ft.Dropdown(options=get_options_recursos(), width=300, border_color=ft.colors.WHITE, label="Ciclos de encendido/apagado")
    refrigeracion_switch = ft.Switch(value=False)


    def formatear_meses_a_meses_dias(valor):
        meses = int(valor)
        dias = int(round((valor - meses) * 30))  # Aproximamos a 30 días por mes

        if meses > 0 and dias > 0:
            return f"{meses} mes{'es' if meses > 1 else ''} y {dias} día{'s' if dias > 1 else ''}"
        elif meses > 0:
            return f"{meses} mes{'es' if meses > 1 else ''}"
        else:
            return f"{dias} día{'s' if dias != 1 else ''}"
        
   
    def limpiar_valor(valor):
        if valor.endswith("+"):
            return int(valor[:-1])  # "3000+" -> 3000
        return int(valor)


    # Función para realizar predicción
    def realizar_prediccion(e):
        if not validar_campos_requeridos():
            page.snack_bar = ft.SnackBar(
                content=ft.Text("Por favor completa todos los campos obligatorios."),
                bgcolor=ft.colors.RED
            )
            page.snack_bar.open = True
            page.update()
            return


        if not validar_horas_y_ciclos(horas_input, ciclos_input):
            page.snack_bar = ft.SnackBar(content=ft.Text("Corrige los errores indicados."), bgcolor=ft.colors.RED)
            page.snack_bar.open = True
            page.update()
            return
        
        condiciones_ambiente = {
            'Óptimo': [1, 0, 0], 
            'Aceptable': [0, 1, 0], 
            'Crítico': [0, 0, 1]
        }

        tipo_aplicaciones = {
            "De bajo consumo de recursos": [1, 0, 0],
            "De mediano consumo de recursos": [0, 1, 0],
            "De alto consumo de recursos": [0, 0, 1]
        }

        datos_entrada = [
            int(meses_input.value),
            limpiar_valor(horas_input.value),
            limpiar_valor(ciclos_input.value),
            *condiciones_ambiente[ambiente_dropdown.value],
            *tipo_aplicaciones[recursos_dropdown.value],
            1 if refrigeracion_switch.value else 0,
            int(carga_input.value)
        ]

        prediccion = modelo.predict([datos_entrada])[0]
        prediccion_ajustada = max(min(prediccion, 10), 0.5)
        resultado.value = formatear_meses_a_meses_dias(prediccion_ajustada)
        resultado.update()


        # ➡️ Mostrar advertencia en texto si corresponde
        if prediccion_ajustada <= 0.5:
            mensaje_advertencia.value = "⚠️ Se recomienda hacer mantenimiento lo más pronto posible."
        else:
            mensaje_advertencia.value = ""  # Limpiar si no hay advertencia
        mensaje_advertencia.update()

        # Datos para el PDF y correo
        nombre_equipo = nombre_equipo_input.value
        correo_usuario = correo_input.value

        datos_equipo = {
            "Correo del usuario": correo_usuario,
            "Meses desde último mantenimiento": meses_input.value,
            "Horas totales de uso": horas_input.value,
            "Ciclos de Encendido/Apagado": ciclos_input.value,
            "Carga promedio (%)": carga_input.value,
            "Condiciones ambientales": ambiente_dropdown.value,
            "Tipo de aplicaciones": recursos_dropdown.value,
            "Refrigeración adicional": "Sí" if refrigeracion_switch.value else "No"
        }

        archivo_pdf = generar_reporte_pdf(nombre_equipo, datos_equipo, round(prediccion_ajustada, 1))
        archivo_ics = generar_evento_ics(nombre_equipo, prediccion_ajustada)

        # Enviar correo con ambos archivos
        if correo_usuario != "":
            if validar_correo(correo_usuario):
                enviar_correo_con_pdf(correo_usuario, nombre_equipo, archivo_pdf, archivo_ics)
            else:
                correo_input.error_text = "Correo electrónico no válido."
                correo_input.update()
                return

    boton_prediccion = ft.ElevatedButton(
        text="Calcular Tiempo",
        style=ft.ButtonStyle(color=ft.colors.WHITE, bgcolor='#0B9692'),
        on_click=realizar_prediccion,
    )


    #Contenedor de inputs
    inputs_container = ft.Column(
        controls=[
            ft.Text("Ingrese datos del equipo:", size=30, color=ft.colors.WHITE, weight="bold"),
            ft.Row([ft.Text("Nombre del equipo:", width=250, size=15, weight="bold", tooltip=ft.Tooltip(message="Nombre que le deseas asignar al computador a predecir el mantenimiento.",
                                                   padding=12,
                                                   bgcolor=ft.colors.WHITE,
                                                   text_style=ft.TextStyle(color=ft.colors.BLACK, size=13),
                                                   wait_duration=400,border_radius=8)), nombre_equipo_input], alignment=ft.MainAxisAlignment.CENTER),
            ft.Row([ft.Text("Correo electrónico:", width=250,size=15, weight="bold", tooltip=ft.Tooltip(message="Este correo electrónico se utilizará para enviarte un reporte sobre la predicción del mantenimiento.",
                                                   padding=12,
                                                   bgcolor=ft.colors.WHITE,
                                                   text_style=ft.TextStyle(color=ft.colors.BLACK, size=13),
                                                   wait_duration=400,border_radius=8)), correo_input],alignment=ft.MainAxisAlignment.CENTER, ),
            ft.Row([ft.Text("Tiempo en meses desde el último mantenimiento:", width=250,size=15, weight="bold", tooltip=ft.Tooltip(message="Si no conoce el tiempo desde el último mantenimiento realizado o nunca se le ha realizado mantenimiento, ingrese los meses que se conocen desde la adquisición del computador.",
                                                   padding=12,
                                                   bgcolor=ft.colors.WHITE,
                                                   text_style=ft.TextStyle(color=ft.colors.BLACK, size=13),
                                                   wait_duration=400,border_radius=8)), meses_input],alignment=ft.MainAxisAlignment.CENTER),
            ft.Row([ft.Text("Horas de Uso totales del equipo:", width=250,size=15, weight="bold", tooltip=ft.Tooltip(message="Horas totales que el equipo ha estado operativo desde que se utilizó por primera vez (los valores mostrados son aproximaciones)",
                                                   padding=12,
                                                   bgcolor=ft.colors.WHITE,
                                                   text_style=ft.TextStyle(color=ft.colors.BLACK, size=13),
                                                   wait_duration=400,border_radius=8)), horas_input],alignment=ft.MainAxisAlignment.CENTER),
            ft.Row([ft.Text("Ciclos de Encendido y Apagado del equipo:", width=250,size=15, weight="bold", tooltip=ft.Tooltip(message="Veces totales desde que el equipo se ha encendido y apagado desde que se utilizó por primera vez (los valores mostrados son aproximaciones)",
                                                   padding=12,
                                                   bgcolor=ft.colors.WHITE,
                                                   text_style=ft.TextStyle(color=ft.colors.BLACK, size=13),
                                                   wait_duration=400,border_radius=8)), ciclos_input],alignment=ft.MainAxisAlignment.CENTER),
            ft.Row([ft.Text("Carga de Trabajo Promedio del equipo (1 - 100%):", width=250,size=15, weight="bold", tooltip=ft.Tooltip(message="Carga promedio de trabajo del CPU desde que se utilizó por primera vez",
                                                   padding=12,
                                                   bgcolor=ft.colors.WHITE,
                                                   text_style=ft.TextStyle(color=ft.colors.BLACK, size=13),
                                                   wait_duration=400,border_radius=8)), carga_input],alignment=ft.MainAxisAlignment.CENTER),
            ft.Row([ft.Text("Condiciones ambientales del equipo:", width=250,size=15, weight="bold", tooltip=ft.Tooltip(message="Evalúa las condiciones ambientales donde opera el equipo:\n Óptimas: Ambiente limpio, buena ventilación y temperatura estable.\n Aceptables: Ambiente medianamente ventilado, posibles variaciones leves de temperatura y polvo moderado.\n Críticas: Ambiente poco ventilado, altas temperaturas, exposición frecuente a polvo o humedad.",
                                                   padding=12,
                                                   bgcolor=ft.colors.WHITE,
                                                   text_style=ft.TextStyle(color=ft.colors.BLACK, size=13),
                                                   wait_duration=400,border_radius=8)), ambiente_dropdown],alignment=ft.MainAxisAlignment.CENTER),
            ft.Row([ft.Text("Tipo de aplicaciones utilizadas:", width=250,size=15, weight="bold", tooltip=ft.Tooltip(message="Indica el tipo de aplicaciones generalmente ejecutadas en el equipo según su exigencia de recursos \n Bajo consumo: Aplicaciones ligeras (procesadores de texto, navegación básica, correo electrónico). \n Mediano consumo: Aplicaciones moderadas (edición básica multimedia, herramientas administrativas, multitarea frecuente). \n Alto consumo: Aplicaciones exigentes (edición avanzada, videojuegos, software de diseño gráfico o simulación).",
                                                   padding=12,
                                                   bgcolor=ft.colors.WHITE,
                                                   text_style=ft.TextStyle(color=ft.colors.BLACK, size=13),
                                                   wait_duration=400,border_radius=8)), recursos_dropdown],alignment=ft.MainAxisAlignment.CENTER),
            ft.Row([ft.Text("¿Tiene refrigeración adicional?:", width=250,size=15, weight="bold", tooltip=ft.Tooltip(message="Indica si el equipo tiene refrigeración adicional (ventiladores, refrigeración líquida, etc.)",
                                                   padding=12,
                                                   bgcolor=ft.colors.WHITE,
                                                   text_style=ft.TextStyle(color=ft.colors.BLACK, size=13),
                                                   wait_duration=400,border_radius=8)), refrigeracion_switch],alignment=ft.MainAxisAlignment.CENTER),
            texto_ayuda,
            boton_prediccion,
            
        ], alignment=ft.MainAxisAlignment.CENTER, horizontal_alignment=ft.CrossAxisAlignment.CENTER,
    )

    resultado = ft.Text("", size=40, color=ft.colors.WHITE, weight="bold", text_align=ft.TextAlign.CENTER)
    mensaje_advertencia = ft.Text("", size=16, color=ft.colors.WHITE, weight="bold", text_align=ft.TextAlign.CENTER)
    mensaje_status_correo = ft.Text("", size=16, color='#12FFD1', weight="bold", text_align=ft.TextAlign.CENTER)
    nota = ft.Text("\nNota: Es recomendable realizar mantenimiento \nperiódico a componentes críticos como el procesador, \nventiladores, memoria RAM, disco duro y fuente de poder.", size=14, color=ft.colors.WHITE70, italic=True)

    # Contenedor de resultados
    result_container = ft.Column(
    controls=[
       
        ft.Text("Tiempo estimado de mantenimiento:", size=24, color=ft.colors.WHITE, weight="bold", text_align=ft.TextAlign.CENTER),
        resultado,
        nota,
        mensaje_advertencia,
        mensaje_status_correo,
        boton_descargar_manual

    ],
    alignment=ft.MainAxisAlignment.CENTER,
    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
    expand=True  # Expandir para ocupar toda la altura disponible
)

    responsive_layout = ft.ResponsiveRow(
        [
            ft.Container(ft.Text("Sistema Predictivo de Mantenimiento", size=28, color="#12FFD1", weight="bold", text_align=ft.TextAlign.CENTER), col={"xs":12, "sm":12, "md":12, "lg":12}, alignment=ft.alignment.center),
            ft.Container(
                inputs_container,
                col={"xs":12, "sm":12, "md":12, "lg":6},
                alignment=ft.alignment.center,
                expand=True,  # Expandir para ocupar toda la altura disponible
            ),
            ft.Container(
                result_container,
                col={"xs":12, "sm":12, "md":12, "lg":6},
                alignment=ft.alignment.center,
                expand=True,  # Expandir para ocupar toda la altura disponible
            ),
        ],
        alignment=ft.MainAxisAlignment.CENTER,
        vertical_alignment=ft.CrossAxisAlignment.CENTER,
    )


    page.add(responsive_layout)

ft.app(target=main)
