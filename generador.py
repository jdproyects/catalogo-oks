import pandas as pd
import fitz  # PyMuPDF
import json
import re

def limpiar_precio_sucio(valor):
    if pd.isna(valor) or valor == "": return ""
    v = str(valor).strip()
    
    # Quitamos el .0 si Python lo lee como decimal
    if v.endswith('.0'): v = v[:-2]
    
    # Limpiamos cualquier punto o coma accidental que venga del Excel
    v = v.replace('.', '').replace(',', '')
    
    # Aquí hacemos la MAGIA MATEMÁTICA con el número puro (ej: "5076417")
    if len(v) >= 3:
        v = v[:-1] # REGLA 1: Quitamos el último dígito -> queda "507641"
        
        enteros = v[:-2] # Todo menos los últimos dos -> "5076"
        decimales = v[-2:] # Los últimos dos -> "41"
        
        if enteros == "": enteros = "0"
        
        # REGLA 2: Le ponemos el punto de miles a los enteros
        enteros_fmt = f"{int(enteros):,}".replace(',', '.') # Queda "5.076"
        
        # Unimos todo con la coma
        return f"{enteros_fmt},{decimales}" # Resultado: "5.076,41"
        
    return v

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

print(f"Procesando {len(doc)} páginas...")

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
