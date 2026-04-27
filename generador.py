import pandas as pd
import fitz  # PyMuPDF
import json
import re

def limpiar_precio_sucio(valor):
    if pd.isna(valor) or valor == "": return ""
    valor_str = str(valor).strip()
    if valor_str.endswith('.0'): valor_str = valor_str[:-2]
    if '.' in valor_str:
        partes = valor_str.rsplit('.', 1)
        return f"{partes[0]},{partes[1][:2]}"
    elif len(valor_str) >= 3:
        enteros = valor_str[:-2]
        decimales = valor_str[-2:]
        return f"{enteros},{decimales}"
    return valor_str

def formatear_promo_limpia(valor):
    if pd.isna(valor) or valor == "": return ""
    try:
        numero = float(valor)
        return f"{numero:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')
    except: return str(valor).strip()

def normalizar_codigo(texto):
    """Elimina todo lo que no sea letras o números para comparar mejor"""
    return re.sub(r'[^A-Z0-9]', '', str(texto).upper())

# 1. Cargar Excel
print("Cargando base de datos...")
df = pd.read_excel('precios.xlsx', dtype={'Codigo de Producto': str})

# 2. Abrir PDF
doc = fitz.open('catalogo.pdf')
resultados = []
codigos_encontrados = set()

print(f"Procesando {len(doc)} páginas...")

for num_pagina in range(len(doc)):
    pagina = doc.load_page(num_pagina)
    palabras = pagina.get_text("words") # [x0, y0, x1, y1, "texto", block_no, line_no, word_no]
    
    tags_pagina = []
    
    for index, row in df.iterrows():
        try:
            if float(row['Precio']) <= 1: continue
        except: continue
            
        codigo_excel = normalizar_codigo(row['Codigo de Producto'])
        
        for i, p in enumerate(palabras):
            texto_pdf_original = p[4]
            texto_pdf_limpio = normalizar_codigo(texto_pdf_original)
            
            # Si el texto del PDF contiene el código del Excel (ej: "COD.851" contiene "851")
            if codigo_excel in texto_pdf_limpio:
                
                # REGLA DE SEGURIDAD PARA NÚMEROS CORTOS
                if len(codigo_excel) <= 4:
                    # Buscamos "COD" en la misma palabra o en las 2 anteriores
                    contexto = texto_pdf_original.upper()
                    if i > 0: contexto += palabras[i-1][4].upper()
                    if i > 1: contexto += palabras[i-2][4].upper()
                    
                    if "COD" not in contexto and "CÓD" not in contexto:
                        continue # Es un gramaje o cantidad, lo ignoramos

                # Si pasó el filtro, guardamos
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

    # Anti-superposición
    filtrados = []
    for nt in tags_pagina:
        es_duplicado = False
        for ft in filtrados:
            if abs(nt['x'] - ft['x']) < 7 and abs(nt['y'] - ft['y']) < 5:
                es_duplicado = True
                if nt['precio_promo'] and not ft['precio_promo']:
                    ft.update(nt) # Preferir el que tiene promo
                break
        if not es_duplicado: filtrados.append(nt)
    
    resultados.extend(filtrados)

# 4. Guardar
with open('datos.json', 'w', encoding='utf-8') as f:
    json.dump(resultados, f, indent=4, ensure_ascii=False)

print("-" * 30)
print(f"¡Hecho! {len(codigos_encontrados)} productos indexados en {len(doc)} páginas.")
