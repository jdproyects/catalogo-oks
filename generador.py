import pandas as pd
import fitz  # PyMuPDF
import json

def limpiar_precio_sucio(valor):
    if pd.isna(valor) or valor == "":
        return ""
    valor_str = str(valor).strip()
    if valor_str.endswith('.0'):
        valor_str = valor_str[:-2]
    if '.' in valor_str:
        partes = valor_str.rsplit('.', 1) 
        enteros = partes[0]
        decimales = partes[1][:2] 
        return f"{enteros},{decimales}"
    elif len(valor_str) >= 3:
        valor_truncado = valor_str[:-1] 
        enteros = valor_truncado[:-2]
        decimales = valor_truncado[-2:]
        try:
            enteros_fmt = f"{int(enteros):,}".replace(',', '.')
            return f"{enteros_fmt},{decimales}"
        except ValueError:
            return f"{enteros},{decimales}"
    return valor_str

def formatear_promo_limpia(valor):
    if pd.isna(valor) or valor == "":
        return ""
    try:
        numero = float(valor)
        return f"{numero:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')
    except:
        return str(valor).strip()

# 1. Cargar Excel
print("Cargando base de datos...")
df = pd.read_excel('precios.xlsx', dtype={'Codigo de Producto': str})

# 2. Abrir PDF
doc = fitz.open('catalogo.pdf')
resultados = []
codigos_encontrados = set()

# 3. Procesar
print("Escaneando páginas con filtro inteligente y anti-superposición...")
for num_pagina in range(len(doc)):
    pagina = doc.load_page(num_pagina)
    palabras = pagina.get_text("words") 
    
    tags_pagina = [] # GUARDAMOS LOS PRECIOS DE ESTA PÁGINA AQUÍ PRIMERO
    
    for index, row in df.iterrows():
        try:
            precio_valor = float(row['Precio'])
        except:
            precio_valor = 0
            
        if precio_valor <= 1:
            continue
            
        codigo = str(row['Codigo de Producto']).strip().upper()
        
        for palabra in palabras:
            texto_limpio = palabra[4].strip('.,;:') 
            texto_comparar = texto_limpio.upper().replace('COD.', '').replace('COD', '').strip('.:,;- ')
            
            if texto_limpio.upper() == codigo or texto_comparar == codigo:
                precio_normal = limpiar_precio_sucio(row['Precio'])
                precio_promo = formatear_promo_limpia(row['Precio Promo'])
                tiene_promo = not pd.isna(row['Precio Promo'])
                
                ancho = pagina.rect.width
                alto = pagina.rect.height
                
                item = {
                    "pagina": num_pagina + 1,
                    "codigo": codigo,
                    "precio_normal": precio_normal,
                    "precio_promo": precio_promo if tiene_promo else "",
                    "x": round((palabra[0] / ancho) * 100, 2),
                    "y": round((palabra[1] / alto) * 100, 2)
                }
                tags_pagina.append(item)
                codigos_encontrados.add(codigo)
                
    # --- MAGIA ANTI-SUPERPOSICIÓN ---
    tags_filtrados = []
    for nuevo_tag in tags_pagina:
        colision = False
        for i, tag_existente in enumerate(tags_filtrados):
            # Medimos qué tan cerca están en la hoja (en porcentaje)
            dist_x = abs(nuevo_tag['x'] - tag_existente['x'])
            dist_y = abs(nuevo_tag['y'] - tag_existente['y'])
            
            # Si están a menos de 8% de distancia horizontal y 6% vertical, son del mismo producto
            if dist_x < 8 and dist_y < 6:
                colision = True
                # PRIORIDAD: Si el nuevo tiene promo y el viejo no, lo pisamos y nos quedamos con el de Promo
                if nuevo_tag['precio_promo'] != "" and tag_existente['precio_promo'] == "":
                    tags_filtrados[i] = nuevo_tag
                break # Dejamos de buscar porque ya colisionó con uno
                
        if not colision:
            tags_filtrados.append(nuevo_tag)
            
    # Ahora sí, agregamos los tags limpios y sin repetir a la lista final
    resultados.extend(tags_filtrados)

# 4. Guardar
with open('datos.json', 'w', encoding='utf-8') as f:
    json.dump(resultados, f, indent=4, ensure_ascii=False)

print("-" * 30)
print(f"¡Listo! Se indexaron {len(codigos_encontrados)} códigos y se eliminaron duplicados.")
