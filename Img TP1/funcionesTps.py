import os
import numpy as np
from PIL import Image, ImageChops, ImageStat
import matplotlib.pyplot as plt

# Utilidades Generales

def cargar_imagen_raw(ruta_archivo, ancho, alto, modo="L"):
    """Carga una imagen RAW sin cabecera indicando ancho, alto y modo PIL."""
    with open(ruta_archivo, "rb") as f:
        datos_raw = f.read()

    canales = {"L": 1, "RGB": 3}.get(modo)
    if canales is None:
        raise ValueError("Modo RAW no soportado. Use 'L' o 'RGB'.")

    esperado = ancho * alto * canales
    if len(datos_raw) != esperado:
        raise ValueError(
            f"El RAW contiene {len(datos_raw)} bytes, pero se esperaban "
            f"{esperado} para {ancho}x{alto} en modo {modo}."
        )

    return Image.frombytes(modo, (ancho, alto), datos_raw)

def obtener_tamano(imagen_pil):  
    """Devuelve (ancho, alto, total_pixels) de una imagen PIL."""
    if imagen_pil is None:
        return None
    ancho, alto = imagen_pil.size
    return ancho, alto, ancho * alto


def consultar_pixel(imagen_pil, x, y):
    """Devuelve el valor del píxel (x, y)."""
    if not (0 <= x < imagen_pil.width and 0 <= y < imagen_pil.height):
        raise IndexError("Coordenadas fuera de la imagen.")
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
    color = 0 if img_chica.mode == "L" else tuple([0] * len(img_chica.getbands()))
    lienzo = Image.new(img_chica.mode, (ancho_meta, alto_meta), color=color)
    lienzo.paste(img_chica, (0, 0))
    return lienzo


def restar_imagenes(img1_pil, img2_pil, modo_ajuste="resize"):
    """Resta img2 a img1 evitando overflow y saturando a [0, 255]."""
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

            if img1_pil.size != (ancho_max, alto_max):
                img1_pil = igualar_dimensiones_padding(img1_pil, ancho_max, alto_max)
            if img2_pil.size != (ancho_max, alto_max):
                img2_pil = igualar_dimensiones_padding(img2_pil, ancho_max, alto_max)
        else:
            raise ValueError("modo_ajuste debe ser 'resize' o 'padding'.")

    if img1_pil.mode != img2_pil.mode:
        img2_pil = img2_pil.convert(img1_pil.mode)

    arr1 = np.asarray(img1_pil, dtype=np.float32)
    arr2 = np.asarray(img2_pil, dtype=np.float32)
    resultado = np.clip(arr1 - arr2, 0, 255).astype(np.uint8)
    return Image.fromarray(resultado)


def analizar_region(imagen_pil, region_box):
    """Devuelve la cantidad de píxeles y el promedio por canal en la región."""
    recorte = imagen_pil.crop(region_box)
    total_px = recorte.width * recorte.height
    stats = ImageStat.Stat(recorte)
    return total_px, stats.mean, recorte.mode

def _validar_porcentaje(porcentaje):
    if not 0 <= porcentaje <= 100:
        raise ValueError("El porcentaje debe estar entre 0 y 100.")


def _validar_tam_impar(tam):
    if not isinstance(tam, (int, np.integer)) or tam < 1 or tam % 2 == 0:
        raise ValueError("El tamaño de máscara debe ser un entero impar >= 1.")


def _pil_a_array(imagen_pil, dtype=np.float64):
    return np.asarray(imagen_pil, dtype=dtype)


def _array_a_pil(arr):
    return Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8))


def _aplicar_por_canal(arr, funcion_2d):
    """Aplica una función 2D a una imagen L o canal por canal en RGB/RGBA."""
    if arr.ndim == 2:
        return funcion_2d(arr)
    if arr.ndim == 3:
        canales = [funcion_2d(arr[..., c]) for c in range(arr.shape[2])]
        return np.stack(canales, axis=2)
    raise ValueError("Formato de imagen no soportado.")


# TP1 - 1. Transformación gamma

def transformacion_gamma(imagen, gamma):

    # Validamos la condición indicada en el TP:
    # 0 < gamma < 2 y gamma != 1
    if gamma <= 0 or gamma >= 2 or gamma == 1:
        raise ValueError(
            "Gamma debe cumplir: 0 < gamma < 2 y gamma != 1"
        )

    # Convertimos la imagen a float para poder realizar
    # operaciones con potencias sin perder precisión
    arr_imagen = np.array(
        imagen,
        dtype=np.float64
    )

    # Calculamos la constante c
    # c = 255 / (255^gamma)
    c = 255 / (255 ** gamma)

    # Aplicamos la transformación puntual:
    # T(r) = c * r^gamma
    for x in range(arr_imagen.shape[0]):
        for y in range(arr_imagen.shape[1]):

            r = arr_imagen[x, y]

            arr_imagen[x, y] = c * (r ** gamma)

    # Nos aseguramos de estar en el rango válido
    # de una imagen de 8 bits [0,255]
    arr_imagen = np.clip(
        arr_imagen,
        0,
        255
    ).astype(np.uint8)

    # Convertimos nuevamente a imagen PIL
    imagen_transformada = Image.fromarray(arr_imagen)

    return imagen_transformada

# 2. Negativo

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

# 3. Histograma

def obtener_histograma(imagen_pil):
    
    # Convertir a escala de grises
    img_gris = imagen_pil.convert("L")
    
    #Convertir a matriz
    arr_imagen = np.array(img_gris)
    
    total_pixeles = arr_imagen.size

    # Contar ocurrencias en cada nivel de gris
    valores, conteos = np.unique(
        arr_imagen, 
        return_counts=True
    )

    # Histograma normalizado con 256 niveles
    frecuencias_relativas = np.zeros(
        256, 
        dtype=np.float64
    
    )

    # Mapeamos los valores presentes a su frecuencia relativa
    frecuencias_relativas[valores] = (
        conteos / total_pixeles
    )

    return {
        nivel: frecuencia
        for nivel, frecuencia
        in enumerate(frecuencias_relativas)
    }


# 4. Umbralización

def binarizar_imagen(imagen_pil, umbral):

    # Validamos que el umbral esté dentro del rango
    # de niveles de gris de una imagen de 8 bits
    if umbral < 0 or umbral > 255:
        raise ValueError(
            "El umbral debe estar entre 0 y 255."
        )

    # Convertimos la imagen a escala de grises
    # para trabajar con un único valor por píxel
    img_gris = imagen_pil.convert("L")

    # Convertimos la imagen a matriz NumPy
    arr_imagen = np.array(img_gris)

    # Recorremos cada píxel
    for x in range(arr_imagen.shape[0]):
        for y in range(arr_imagen.shape[1]):

            nivel_gris = arr_imagen[x, y]

            # Aplicamos la función de umbral
            if nivel_gris >= umbral:
                arr_imagen[x, y] = 255
            else:
                arr_imagen[x, y] = 0

    # Convertimos nuevamente a imagen PIL
    return Image.fromarray(
        arr_imagen.astype(np.uint8)
    )

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

# 5 y 6. Ecualización

def aplicar_ecualizacion(imagen_pil):
    """
    Ecualización discreta del histograma usando la CDF.

    s_k = 255 * (CDF(k) - CDF_min)/(1 - CDF_min)
    """
    arr = np.asarray(imagen_pil.convert("L"), dtype=np.uint8)
    hist_abs = np.bincount(arr.ravel(), minlength=256)
    cdf = np.cumsum(hist_abs).astype(np.float64)

    no_cero = np.flatnonzero(hist_abs)
    if no_cero.size == 0:
        return Image.fromarray(arr.copy(), mode="L")

    cdf_min = cdf[no_cero[0]]
    total = cdf[-1]

    # Imagen constante: no hay rango tonal que expandir.
    if total == cdf_min:
        return Image.fromarray(arr.copy(), mode="L")

    lut = np.floor(255.0 * (cdf - cdf_min) / (total - cdf_min))
    lut = np.clip(lut, 0, 255).astype(np.uint8)

    return Image.fromarray(lut[arr], mode="L")

# 7. Generadores de números aleatorios

def graficar_distribucion(
    datos, titulo="Distribución de Ruido", xlabel="Valores", bins=50
):
    """Grafica el histograma normalizado de una muestra aleatoria."""
    plt.figure(figsize=(7, 4))
    plt.hist(datos, bins=bins, density=True)
    plt.title(titulo)
    plt.xlabel(xlabel)
    plt.ylabel("Densidad")
    plt.grid(True, linestyle="--", alpha=0.4)
    plt.tight_layout()
    plt.show()

def generar_datos_gauss(mu=0.0, sigma=1.0, cant=10000, graficar=False, **kwargs):
    """
    Genera N(mu, sigma).
    Se acepta el alias histórico graficar_distribucion=True para compatibilidad.
    """
    if "graficar_distribucion" in kwargs:
        graficar = bool(kwargs["graficar_distribucion"])
    if sigma <= 0:
        raise ValueError("sigma debe ser > 0.")
    if cant <= 0:
        raise ValueError("cant debe ser > 0.")

    datos = np.random.normal(loc=mu, scale=sigma, size=int(cant))
    if graficar:
        globals()["graficar_distribucion"](
            datos,
            titulo=f"Distribución Gaussiana (mu={mu}, sigma={sigma})",
            xlabel="Valores",
        )
    return datos

def generar_datos_exponencial(lambd, cant=10000, graficar=False, **kwargs):
    """
    Genera E(lambda) por transformada inversa:
    y = -ln(1-u)/lambda, u ~ U(0,1).
    """
    if "graficar_distribucion" in kwargs:
        graficar = bool(kwargs["graficar_distribucion"])
    if lambd <= 0:
        raise ValueError("lambda debe ser > 0.")
    if cant <= 0:
        raise ValueError("cant debe ser > 0.")

    u = np.random.uniform(0.0, 1.0, int(cant))
    # clip para evitar log(0) en el extremo numérico
    u = np.clip(u, 0.0, 1.0 - np.finfo(float).eps)
    datos = -np.log1p(-u) / lambd

    if graficar:
        globals()["graficar_distribucion"](
            datos,
            titulo=f"Distribución Exponencial (lambda={lambd})",
            xlabel="Valores",
        )
    return datos

# 8 y 9. Contaminación de ruido

def indices_pixeles(filas, columnas, porcentaje, rng=None):
    _validar_porcentaje(porcentaje)
    rng = np.random.default_rng() if rng is None else rng
    total = filas * columnas
    cantidad = int(round(total * porcentaje / 100.0))
    cantidad = min(max(cantidad, 0), total)
    if cantidad == 0:
        return np.array([], dtype=np.int64)
    return rng.choice(total, size=cantidad, replace=False)

def contaminar_ruido_gauss(imagen_pil, porcentaje, sigma):
    
    """
    1. d = porcentaje * total_pixeles.
    2. D = conjunto de d píxeles seleccionados aleatoriamente.
    3. Generar d valores aleatorios Gaussianos con μ=0 y σ.
    4. Para cada (i,j) ∈ D: IC(i,j) = I(i,j) + yk; si no, queda igual.
    """
    
    if porcentaje < 0 or porcentaje > 100:
        raise ValueError(
            "El porcentaje debe estar entre 0 y 100"
        )

    arr_imagen = np.array(imagen_pil, dtype=np.float64)
    

    if arr_imagen.ndim == 3:
        filas, columnas, canales = arr_imagen.shape
    else:
        filas, columnas = arr_imagen.shape
        canales = 1

    # Seleccionamos el conjunto D de píxeles a contaminar
    indices = indices_pixeles(
        filas,
        columnas,
        porcentaje
    )

    # Cantidad de valores de ruido que necesitamos generar
    cant_a_contaminar = len(indices)

    if cant_a_contaminar <= 0:
        return imagen_pil.copy()

    if canales > 1:

        # Reestructuramos la matriz:
        # (filas, columnas, canales)
        # a:
        # (cantidad_pixeles, canales)

        arr_plano = arr_imagen.reshape(-1, canales)

        for c in range(canales):

            datos_gauss = generar_datos_gauss(
                0,
                sigma,
                cant_a_contaminar
            )

            arr_plano[indices, c] += datos_gauss

    else:

        arr_plano = arr_imagen.ravel()

        datos_gauss = generar_datos_gauss(
            0,
            sigma,
            cant_a_contaminar
        )

        arr_plano[indices] += datos_gauss

def contaminar_ruido_exponencial(imagen_pil, porcentaje, lambd):
    
    #Validamos que el porcentaje este entre 0 y 100
    _validar_porcentaje(porcentaje)
    
    #Validamos que lambda sea positivo
    if lambd <=0:
        raise ValueError(
            "Lambda debe ser mayor que cero."
        )
        
    # Convertir a float64 para evitar desbordamientos en la multiplicación
    arr_imagen = np.array(imagen_pil, dtype=np.float64)

    # Detectar dimensiones y cantidad de canales
    if arr_imagen.ndim == 3:
        filas, columnas, canales = arr_imagen.shape
    else:
        filas, columnas = arr_imagen.shape
        canales = 1

    total_pixeles = filas * columnas
    cant_a_contaminar = round(total_pixeles * (porcentaje / 100.0))

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


# 10. Ventana deslizante y filtros espaciales

def aplicar_ventana_deslizante(imagen_pil, tam, funcion_filtro):
    """
    Aplica una ventana deslizante sobre la imagen.

    Parámetros:
    - imagen_pil: imagen de entrada
    - tam: tamaño de la ventana (debe ser impar)
    - funcion_filtro: función que recibe la ventana
                      y retorna el nuevo valor del píxel

    Ejemplo:
    ventana 3x3:

    [ a b c ]
    [ d e f ]
    [ g h i ]

    Se calcula un nuevo valor para el píxel central e.
    """

    _validar_tam_impar(tam)

    # Convertimos la imagen a escala de grises
    imagen_gris = imagen_pil.convert("L")

    arr_imagen = np.array(
        imagen_gris,
        dtype=np.float64
    )

    alto, ancho = arr_imagen.shape

    # Radio de la ventana
    radio = tam // 2

    # Padding para manejar bordes
    imagen_padding = np.pad(
        arr_imagen,
        radio,
        mode="edge"
    )

    resultado = np.zeros_like(arr_imagen)

    # Recorremos cada píxel
    for x in range(alto):
        for y in range(ancho):

            # Extraemos la vecindad
            ventana = imagen_padding[
                x:x+tam,
                y:y+tam
            ]

            # Aplicamos el filtro
            resultado[x, y] = funcion_filtro(
                ventana
            )

    return Image.fromarray(
        np.clip(resultado,0,255)
        .astype(np.uint8)
    )
#
# Filtro de media

def filtro_media(imagen_pil, tam=3):

    """
    Filtro de media:

    Nuevo píxel =
    promedio de los valores de la ventana
    """

    return aplicar_ventana_deslizante(
        imagen_pil,
        tam,
        lambda ventana: np.mean(ventana)
    )

# Filtro de mediana

def filtro_mediana(imagen_pil, tam=3):

    """
    Filtro de mediana:

    Ordena los valores de la ventana
    y toma el valor central.
    """

    return aplicar_ventana_deslizante(
        imagen_pil,
        tam,
        lambda ventana: np.median(ventana)
    )
    
# Filtro mediana Ponderada

def filtro_mediana_ponderada(imagen_pil, pesos=None):
    """
    Mediana ponderada.
    Por defecto usa la matriz del material:
        1 2 1
        2 4 2
        1 2 1
    """
    if pesos is None:
        pesos = np.array(
            [[1, 2, 1],
             [2, 4, 2],
             [1, 2, 1]],
            dtype=np.int32,
        )
    pesos = np.asarray(pesos)

    if pesos.ndim != 2 or pesos.shape[0] != pesos.shape[1]:
        raise ValueError("La matriz de pesos debe ser cuadrada.")
    if pesos.shape[0] % 2 == 0:
        raise ValueError("La matriz de pesos debe tener tamaño impar.")
    if np.any(pesos < 0) or not np.all(np.equal(pesos, np.floor(pesos))):
        raise ValueError("Los pesos deben ser enteros no negativos.")
    if pesos.sum() == 0:
        raise ValueError("La matriz de pesos no puede sumar 0.")

    pesos = pesos.astype(np.int32)
    tam = pesos.shape[0]

    def mediana_ponderada(ventana):
        repetidos = np.repeat(ventana.ravel(), pesos.ravel())
        return np.median(repetidos)

    return aplicar_ventana_deslizante(imagen_pil, tam, mediana_ponderada)

# Máscara Gaussiana

def crear_mascara_gaussiana(sigma=1, tam=3):
    """
    Genera una máscara Gaussiana 2D.

    Parámetros:
    - sigma: desviación estándar de la distribución Gaussiana.
    - tam: tamaño de la máscara (debe ser impar).

    La máscara se normaliza para que la suma de sus valores sea 1.
    """

    if sigma <= 0:
        raise ValueError(
            "Sigma debe ser mayor que cero."
        )

    if tam % 2 == 0 or tam < 1:
        raise ValueError(
            "El tamaño de la máscara debe ser impar."
        )

    # Centro de la máscara
    centro = tam // 2

    mascara = np.zeros(
        (tam, tam),
        dtype=np.float64
    )

    # Aplicamos la función Gaussiana:
    # G(x,y)=1/(2πσ²) * e^(-(x²+y²)/(2σ²))

    for x in range(tam):
        for y in range(tam):

            distancia_x = x - centro
            distancia_y = y - centro

            mascara[x, y] = np.exp(
                -(
                    distancia_x**2 +
                    distancia_y**2
                ) /
                (2 * sigma**2)
            )

    # Normalizamos para que la suma sea 1
    mascara = mascara / np.sum(mascara)

    return mascara
# Filtro Gaussiano

def filtro_gauss(imagen_pil, sigma=1, tam=3):

    mascara = crear_mascara_gaussiana(
        sigma,
        tam
    )

    return aplicar_ventana_deslizante(
        imagen_pil,
        tam,
        lambda ventana:
            np.sum(
                ventana * mascara
            )
    )

# Máscara de realce de bordes


def crear_mascara_realce():

    """
    Máscara Laplaciana:

    -1 -1 -1
    -1  8 -1
    -1 -1 -1

    La suma de los coeficientes es 0.
    """

    return np.array(
        [
            [-1,-1,-1],
            [-1, 8,-1],
            [-1,-1,-1]
        ],
        dtype=np.float64
    )

# Filtro realce de bordes

def filtro_realce_bordes(imagen_pil):

    mascara = crear_mascara_realce()

    resultado = aplicar_ventana_deslizante(
        imagen_pil,
        3,
        lambda ventana:
            np.sum(
                ventana * mascara
            )
    )

    return resultado

# TP1 - 11 y 12. Helpers de experimentación/comparación

def error_cuadratico_medio(img_a, img_b):
    """MSE entre dos imágenes del mismo tamaño/modo comparable."""
    a = np.asarray(img_a.convert("L"), dtype=np.float64)
    b = np.asarray(img_b.convert("L"), dtype=np.float64)
    if a.shape != b.shape:
        raise ValueError("Las imágenes deben tener las mismas dimensiones.")
    return float(np.mean((a - b) ** 2))


def experimento_ruido_filtro(
    imagen_pil,
    tipo_ruido,
    parametros_ruido,
    tipo_filtro,
    parametros_filtro=None,
):
    """
    Ejecuta Original -> Ruido -> Filtro y retorna imágenes + MSE.
    Útil para documentar los puntos 11 y 12 del TP1.
    """
    parametros_filtro = parametros_filtro or {}
    tipo_ruido = tipo_ruido.lower()
    tipo_filtro = tipo_filtro.lower()

    if tipo_ruido == "gaussiano":
        ruidosa = contaminar_ruido_gauss(imagen_pil, **parametros_ruido)
    elif tipo_ruido == "exponencial":
        ruidosa = contaminar_ruido_exponencial(imagen_pil, **parametros_ruido)
    elif tipo_ruido in ("sal_pimienta", "sal y pimienta"):
        ruidosa = contaminar_sal_pimienta(imagen_pil, **parametros_ruido)
    else:
        raise ValueError("Tipo de ruido no soportado.")

    filtros = {
        "media": filtro_media,
        "mediana": filtro_mediana,
        "gauss": filtro_gauss,
        "realce": filtro_realce_bordes,
    }
    if tipo_filtro not in filtros:
        raise ValueError("Tipo de filtro no soportado.")

    filtrada = filtros[tipo_filtro](ruidosa, **parametros_filtro)

    return {
        "original": imagen_pil.copy(),
        "ruidosa": ruidosa,
        "filtrada": filtrada,
        "mse_ruido": error_cuadratico_medio(imagen_pil, ruidosa),
        "mse_filtrada": error_cuadratico_medio(imagen_pil, filtrada),
    }

filtro_promedio = filtro_media