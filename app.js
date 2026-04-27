// Configuración: Coloca aquí la cantidad exacta de páginas de tu PDF
const TOTAL_PAGINAS = 60; 

document.addEventListener('DOMContentLoaded', async function() {
    const flipbook = document.getElementById('flipbook');

    // 1. Crear las páginas del libro vacías con su imagen
    for (let i = 1; i <= TOTAL_PAGINAS; i++) {
        const divPage = document.createElement('div');
        divPage.className = 'page';
        divPage.id = `pagina-${i}`;
        
        const img = document.createElement('img');
        img.src = `paginas/pagina_${i}.jpg`;
        
        divPage.appendChild(img);
        flipbook.appendChild(divPage);
    }

    // 2. Cargar el JSON de precios
    try {
        const response = await fetch('datos.json');
        const datosPrecios = await response.json();

        // 3. Colocar cada precio en su página
        datosPrecios.forEach(item => {
            const paginaDestino = document.getElementById(`pagina-${item.pagina}`);
            
            if (paginaDestino) {
                const etiqueta = document.createElement('div');
                etiqueta.className = 'etiqueta-precio';
                
                // NOTA: Multiplicamos por un factor de escala. 
                // PyMuPDF usa puntos (aprox 1.33 px). Ajustaremos esto si quedan desfasados.
                etiqueta.style.left = `${item.x}%`;
                etiqueta.style.top = `${item.y}%`;

                let htmlPrecio = '';
                
                // Lógica que me pediste: Mostrar promo resaltada si existe
                if (item.precio_promo && item.precio_promo.trim() !== "") {
                    htmlPrecio += `<span class="precio-normal tachado">$${item.precio_normal}</span>`;
                    htmlPrecio += `<span class="precio-promo">$${item.precio_promo}</span>`;
                } else {
                    htmlPrecio += `<span class="precio-normal">$${item.precio_normal}</span>`;
                }

                etiqueta.innerHTML = htmlPrecio;
                paginaDestino.appendChild(etiqueta);
            }
        });

    } catch (error) {
        console.error("Error cargando los precios:", error);
    }

    // 4. Inicializar el efecto de Flipbook
    const pageFlip = new St.PageFlip(flipbook, {
        width: 500, // Ancho de una sola página
        height: 700, // Alto de una sola página
        showCover: true,
        useMouseEvents: true
    });

    pageFlip.loadFromHTML(document.querySelectorAll('.page'));
});
