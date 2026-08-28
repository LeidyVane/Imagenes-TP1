import os
import tkinter as tk #Importa el framework gráfico. Permite crear botones, ventanas, paneles y manejar eventos
from tkinter import filedialog, messagebox #Busca y guarda archivos en el disco/despliega cajas de diálogo.
from PIL import Image, ImageTk
import matplotlib.pyplot as plt

# Importamos las funciones del módulo de procesamiento
import funcionesTps as ft

# Variables Globales de Interfaz 
# Variables Globales (guarda los objetos Image de PIL en memoria)
imagen_original = None
imagen_modificada = None
# Referencias TK para evitar garbage collection (Guardan la versión PhotoImage para evitar que el recolector de basura de Python las borre de la memoria visual.
tk_original = None
tk_modificada = None
# Variables para selección con mouse (mantiene las coordenadas y la referencia gráfica del recuadro que dibuja el mouse.)
inicio_x = None
inicio_y = None
rect_id = None
region_seleccionada = None


# Ventana auxiliar para visualización simultánea
def abrir_ventana_secundaria(titulo, imagen_pil):
    if imagen_pil is None:
        return
    win = tk.Toplevel(ventana)
    """Abre una ventana independiente (Toplevel) para ver imágenes en simultáneo."""
    win.title(titulo)
    win.geometry("500x500")

    canvas = tk.Canvas(win, bg="gray")
    canvas.pack(fill="both", expand=True)

    tk_img = ImageTk.PhotoImage(imagen_pil)
    canvas.image = tk_img
    canvas.create_image(0, 0, anchor="nw", image=tk_img)


def actualizar_panel_modificado(nueva_img, mensaje=""):
    global imagen_modificada, tk_modificada
    imagen_modificada = nueva_img
    tk_modificada = ImageTk.PhotoImage(imagen_modificada)

    panel_modificado.delete("all")
    panel_modificado.config(
        width=imagen_modificada.width, height=imagen_modificada.height
    )
    panel_modificado.create_image(0, 0, anchor="nw", image=tk_modificada)

    if mensaje:
        txt_estado.config(text=mensaje)


#  Comandos

def cmd_cargar():
    global imagen_original, tk_original
    ruta = filedialog.askopenfilename(
        filetypes=[
            (
                "Imágenes",
                "*.png *.jpg *.jpeg *.bmp *.tiff *.pgm *.raw *.bin",
            ),
            ("Archivos RAW", "*.raw *.bin"),
            ("Todos los archivos", "*.*"),
        ]
    )
    if not ruta:
        return

    # Si es un archivo RAW, solicitamos dimensiones
    if ruta.lower().endswith((".raw", ".bin")): # Verifica si el archivo seleccionado termina en .raw o .bin
        win_raw = tk.Toplevel(ventana) # Crea una ventana flotante secundaria
        win_raw.title("Parámetros RAW") # le asigna un título 
        win_raw.geometry("250x150") # define su tamaño 
        win_raw.grab_set() # bloquea la ventana principal hasta que se defina la dimensión

        tk.Label(win_raw, text="Ancho (px):").grid( # Coloca una etiqueta de texto para el Ancho,
            row=0, column=0, padx=5, pady=5
        )
        ent_ancho = tk.Entry(win_raw, width=8) # Campo de entrada numérica
        ent_ancho.insert(0, "256") # valor por defecto
        ent_ancho.grid(row=0, column=1, padx=5, pady=5)

        tk.Label(win_raw, text="Alto (px):").grid( # para el alto
            row=1, column=0, padx=5, pady=5
        )
        ent_alto = tk.Entry(win_raw, width=8)
        ent_alto.insert(0, "256")
        ent_alto.grid(row=1, column=1, padx=5, pady=5)

        def procesar_raw(): # 
            global imagen_original, tk_original
            try:
                w = int(ent_ancho.get()) # lee el texto ingresado en los dos campos de entrada
                h = int(ent_alto.get())

                imagen_original = ft.cargar_imagen_raw( # Llama a la función para leer la secuencia binaria
                    ruta, w, h, modo="L"
                )
                mostrar_imagen_cargada(ruta) # actualiza los paneles de la interfaz
                win_raw.destroy() 
            except Exception as e:
                messagebox.showerror(
                    "Error RAW", f"No se pudo abrir la imagen RAW: {e}"
                )

        tk.Button(win_raw, text="Cargar", command=procesar_raw).grid( # botón "Cargar" dentro de la ventana procesar_raw.
            row=2, column=0, columnspan=2, pady=10
        )
    else:
        # Carga para formatos con encabezado (PNG, JPG, BMP, etc.)
        try:
            imagen_original = Image.open(ruta)
            mostrar_imagen_cargada(ruta)
        except Exception as e:
            messagebox.showerror(
                "Error", f"No se pudo cargar la imagen: {e}"
            )


# Función auxiliar para refrescar la visualización de las ventanas
def mostrar_imagen_cargada(ruta):
    global tk_original
    tk_original = ImageTk.PhotoImage(imagen_original)

    panel_original.config( # Ajusta el ancho y alto de la ventana izquierda al tamaño real de la imagen, 
        width=imagen_original.width, height=imagen_original.height
    )
    panel_original.delete("all") # elimina cualquier dibujo anterior 
    panel_original.create_image(0, 0, anchor="nw", image=tk_original) # proyecta la nueva imagen alineada arriba a la izquierda

    abrir_ventana_secundaria("Imagen Original", imagen_original)# Despliega la ventana emergente con la imagen limpia 
    txt_estado.config( # y actualiza la barra de estado con la ruta del archivo y las dimensiones en píxeles.
        text=f"Cargada: {ruta} ({imagen_original.width}x{imagen_original.height} px)"
    )

def cmd_guardar(): # Guarda una Imagen
    if imagen_modificada is None:
        messagebox.showwarning("Aviso", "No hay imagen modificada para guardar.")
        return

    ext_defecto = ".png"
    if (
        imagen_original
        and hasattr(imagen_original, "filename")
        and imagen_original.filename
    ):
        _, ext = os.path.splitext(imagen_original.filename)
        if ext:
            ext_defecto = ext.lower()

    ruta = filedialog.asksaveasfilename( # Abre el cuadro de diálogo Guardar Como
        defaultextension=ext_defecto,
        filetypes=[
            ("Formato Original", f"*{ext_defecto}"),
            ("PNG", "*.png"),
            ("JPEG", "*.jpg"),
            ("BMP", "*.bmp"),
        ],
    )
    if ruta:
        imagen_modificada.save(ruta)
        messagebox.showinfo("Éxito", "Imagen guardada correctamente.")


def cmd_tamano(): # Tamaño de la imagen
    if imagen_original is None:
        messagebox.showwarning("Aviso", "Cargue una imagen primero.")
        return
    ancho, alto, total = ft.obtener_tamano(imagen_original)
    messagebox.showinfo(
        "Tamaño",
        f"Ancho: {ancho} px\nAlto: {alto} px\nTotal Píxeles: {total:,} px",
    )


def cmd_pixel(): # Obtener y modificar pixel
    if imagen_original is None:
        messagebox.showwarning("Aviso", "Cargue una imagen primero.")
        return

    win = tk.Toplevel(ventana)# Crea una ventana emergente pequeña 
    win.title("Consultar / Modificar Píxel")
    win.geometry("280x160")
    win.grab_set()# impide interactuar con la ventana de atrás, evita clics en el panel del fondo por accidente.

    tk.Label(win, text="X:").grid(row=0, column=0) # Crea las etiquetas de texto que indican qué información colocar en cada casilla.
    ent_x = tk.Entry(win, width=6)
    ent_x.grid(row=0, column=1)

    tk.Label(win, text="Y:").grid(row=1, column=0)
    ent_y = tk.Entry(win, width=6)
    ent_y.grid(row=1, column=1)

    lbl_val = tk.Label(win, text="Valor: -")
    lbl_val.grid(row=2, column=0, columnspan=2)# organiza la ventana como una tabla de filas y columnas
    # columnspan permite que la etiqueta del resultado quede centrada debajo de las dos casillas superiores.

    def obtener_val():
        try:
            x, y = int(ent_x.get()), int(ent_y.get()) # Entradas para X e Y
            v = ft.consultar_pixel(imagen_original, x, y) # Extrae la intensidad de grises o una tupla si es a color, en la posición elegida
            lbl_val.config(text=f"Valor actual: {v}")
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def modificar_val():
        try:
            x, y = int(ent_x.get()), int(ent_y.get())
            raw = ent_val.get()
            val = (
                tuple(map(int, raw.split(","))) if "," in raw else int(raw) # interpreta si se ingresó un valor simple (gris) o un formato RGB
            )
            
            res = ft.modificar_pixel(imagen_original, x, y, val)
            actualizar_panel_modificado(res, f"Píxel ({x},{y}) cambiado")
            abrir_ventana_secundaria("Píxel Modificado", res)
            win.destroy() # Cierra la ventana emergente tras aplicar el cambio
        except Exception as e:
            messagebox.showerror("Error", str(e))

    tk.Button(win, text="Consultar", command=obtener_val).grid(row=0, column=2)
    tk.Label(win, text="Nuevo Val:").grid(row=3, column=0)
    ent_val = tk.Entry(win, width=10)
    ent_val.grid(row=3, column=1)
    tk.Button(win, text="Aplicar", command=modificar_val).grid(row=3, column=2)


def cmd_copiar_region():
    if imagen_original is None or region_seleccionada is None:
        messagebox.showwarning(
            "Aviso", "Cargue una imagen y seleccione un área."
        )
        return
    res = ft.recortar_region(imagen_original, region_seleccionada)
    actualizar_panel_modificado(res, "Región copiada correctamente.")
    abrir_ventana_secundaria("Región Copiada", res)


def cmd_resta():
    if imagen_original is None:
        messagebox.showwarning(
            "Aviso", "Cargue primero la imagen original."
        )
        return

    # Solicita la segunda imagen al usuario
    ruta_img2 = filedialog.askopenfilename(
        title="Seleccionar segunda imagen para restar",
        filetypes=[
            (
                "Imágenes",
                "*.png *.jpg *.jpeg *.bmp *.tiff *.pgm *.raw *.bin",
            ),
            ("Archivos RAW", "*.raw *.bin"),
            ("Todos los archivos", "*.*"),
        ],
    )

    if not ruta_img2:
        return  # Se canceló la selección

    # Función interna auxiliar para procesar la resta de dos objetos PIL
    def ejecutar_proceso_resta(img2_cargada):
        modo = "resize"

        # Evaluar diferencia de tamaño y preguntar al usuario
        if imagen_original.size != img2_cargada.size:
            respuesta = messagebox.askyesnocancel(
                "Dimensiones diferentes",
                "Las imágenes tienen tamaños distintos:\n\n"
                "• [Sí] -> Redimensionar la imagen para ajustar al tamaño.\n"
                "• [No] -> Rellenar con ceros la más chica.\n"
                "• [Cancelar] -> Abortar operación.",
            )

            if respuesta is None:
                return  # Presionó Cancelar
            elif respuesta is True:
                modo = "resize"
            else:
                modo = "padding"

        # Realizar la resta en el backend
        res = ft.restar_imagenes(
            imagen_original, img2_cargada, modo_ajuste=modo
        )
        actualizar_panel_modificado(res, "Resta de imágenes realizada")
        abrir_ventana_secundaria("Resultado Resta", res)

    # Cargar la segunda imagen según su extensión
    try:
        if ruta_img2.lower().endswith((".raw", ".bin")):
            # Si es RAW, solicitamos dimensiones
            win_raw = tk.Toplevel(ventana)
            win_raw.title("Dimensiones de la 2da Imagen RAW")
            win_raw.geometry("260x150")
            win_raw.grab_set()

            tk.Label(win_raw, text="Ancho (px):").grid(
                row=0, column=0, padx=5, pady=5
            )
            ent_ancho = tk.Entry(win_raw, width=8)
            ent_ancho.insert(0, str(imagen_original.width))
            ent_ancho.grid(row=0, column=1, padx=5, pady=5)

            tk.Label(win_raw, text="Alto (px):").grid(
                row=1, column=0, padx=5, pady=5
            )
            ent_alto = tk.Entry(win_raw, width=8)
            ent_alto.insert(0, str(imagen_original.height))
            ent_alto.grid(row=1, column=1, padx=5, pady=5)

            def procesar_resta_raw():
                try:
                    w = int(ent_ancho.get())
                    h = int(ent_alto.get())
                    img2 = ft.cargar_imagen_raw(ruta_img2, w, h, modo="L")

                    win_raw.destroy()
                    ejecutar_proceso_resta(img2)
                except Exception as e:
                    messagebox.showerror(
                        "Error RAW", f"No se pudo procesar la resta: {e}"
                    )

            tk.Button(
                win_raw, text="Restar", command=procesar_resta_raw
            ).grid(row=2, column=0, columnspan=2, pady=10)
        else:
            # Carga tradicional para PNG, JPG, BMP, etc.
            img2 = Image.open(ruta_img2)
            ejecutar_proceso_resta(img2)

    except Exception as e:
        messagebox.showerror(
            "Error en Resta", f"No se pudo ejecutar la resta: {e}"
        )

def cmd_analizar():
    if imagen_original is None or region_seleccionada is None:
        messagebox.showwarning(
            "Aviso", "Cargue una imagen y seleccione un área."
        )
        return
    px, promedios, modo = ft.analizar_region(
        imagen_original, region_seleccionada
    )
    if modo == "L": # Es una propiedad de PIL que indica el modo de color o formato de píxeles que usa la imagen.
        msg = f"Píxeles: {px}\nPromedio Gris: {promedios[0]:.2f}"
    else:
        msg = f"Píxeles: {px}\nPromedio RGB:\n  R: {promedios[0]:.2f}\n  G: {promedios[1]:.2f}\n  B: {promedios[2]:.2f}"
    messagebox.showinfo("Estadísticas", msg)


def cmd_gamma():
    if imagen_original is None:
        messagebox.showwarning("Aviso", "Cargue una imagen primero.")
        return

    win = tk.Toplevel(ventana)
    win.title("Transformación Gamma")
    win.geometry("260x120")
    win.grab_set()

    tk.Label(win, text="Valor Gamma (0 < γ < 2, γ ≠ 1):").pack(pady=5)
    ent_g = tk.Entry(win, width=8)
    ent_g.insert(0, "0.5")
    ent_g.pack(pady=5)

    def ejecutar():
        try:
            g = float(ent_g.get())
            if not (0 < g < 2) or g == 1:
                messagebox.showerror(
                    "Error", "Gamma debe cumplir 0 < γ < 2 y γ ≠ 1"
                )
                return
            res = ft.transformacion_gamma(imagen_original, g)
            actualizar_panel_modificado(res, f"Transformación Gamma (γ={g})")
            abrir_ventana_secundaria(f"Gamma (γ={g})", res)
            win.destroy()
        except ValueError:
            messagebox.showerror("Error", "Ingrese un número válido.")

    tk.Button(win, text="Aplicar", command=ejecutar).pack(pady=5)

def cmd_negativo():
    if imagen_original is None:
        messagebox.showwarning("Aviso", "Cargue una imagen primero.")
        return

    # Llamamos a la función del archivo de procesamiento
    res = ft.aplicar_negativo(imagen_original)

    # Actualizamos el panel derecho y abrimos ventana secundaria
    actualizar_panel_modificado(res, "Filtro Negativo aplicado con éxito.")
    abrir_ventana_secundaria("Imagen Negativa", res)

def cmd_binarizar():
    if imagen_original is None:
        messagebox.showwarning("Aviso", "Cargue una imagen primero.")
        return

    win = tk.Toplevel(ventana)
    win.title("Binarización")
    win.geometry("260x120")
    win.grab_set()

    tk.Label(win, text="Ingrese el Umbral (0 - 255):").pack(pady=5)
    ent_u = tk.Entry(win, width=8)
    ent_u.insert(0, "128")  # Valor por defecto típico
    ent_u.pack(pady=5)

    def ejecutar():
        try:
            u = int(ent_u.get())
            if not (0 <= u <= 255):
                messagebox.showerror(
                    "Error", "El umbral debe estar entre 0 y 255."
                )
                return

            res = ft.binarizar_imagen(imagen_original, u)
            actualizar_panel_modificado(res, f"Binarización (Umbral={u})")
            abrir_ventana_secundaria(f"Binarizada (U={u})", res)
            win.destroy()
        except ValueError:
            messagebox.showerror("Error", "Ingrese un número entero válido.")

    tk.Button(win, text="Aplicar", command=ejecutar).pack(pady=5)

def cmd_histograma():
    if imagen_original is None:
        messagebox.showwarning("Aviso", "Cargue una imagen primero.")
        return

    # Obtener el diccionario de frecuencias relativas
    hist = ft.obtener_histograma(imagen_original)

    # Separar claves (niveles de gris 0-255) y valores (frecuencia relativa)
    niveles = list(hist.keys())
    frecuencias = list(hist.values())

    # Graficar con Matplotlib
    plt.figure("Histograma de Grises")
    plt.bar(
        niveles, frecuencias, color="gray", width=1.0, edgecolor="black", lw=0.2
    )
    plt.title("Histograma de Frecuencias Relativas")
    plt.xlabel("Nivel de Gris (0 - 255)")
    plt.ylabel("Frecuencia Relativa")
    plt.xlim([0, 255])
    plt.grid(axis="y", linestyle="--", alpha=0.7)
    plt.show()

def cmd_ecualizar():
    if imagen_original is None:
        messagebox.showwarning("Aviso", "Cargue una imagen primero.")
        return

    res = ft.aplicar_ecualizacion(imagen_original)
    actualizar_panel_modificado(res, "Ecualización de histograma aplicada.")
    abrir_ventana_secundaria("Imagen Ecualizada", res)

def cmd_ruido_gaussiano():
    """Abre la ventana modal para aplicar Ruido Gaussiano Aditivo."""
    if imagen_original is None:
        messagebox.showwarning(
            "Aviso", "Cargue primero la imagen base (original)."
        )
        return

    win_gauss = tk.Toplevel(ventana)
    win_gauss.title("Contaminar - Ruido Gaussiano")
    win_gauss.geometry("320x220")
    win_gauss.resizable(False, False)
    win_gauss.grab_set()

    # Entradas de texto
    tk.Label(win_gauss, text="Porcentaje de píxeles (%):").grid(
        row=0, column=0, padx=10, pady=8, sticky="w"
    )
    ent_porcentaje = tk.Entry(win_gauss, width=10)
    ent_porcentaje.insert(0, "10")
    ent_porcentaje.grid(row=0, column=1, padx=10, pady=8)

    tk.Label(win_gauss, text="Desviación Estándar (σ):").grid(
        row=1, column=0, padx=10, pady=8, sticky="w"
    )
    ent_sigma = tk.Entry(win_gauss, width=10)
    ent_sigma.insert(0, "25.0")
    ent_sigma.grid(row=1, column=1, padx=10, pady=8)

    # Checkbox para graficar histograma
    var_graficar = tk.BooleanVar(value=False)
    chk_graficar = tk.Checkbutton(
        win_gauss, text="Graficar Distribución", variable=var_graficar
    )
    chk_graficar.grid(row=2, column=0, columnspan=2, pady=5)

    def aplicar_gauss():
        try:
            porcentaje = float(ent_porcentaje.get())
            sigma = float(ent_sigma.get())

            if not (0 <= porcentaje <= 100):
                messagebox.showerror(
                    "Error", "El porcentaje debe estar entre 0 y 100."
                )
                return

            # Graficar histograma de la muestra si está activado
            if var_graficar.get():
                cant_pixeles = int(
                    (imagen_original.width * imagen_original.height)
                    * (porcentaje / 100.0)
                )
                ft.generar_datos_gauss(
                    mu=0,
                    sigma=sigma,
                    cant=max(cant_pixeles, 1000),
                    graficar_distribucion=True,
                )

            # Aplicar la contaminación sobre la imagen
            img_contaminada = ft.contaminar_ruido_gauss(
                imagen_original, porcentaje, sigma
            )
            actualizar_panel_modificado(
                img_contaminada, f"Ruido Gaussiano (p={porcentaje}%, σ={sigma})"
            )
            abrir_ventana_secundaria("Imagen con Ruido Gaussiano", img_contaminada)
            win_gauss.destroy()

        except ValueError:
            messagebox.showerror(
                "Error", "Ingrese valores numéricos válidos."
            )

    tk.Button(
        win_gauss,
        text="Aplicar Ruido",
        command=aplicar_gauss,
        bg="#4CAF50",
        fg="white",
    ).grid(row=3, column=0, columnspan=2, pady=12)


def cmd_ruido_exponencial():
    """Abre la ventana modal para aplicar Ruido Exponencial Multiplicativo."""
    if imagen_original is None:
        messagebox.showwarning(
            "Aviso", "Cargue primero la imagen base (original)."
        )
        return

    win_exp = tk.Toplevel(ventana)
    win_exp.title("Contaminar - Ruido Exponencial")
    win_exp.geometry("320x220")
    win_exp.resizable(False, False)
    win_exp.grab_set()

    # Entradas de texto
    tk.Label(win_exp, text="Porcentaje de píxeles (%):").grid(
        row=0, column=0, padx=10, pady=8, sticky="w"
    )
    ent_porcentaje = tk.Entry(win_exp, width=10)
    ent_porcentaje.insert(0, "10")
    ent_porcentaje.grid(row=0, column=1, padx=10, pady=8)

    tk.Label(win_exp, text="Parámetro Lambda (λ):").grid(
        row=1, column=0, padx=10, pady=8, sticky="w"
    )
    ent_lambda = tk.Entry(win_exp, width=10)
    ent_lambda.insert(0, "1.0")
    ent_lambda.grid(row=1, column=1, padx=10, pady=8)

    # Checkbox para graficar histograma
    var_graficar = tk.BooleanVar(value=False)
    chk_graficar = tk.Checkbutton(
        win_exp, text="Graficar Distribución", variable=var_graficar
    )
    chk_graficar.grid(row=2, column=0, columnspan=2, pady=5)

    def aplicar_exp():
        try:
            porcentaje = float(ent_porcentaje.get())
            lambd = float(ent_lambda.get())

            if not (0 <= porcentaje <= 100):
                messagebox.showerror(
                    "Error", "El porcentaje debe estar entre 0 y 100."
                )
                return
            if lambd <= 0:
                messagebox.showerror(
                    "Error", "El valor de Lambda debe ser positivo (λ > 0)."
                )
                return

            # Graficar histograma de la muestra si está activado
            if var_graficar.get():
                cant_pixeles = int(
                    (imagen_original.width * imagen_original.height)
                    * (porcentaje / 100.0)
                )
                ft.generar_datos_exponencial(
                    lambd=lambd,
                    cant=max(cant_pixeles, 1000),
                    graficar_distribucion=True,
                )

            # Aplicar la contaminación sobre la imagen
            img_contaminada = ft.contaminar_ruido_exponencial(
                imagen_original, porcentaje, lambd
            )
            actualizar_panel_modificado(
                img_contaminada, f"Ruido Exponencial (p={porcentaje}%, λ={lambd})"
            )
            abrir_ventana_secundaria("Imagen con Ruido Exponencial", img_contaminada)
            win_exp.destroy()

        except ValueError:
            messagebox.showerror(
                "Error", "Ingrese valores numéricos válidos."
            )

    tk.Button(
        win_exp,
        text="Aplicar Ruido",
        command=aplicar_exp,
        bg="#4CAF50",
        fg="white",
    ).grid(row=3, column=0, columnspan=2, pady=12)

def cmd_ruido_sal_pimienta():
    if imagen_original is None:
        messagebox.showwarning(
            "Aviso", "Cargue primero la imagen base (original)."
        )
        return

    win_sp = tk.Toplevel(ventana)
    win_sp.title("Ruido Sal y Pimienta")
    win_sp.geometry("300x160")
    win_sp.resizable(False, False)
    win_sp.grab_set()

    tk.Label(win_sp, text="Probabilidad p (0 a 0.5):").grid(
        row=0, column=0, padx=10, pady=12, sticky="w"
    )
    ent_p = tk.Entry(win_sp, width=10)
    ent_p.insert(0, "0.05")
    ent_p.grid(row=0, column=1, padx=10, pady=12)

    def aplicar_sp():
        try:
            p = float(ent_p.get())
            if not (0 <= p <= 0.5):
                messagebox.showerror(
                    "Error", "El valor de p debe estar entre 0 y 0.5"
                )
                return

            res = ft.contaminar_sal_pimienta(imagen_original, p)
            actualizar_panel_modificado(res, f"Sal y Pimienta (p={p})")
            abrir_ventana_secundaria("Ruido Sal y Pimienta", res)
            win_sp.destroy()
        except ValueError:
            messagebox.showerror("Error", "Ingrese un valor numérico válido.")
    tk.Button(
        win_sp,
        text="Aplicar Ruido",
        command=aplicar_sp,
        bg="#4CAF50",
        fg="white",
    ).grid(row=1, column=0, columnspan=2, pady=10)


#  Eventos Mouse 
def empezar_sel(e):
    global inicio_x, inicio_y, rect_id
    if imagen_original is None:
        return
    inicio_x, inicio_y = e.x, e.y
    if rect_id:
        panel_original.delete(rect_id)
    rect_id = panel_original.create_rectangle(
        inicio_x, inicio_y, inicio_x, inicio_y, outline="red", width=2
    )


def arrastrar_sel(e):
    if rect_id:
        panel_original.coords(rect_id, inicio_x, inicio_y, e.x, e.y)


def finalizar_sel(e):
    global region_seleccionada
    if inicio_x is not None and imagen_original is not None:
        fin_x, fin_y = e.x, e.y
        region_seleccionada = (
            min(inicio_x, fin_x),
            min(inicio_y, fin_y),
            max(inicio_x, fin_x),
            max(inicio_y, fin_y),
        )


#  Construcción de la Interfaz 
ventana = tk.Tk()
ventana.title("Procesamiento de Imágenes - Universidad")
ventana.geometry("1000x650")

txt_estado = tk.Label(
    ventana,
    text="Bienvenido. Cargue una imagen para comenzar.",
    bd=1,
    relief="sunken",
    anchor="w",
)
txt_estado.pack(side="bottom", fill="x")



# Frames
#  Panel de Control Lateral (Botones) 
panel_control = tk.Frame(ventana, width=220)
panel_control.pack(side="left", fill="y", padx=5, pady=5)

# Frame contenedor 
frame_operaciones = tk.Frame(panel_control, padx=5, pady=5)
frame_operaciones.pack(fill="x", padx=5, pady=5)

# Lista continua de botones
tk.Button(
    frame_operaciones, text="Cargar Imagen", command=cmd_cargar
).pack(fill="x", pady=2)
tk.Button(
    frame_operaciones, text="Guardar Imagen", command=cmd_guardar
).pack(fill="x", pady=2)
tk.Button(
    frame_operaciones, text="Obtener Tamaño (px)", command=cmd_tamano
).pack(fill="x", pady=2)
tk.Button(
    frame_operaciones, text="Consultar/Modificar Píxel", command=cmd_pixel
).pack(fill="x", pady=2)
tk.Button(
    frame_operaciones,
    text="Copiar Región Seleccionada",
    command=cmd_copiar_region,
).pack(fill="x", pady=2)
tk.Button(
    frame_operaciones, text="Resta de 2 Imágenes", command=cmd_resta
).pack(fill="x", pady=2)
tk.Button(
    frame_operaciones, text="Analizar Región", command=cmd_analizar
).pack(fill="x", pady=2)
tk.Button(
    frame_operaciones, text="Transformación Gamma", command=cmd_gamma
).pack(fill="x", pady=2)
tk.Button(
    frame_operaciones, text="Aplicar Negativo", command=cmd_negativo
).pack(fill="x", pady=2)
tk.Button(
    frame_operaciones, text="Binarizar Imagen", command=cmd_binarizar
).pack(fill="x", pady=2)
tk.Button(
    frame_operaciones, text="Calcular Histograma", command=cmd_histograma
).pack(fill="x", pady=2)
tk.Button(
    frame_operaciones, text="Ecualizar Histograma", command=cmd_ecualizar
).pack(fill="x", pady=2)
frame_ruidos = tk.LabelFrame(frame_operaciones, text=" Ruido ")
frame_ruidos.pack(side="top", padx=5, pady=5, fill="x")

btn_gauss = tk.Button(
    frame_ruidos, text="Ruido Gaussiano", command=cmd_ruido_gaussiano
)
btn_gauss.pack(side="top", padx=5, pady=3, fill="x")

btn_exp = tk.Button(
    frame_ruidos, text="Ruido Exponencial", command=cmd_ruido_exponencial
)
btn_exp.pack(side="top", padx=5, pady=3, fill="x")

btn_sp = tk.Button(
    frame_ruidos,text="Ruido Sal y Pimienta", command=cmd_ruido_sal_pimienta,
)
btn_sp.pack(side="top", padx=5, pady=5, fill="x")

# Paneles de Imágenes
zona_imagenes = tk.Frame(ventana, bg="gray") # marco contenedor rectangular a la derecha de  
                                             #la barra lateral de botones, con fondo gris.
zona_imagenes.pack(side="right", expand=True, fill="both", padx=5, pady=5) # Se ubica a la derecha, ocupa todo
  # el espacio disponible y permite que se estire horizontal y verticalmente.

frame_izq = tk.Frame(zona_imagenes) # Panel para la imagen original
frame_izq.pack(side="left", expand=True, fill="both", padx=2, pady=2)
panel_original = tk.Canvas(frame_izq, bg="darkgray")
panel_original.pack(expand=True, fill="both")

frame_der = tk.Frame(zona_imagenes) # Panel para la imagen modificada
frame_der.pack(side="right", expand=True, fill="both", padx=2, pady=2)
panel_modificado = tk.Canvas(frame_der, bg="darkgray")
panel_modificado.pack(expand=True, fill="both")

# Binds del Mouse
panel_original.bind("<Button-1>", empezar_sel) # vincula en boton izq. con empezar seleccion
panel_original.bind("<B1-Motion>", arrastrar_sel) # mover el mouse mientras se mantiene presionado el botón izquierdo
panel_original.bind("<ButtonRelease-1>", finalizar_sel) # Representa el evento de soltar el botón izquierdo del mouse."

ventana.mainloop() # Inicia el ciclo que mantiene escuchando eventos 
                   #(clics, teclas, redimensionamientos) de la interfaz gráfica.