import os
import numpy as np
from PIL import Image, ImageChops, ImageStat
import matplotlib.pyplot as plt


def cargar_imagen_raw(ruta_archivo, ancho, alto, modo="L"):
    # Leemos el contenido binario crudo del archivo
    with open(ruta_archivo, "rb") as f:
        datos_raw = f.read()

    # Creamos la imagen PIL a partir del mapa de bytes crudos
    imagen_pil = Image.frombytes(modo, (ancho, alto), datos_raw)
    return imagen_pil


def obtener_tamano(imagen_pil):  
    """Devuelve (ancho, alto, total_pixels) de una imagen PIL."""
    if imagen_pil is None:
        return None
    ancho, alto = imagen_pil.size
    return ancho, alto, ancho * alto


def consultar_pixel(imagen_pil, x, y): 
    """Devuelve el valor del píxel en (x, y)."""
    return imagen_pil.getpixel((x, y))


def modificar_pixel(imagen_pil, x, y, nuevo_valor):
    """Retorna una copia de la imagen con el píxel modificado."""
    copia = imagen_pil.copy() # Copia la imagen original para no per
    copia.putpixel((x, y), nuevo_valor) # Escribe el nuevo valor en el píxel indicado
               # Parsea la entrada para determinar si es un valor de gris (128) o RGB (255, 0, 0)
    return copia


def recortar_region(imagen_pil, region_box):
    """Recorta la región definida por (left, top, right, bottom)."""
    return imagen_pil.crop(region_box) # Toma la tupla de coordenadas (izquierda, arriba, derecha, abajo) 
                                       # generada con el mouse y genera un nuevo objeto imagen independiente.


def igualar_dimensiones_padding(img_chica, ancho_meta, alto_meta):
    """Crea una imagen negra del tamaño objetivo y coloca la imagen chica en (0,0) sin alterar sus píxeles."""
    lienzo_negro = Image.new(
        img_chica.mode, (ancho_meta, alto_meta), color=0
    )
    lienzo_negro.paste(img_chica, (0, 0))
    return lienzo_negro


def restar_imagenes(img1_pil, img2_pil, modo_ajuste="resize"):
    w1, h1 = img1_pil.size
    w2, h2 = img2_pil.size

    # Resolvermos diferencia de dimensiones 
    if (w1, h1) != (w2, h2):
        if modo_ajuste == "resize":
            # Redimensiona la segunda imagen para igualar a la primera
            img2_pil = img2_pil.resize((w1, h1))

        elif modo_ajuste == "padding":
            # Rellena con ceros (negro) la imagen más chica para no distorsionar píxeles
            ancho_max = max(w1, w2)
            alto_max = max(h1, h2)

            if (w1, h1) != (ancho_max, alto_max):
                img1_pil = igualar_dimensiones_padding(
                    img1_pil, ancho_max, alto_max
                )
            if (w2, h2) != (ancho_max, alto_max):
                img2_pil = igualar_dimensiones_padding(
                    img2_pil, ancho_max, alto_max
                )

    # Convertimos modos de color si difieren (ej: RGB vs L)
    if img1_pil.mode != img2_pil.mode:
        img2_pil = img2_pil.convert(img1_pil.mode)

    # Operación matemática evitando el overflow 
    arr1 = np.array(img1_pil, dtype=np.float32)
    arr2 = np.array(img2_pil, dtype=np.float32)

    resta = arr1 - arr2
    resta_clamped = np.clip(resta, 0, 255).astype(np.uint8)

    return Image.fromarray(resta_clamped)


def analizar_region(imagen_pil, region_box):
    """Devuelve la cantidad de píxeles y el promedio por canal en la región."""
    recorte = imagen_pil.crop(region_box)
    total_px = recorte.width * recorte.height
    stats = ImageStat.Stat(recorte)
    return total_px, stats.mean, recorte.mode


def transformacion_gamma(imagen, gamma):

    # Convertimos a float para que las potencias no desborden la memoria
    arr_imagen = np.array(imagen, dtype=np.float64)

    # Calculamos la constante c 
    c = 255 / (255**gamma)

    # Recorremos cada píxel 
    for x in range(arr_imagen.shape[0]):
        for y in range(arr_imagen.shape[1]):
            r = arr_imagen[x, y]
            arr_imagen[x, y] = c * (r**gamma)

    # Aseguramos que los valores estén entre 0 y 255 y volvemos a enteros uint8
    arr_imagen = np.clip(arr_imagen, 0, 255).astype(np.uint8) # tipo uint8 (enteros de 8 bits, de 0 a 255)        

    imagen_transformada = Image.fromarray(arr_imagen)
    return imagen_transformada

def aplicar_negativo(imagen_pil):
    # Convertimos a entero con signo para realizar restas de forma segura
    arr_imagen = np.array(imagen_pil, dtype=np.int32)

    # Recorremos cada píxel
    for x in range(arr_imagen.shape[0]):
        for y in range(arr_imagen.shape[1]):
            arr_imagen[x, y] = 255 - arr_imagen[x, y]

    # Convertimos a uint8 (enteros de 0 a 255)
    arr_imagen = arr_imagen.astype(np.uint8)

    return Image.fromarray(arr_imagen)

def binarizar_imagen(imagen_pil, umbral):
    # Convertimos primero a escala de grises para tener 1 solo valor por píxel
    img_gris = imagen_pil.convert("L")
    arr_imagen = np.array(img_gris)

    for x in range(arr_imagen.shape[0]):
        for y in range(arr_imagen.shape[1]):
            r = arr_imagen[x, y]
            if r >= umbral:
                arr_imagen[x, y] = 255
            else:
                arr_imagen[x, y] = 0

    return Image.fromarray(arr_imagen)

def obtener_histograma(imagen_pil):
    # Aseguramos escala de grises
    img_gris = imagen_pil.convert("L")
    arr_imagen = np.array(img_gris)
    total_pixeles = arr_imagen.size

    # Obtenemos valores presentes y sus frecuencias absolutas
    valores, conteos = np.unique(arr_imagen, return_counts=True)

    # Creamos un arreglo con 256 ceros para asegurar que estén todos los niveles de gris
    frecuencias_relativas = np.zeros(256, dtype=np.float64)

    # Mapeamos los valores presentes a su frecuencia relativa
    frecuencias_relativas[valores] = conteos / total_pixeles

    # Generamos el diccionario de {nivel_gris: frecuencia_relativa}
    frecuencias = {k: v for k, v in enumerate(frecuencias_relativas)}

    return frecuencias

def obtener_prob_y_norm(valor, suma, s_min, total_pixeles):# calcula la frecuencia acumulada y la mapea 
                                                           #a un nuevo nivel de gris normalizado para cada tono
    prob = valor / total_pixeles # Calcula la probabilidad de ocurrencia del nivel de gris
    s_k = prob + suma # Suma la probabilidad actual al acumulado anterior.
    if s_min == 0 and s_k != 0:
        s_min = s_k # Registra el primer valor acumulado distinto de cero

    
    denominador = 1 - s_min # Calcula el denominador
    if denominador == 0:   # Evitamos división por cero si la imagen es completamente homogénea
        s_k_norm = 255 * s_k
    else:
        s_k_norm = 255 * ((s_k - s_min) / denominador) # Calculamos la fórmula de normalización T(rk)

    return s_k, round(s_k_norm), s_min


def aplicar_ecualizacion(imagen_pil):
    # Aseguramos formato escala de grises
    img_gris = imagen_pil.convert("L")
    frecuencias = obtener_histograma(img_gris)
    arr_imagen = np.array(img_gris, dtype=np.uint8)

    acum = 0
    s_min = 0
    total_pixeles = sum(frecuencias.values())
    tabla = {}

    # Crear Look-Up Table 
    for i in range(256): # Recorre los 256 niveles de gris
        frecuencia = frecuencias.get(i, 0)
        acum, s_k_norm, s_min = obtener_prob_y_norm( # Para cada tono llama a obtener_prob_y_norm
            frecuencia, acum, s_min, total_pixeles
        )
        tabla[i] = np.uint8(np.clip(s_k_norm, 0, 255))# guarda en el diccionario tabla la relación 
                                                      # nivel_original : nuevo_nivel_ecualizado.
        # Recorta (satura) el valor del cálculo. Si por algún redondeo o decimal flotante s_k_norm  
        # llega a dar menor a 0, lo fuerza a 0. Si supera 255, lo fuerza a 255.

    # Reemplazar valores en la matriz
    for x in range(arr_imagen.shape[0]):
        for y in range(arr_imagen.shape[1]):
            nivel_gris = arr_imagen[x, y]
            arr_imagen[x, y] = tabla[nivel_gris]

    return Image.fromarray(arr_imagen)

# Generar datos para ruido

def graficar_distribucion(
    datos, titulo="Distribución de Ruido", xlabel="Valores", bins=50
):
    """Función auxiliar para renderizar el histograma."""
    plt.figure(figsize=(7, 4))
    plt.hist(
        datos,
        bins=bins,
        color="skyblue",
        edgecolor="black",
        alpha=0.7,
        density=True,
    )
    plt.title(titulo)
    plt.xlabel(xlabel)
    plt.ylabel("Densidad")
    plt.grid(True, linestyle="--", alpha=0.5)
    plt.show()

def generar_datos_gauss(mu=0.0, sigma=1.0, cant=10000, graficar=False):
    """Genera una cantidad N de valores aleatorios con distribución Gaussiana."""
    datos = np.random.normal(loc=mu, scale=sigma, size=cant)

    # Graficado opcional mediante la función externa
    if graficar:
        graficar_distribucion(
            datos,
            titulo=f"Distribución Gaussiana (μ={mu}, σ={sigma})",
            xlabel="Valores de ruido",
        )

    return datos

def generar_datos_exponencial(lambd, cant=10000, graficar_distribucion=False):
    """Genera N valores aleatorios con distribución Exponencial"""
    # Generamos x ~ U(0, 1) evitando 0 absoluto para no calcular log(0)
    x = np.random.uniform(1e-10, 1.0, cant)

    # Transformada inversa
    datos_exp = -(1.0 / lambd) * np.log(x)

    # Graficado opcional mediante la función externa
    if graficar_distribucion:
        graficar_distribucion(
            datos_exp,
            titulo=f"Distribución Exponencial (λ={lambd})",
            xlabel="Valores de ruido",
        )

    return datos_exp

# Contaminar con ruido

def contaminar_ruido_gauss(imagen_pil, porcentaje, sigma):
    """
    1. d = porcentaje * total_pixeles.
    2. D = conjunto de d píxeles seleccionados aleatoriamente.
    3. Generar d valores aleatorios Gaussianos con μ=0 y σ.
    4. Para cada (i,j) ∈ D: IC(i,j) = I(i,j) + yk; si no, queda igual.
    """

    arr_imagen = np.array(imagen_pil, dtype=np.float64)

    if arr_imagen.ndim == 3:
        filas, columnas, canales = arr_imagen.shape
    else:
        filas, columnas = arr_imagen.shape
        canales = 1

    cant_pixeles = filas * columnas
    cant_a_contaminar = int(cant_pixeles * (porcentaje / 100))

    if cant_a_contaminar <= 0:
        return imagen_pil.copy()

    # Selección directa de índices lineales 
    indices = np.random.choice(
        cant_pixeles, cant_a_contaminar, replace=False
    )

    if canales > 1:
        # Reestructuramos la matriz a 2D (pixeles_totales, canales) 
        arr_plano = arr_imagen.reshape(-1, canales)
        for c in range(canales):
            datos_gauss = generar_datos_gauss(0, sigma, cant_a_contaminar)
            # Asignación vectorizada 
            arr_plano[indices, c] += datos_gauss
    else:
        arr_plano = arr_imagen.ravel()
        datos_gauss = generar_datos_gauss(0, sigma, cant_a_contaminar)
        arr_plano[indices] += datos_gauss

    arr_imagen = np.clip(arr_imagen, 0, 255).astype(np.uint8)
    return Image.fromarray(arr_imagen)

def contaminar_ruido_exponencial(imagen_pil, porcentaje, lambd):
    # Convertir a float64 para evitar desbordamientos en la multiplicación
    arr_imagen = np.array(imagen_pil, dtype=np.float64)

    # Detectar dimensiones y cantidad de canales
    if arr_imagen.ndim == 3:
        filas, columnas, canales = arr_imagen.shape
    else:
        filas, columnas = arr_imagen.shape
        canales = 1

    total_pixeles = filas * columnas
    cant_a_contaminar = int(total_pixeles * (porcentaje / 100.0))

    if cant_a_contaminar <= 0:
        return imagen_pil.copy()

    # Selección vectorizada de índices (Conjunto D)
    indices_D = np.random.choice(
        total_pixeles, size=cant_a_contaminar, replace=False
    )

    # Generar datos aleatorios exponenciales
    datos_exp = generar_datos_exponencial(lambd, cant_a_contaminar)

    # Vista aplanada y multiplicación vectorizada 
    arr_plano = arr_imagen.reshape(-1, canales)

    if canales == 1:
        # En escala de grises, multiplica directamente el vector de ruido
        arr_plano[indices_D, 0] *= datos_exp
    else:
        # En RGB, aplica el factor escalar de ruido a los 3 canales por igual
        arr_plano[indices_D] *= datos_exp[:, np.newaxis]

    # Recorte al rango válido [0, 255] y conversión a uint8
    arr_imagen = np.clip(arr_imagen, 0, 255).astype(np.uint8)

    return Image.fromarray(arr_imagen)

def contaminar_sal_pimienta(img_pil, p):
    """Aplica ruido Sal y Pimienta a la imagen.

    Parámetros:
    - img_pil: imagen original 
    - p: probabilidad individual de cada tipo de ruido (0 <= p <= 0.5).
         - Sal (píxeles blancos = 255) con probabilidad p.
         - Pimienta (píxeles negros = 0) con probabilidad p.
         Densidad total de contaminación = 2 * p.

    """
    if p < 0 or p > 0.5:
        raise ValueError("El valor de p debe estar en el rango [0, 0.5]")

    # Convertir la imagen a arreglo de NumPy
    arr_img = np.array(img_pil).copy()

    # Generar matriz de números aleatorios U(0, 1) solo para alto y ancho
    forma_espacial = arr_img.shape[:2]
    rand = np.random.random(forma_espacial)

    # Definir máscaras booleanas
    mask_pimienta = rand < p  # Pimienta (Negro = 0)
    mask_sal = rand >= (1.0 - p)  # Sal (Blanco = 255)

    # Aplicar los valores según el tipo de imagen (Grises o RGB)
    if arr_img.ndim == 2:  # Grises
        arr_img[mask_pimienta] = 0
        arr_img[mask_sal] = 255
    else:  # RGB (aplica 0 o 255 a los 3 canales simultáneamente)
        arr_img[mask_pimienta] = [0, 0, 0]
        arr_img[mask_sal] = [255, 255, 255]

    return Image.fromarray(arr_img.astype(np.uint8))


