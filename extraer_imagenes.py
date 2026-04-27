import fitz  # PyMuPDF
import os

# 1. Crear una carpeta para guardar las imágenes si no existe
carpeta_img = 'paginas'
if not os.path.exists(carpeta_img):
    os.makedirs(carpeta_img)

# 2. Abrir el PDF
print("Abriendo el PDF para extraer imágenes...")
doc = fitz.open('catalogo.pdf')

# 3. Recorrer el PDF y convertir cada página
for num_pagina in range(len(doc)):
    pagina = doc.load_page(num_pagina)
    
    # Configuramos un 'zoom' para que la imagen salga en alta resolución
    # Matrix(2, 2) significa que duplicamos la calidad estándar para que se vea nítido en celulares
    matriz_alta_resolucion = fitz.Matrix(2, 2)
    pix = pagina.get_pixmap(matrix=matriz_alta_resolucion)
    
    # 4. Guardar la imagen (ejemplo: paginas/pagina_1.jpg)
    nombre_archivo = f"{carpeta_img}/pagina_{num_pagina + 1}.jpg"
    pix.save(nombre_archivo)
    print(f"Guardada: {nombre_archivo}")

print("-" * 30)
print(f"¡Listo! Se extrajeron {len(doc)} imágenes en la carpeta '{carpeta_img}'.")
