import pandas as pd
import fitz  # PyMuPDF
import json
import re

def limpiar_precio_sucio(valor):
    if pd.isna(valor) or valor == "": return ""
    valor_str = str(valor).strip()

    # Si Python lo lee con .0 al final por error, lo limpiamos
    if valor_str.endswith('.0'):
        valor_str = valor_str[:-2]

    # Si trae puntos de origen (ej "5.346.447"), se los quitamos para procesarlo puro
    if '.' in valor_str:
        valor_str = valor_str.replace('.', '')

    # A este punto, tenemos un número puro (ej "5346447" o "5588000")
    if len(valor_str) >= 3:
        # REGLA 1: Eliminamos el último dígito de la derecha
        valor_truncado = valor_str[:-1]

        # REGLA 2: Separamos los enteros y los dos últimos serán los decimales
        enteros = valor_truncado[:-2]
        decimales = valor_truncado[-2:]

        # Le damos formato de miles con puntos y coma para decimales
        try:
            if enteros == "": enteros = "0"
            enteros_fmt = f"{int(enteros):,}".replace(',', '.')
            return f"{enteros_fmt},{decimales}"
        except ValueError:
            return f"{enteros},{decimales}"

    return valor_str

def formatear_promo_limpia(valor):
    if pd.isna(valor) or valor == "": return ""
    try:
        numero = float(valor)
        return f"{numero:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')
    except: return str(valor).strip()

def normalizar_codigo(texto):
    return re.sub(r'[^A-Z0-9]', '', str(texto).upper())

print("Cargando base de datos...")
df = pd.read_excel('precios.xlsx', dtype={'Codigo de Producto': str})
doc = fitz.open('catalogo.pdf')
resultados = []
codigos_encontrados = set()

print(f"Procesando {len(doc)} páginas con la regla estricta de COD y formateo de precios...")

for num_pagina in range(len(doc)):
    pagina = doc.load_page(num_pagina)
    palabras = pagina.get_text("words") 
    
    tags_pagina = []
    
    for index, row in df.iterrows():
        precio_raw = str(row['Precio']).strip()
        if not precio_raw or precio_raw in ["0", "0.0", "0,00"]: continue
            
        codigo_excel = normalizar_codigo(row['Codigo de Producto'])
        if not codigo_excel: continue
        
        for i, p in enumerate(palabras):
            texto_pdf_original = p[4]
            texto_pdf_limpio = normalizar_codigo(texto_pdf_original)
            texto_sin_cod = texto_pdf_limpio.replace("COD", "")
            
            if codigo_excel == texto_pdf_limpio or codigo_excel == texto_sin_cod:
                
                # --- LA REGLA ESTRICTA DE "COD" ---
                contexto = texto_pdf_original.upper()
                if i > 0: contexto += palabras[i-1][4].upper()
                if i > 1: contexto += palabras[i-2][4].upper()
                
                if "COD" not in contexto and "CÓD" not in contexto:
                    continue 

                item = {
                    "pagina": num_pagina + 1,
                    "codigo": row['Codigo de Producto'],
                    "precio_normal": limpiar_precio_sucio(row['Precio']),
                    "precio_promo": formatear_promo_limpia(row['Precio Promo']),
                    "x": round((p[0] / pagina.rect.width) * 100, 2),
                    "y": round((p[1] / pagina.rect.height) * 100, 2)
                }
                tags_pagina.append(item)
                codigos_encontrados.add(row['Codigo de Producto'])

    filtrados = []
    for nt in tags_pagina:
        es_duplicado = False
        for ft in filtrados:
            if abs(nt['x'] - ft['x']) < 7 and abs(nt['y'] - ft['y']) < 5:
                es_duplicado = True
                if nt['precio_promo'] and not ft['precio_promo']:
                    ft.update(nt) 
                break
        if not es_duplicado: filtrados.append(nt)
    
    resultados.extend(filtrados)

with open('datos.json', 'w', encoding='utf-8') as f:
    json.dump(resultados, f, indent=4, ensure_ascii=False)

print("-" * 30)
print(f"¡Hecho! Se procesaron {len(codigos_encontrados)} productos.")
