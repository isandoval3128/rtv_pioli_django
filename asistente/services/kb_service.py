"""
Servicio de Base de Conocimiento (KB).
Procesa documentos, genera palabras clave y busca fragmentos relevantes.
"""
import logging
import os
import re
from collections import Counter

from .intents import normalizar_texto

logger = logging.getLogger(__name__)

# Stopwords español (~80 palabras comunes)
STOPWORDS_ES = {
    'el', 'la', 'los', 'las', 'un', 'una', 'unos', 'unas', 'de', 'del', 'al',
    'en', 'con', 'por', 'para', 'sin', 'sobre', 'entre', 'hasta', 'desde',
    'que', 'es', 'se', 'no', 'si', 'su', 'sus', 'lo', 'le', 'les', 'me', 'te',
    'nos', 'ya', 'muy', 'mas', 'mas', 'pero', 'como', 'este', 'esta', 'estos',
    'estas', 'ese', 'esa', 'esos', 'esas', 'aquel', 'aquella', 'ser', 'estar',
    'haber', 'tener', 'hacer', 'poder', 'decir', 'ir', 'ver', 'dar', 'saber',
    'querer', 'llegar', 'hay', 'son', 'fue', 'han', 'tiene', 'puede', 'hace',
    'cada', 'todo', 'toda', 'todos', 'todas', 'otro', 'otra', 'otros', 'otras',
    'mismo', 'misma', 'donde', 'cuando', 'quien', 'cual', 'tambien', 'asi',
    'bien', 'solo', 'aqui', 'ahi', 'alla', 'entonces', 'despues', 'antes',
    'siempre', 'nunca', 'nada', 'algo', 'alguien', 'nadie', 'mucho', 'poco',
    'tanto', 'tan', 'cual', 'cuyo', 'cuya', 'porque', 'pues',
}


def procesar_documento(documento):
    """
    Procesa un documento: extrae texto del archivo (si hay) y genera palabras clave.
    Incluye el título del documento en la generación de keywords.
    """
    if documento.archivo:
        texto = _extraer_texto_archivo(documento.archivo)
        if texto:
            documento.contenido_texto = texto

    if documento.contenido_texto:
        # Incluir título en el texto para generar keywords más completas
        texto_para_keywords = f"{documento.titulo} {documento.contenido_texto}"
        documento.palabras_clave = generar_palabras_clave(texto_para_keywords)

    documento.save()


def _extraer_texto_archivo(archivo_field):
    """Extrae texto de un archivo según su extensión"""
    nombre = archivo_field.name.lower()
    ext = os.path.splitext(nombre)[1]

    try:
        if ext == '.pdf':
            return _extraer_texto_pdf(archivo_field)
        elif ext == '.docx':
            return _extraer_texto_docx(archivo_field)
        elif ext in ('.txt', '.md', '.csv'):
            archivo_field.seek(0)
            contenido = archivo_field.read()
            if isinstance(contenido, bytes):
                contenido = contenido.decode('utf-8', errors='ignore')
            return contenido
        else:
            logger.warning(f"Tipo de archivo no soportado: {ext}")
            return ''
    except Exception as e:
        logger.error(f"Error extrayendo texto de {nombre}: {e}")
        return ''


def _extraer_texto_pdf(archivo_field):
    """Extrae texto de un PDF usando PyPDF2"""
    from PyPDF2 import PdfReader

    archivo_field.seek(0)
    reader = PdfReader(archivo_field)
    textos = []
    for page in reader.pages:
        texto = page.extract_text()
        if texto:
            textos.append(texto)
    return '\n\n'.join(textos)


def _extraer_texto_docx(archivo_field):
    """Extrae texto de un archivo Word (.docx)"""
    from docx import Document

    archivo_field.seek(0)
    doc = Document(archivo_field)
    textos = []
    for para in doc.paragraphs:
        if para.text.strip():
            textos.append(para.text)
    return '\n'.join(textos)


def generar_palabras_clave(texto, max_keywords=50):
    """
    Genera lista de palabras clave relevantes a partir del texto.
    Incluye unigramas y bigramas frecuentes.
    """
    texto_limpio = normalizar_texto(texto)
    palabras = texto_limpio.split()

    # Filtrar stopwords y palabras muy cortas
    palabras_filtradas = [p for p in palabras if p not in STOPWORDS_ES and len(p) > 2]

    # Contar unigramas
    contador = Counter(palabras_filtradas)

    # Generar bigramas
    bigramas = []
    for i in range(len(palabras_filtradas) - 1):
        bigrama = f"{palabras_filtradas[i]} {palabras_filtradas[i+1]}"
        bigramas.append(bigrama)
    contador_bi = Counter(bigramas)

    # Combinar: unigramas que aparecen 2+ veces + bigramas que aparecen 2+ veces
    keywords = []

    # Top bigramas (más informativos)
    for bigrama, count in contador_bi.most_common(15):
        if count >= 2:
            keywords.append(bigrama)

    # Top unigramas
    for palabra, count in contador.most_common(max_keywords):
        if palabra not in keywords and count >= 2:
            keywords.append(palabra)
        if len(keywords) >= max_keywords:
            break

    # Si hay pocas keywords (documento corto), incluir todas las palabras únicas
    if len(keywords) < 10:
        for palabra in palabras_filtradas:
            if palabra not in keywords:
                keywords.append(palabra)
            if len(keywords) >= max_keywords:
                break

    return keywords


def buscar_en_kb(consulta, max_resultados=3):
    """
    Busca documentos relevantes en la KB para una consulta del cliente.
    Retorna lista de dicts: [{'titulo': str, 'texto': str, 'doc_id': int}, ...]
    """
    from asistente.models import DocumentoKB

    documentos = DocumentoKB.objects.filter(activo=True)
    if not documentos.exists():
        return []

    consulta_norm = normalizar_texto(consulta)
    palabras_consulta = [
        p for p in consulta_norm.split()
        if p not in STOPWORDS_ES and len(p) > 2
    ]

    if not palabras_consulta:
        return []

    resultados = []

    for doc in documentos:
        score = 0

        # Scoring por keywords del documento
        keywords_doc = [normalizar_texto(kw) for kw in (doc.palabras_clave or [])]
        for palabra in palabras_consulta:
            for kw in keywords_doc:
                if palabra in kw or kw in palabra:
                    score += 2
                    break

        # Scoring por título del documento
        titulo_norm = normalizar_texto(doc.titulo) if doc.titulo else ''
        for palabra in palabras_consulta:
            if palabra in titulo_norm:
                score += 2

        # Scoring por contenido (búsqueda en texto completo)
        contenido_norm = normalizar_texto(doc.contenido_texto) if doc.contenido_texto else ''
        for palabra in palabras_consulta:
            if palabra in contenido_norm:
                score += 1

        if score >= 2:  # Umbral mínimo de relevancia
            fragmento = extraer_fragmento_relevante(
                doc.contenido_texto, palabras_consulta
            )
            if fragmento:
                resultados.append({
                    'titulo': doc.titulo,
                    'texto': fragmento,
                    'doc_id': doc.pk,
                    'score': score,
                })

    # Ordenar por score y tomar los mejores
    resultados.sort(key=lambda x: x['score'], reverse=True)
    resultados = resultados[:max_resultados]

    # Incrementar veces_usado
    if resultados:
        from django.db.models import F
        doc_ids = [r['doc_id'] for r in resultados]
        DocumentoKB.objects.filter(pk__in=doc_ids).update(
            veces_usado=F('veces_usado') + 1
        )

    return resultados


def extraer_fragmento_relevante(texto_completo, palabras_consulta, max_chars=800):
    """
    Extrae el fragmento más relevante del documento para la consulta.
    Divide en párrafos y retorna el más relevante.
    """
    if not texto_completo:
        return ''

    # Dividir en párrafos (por doble salto de línea o por líneas individuales)
    parrafos = re.split(r'\n\s*\n|\n', texto_completo)
    parrafos = [p.strip() for p in parrafos if p.strip() and len(p.strip()) > 20]

    if not parrafos:
        return texto_completo[:max_chars]

    # Puntuar cada párrafo por densidad de keywords
    mejores = []
    for parrafo in parrafos:
        parrafo_norm = normalizar_texto(parrafo)
        score = 0
        for palabra in palabras_consulta:
            if palabra in parrafo_norm:
                score += parrafo_norm.count(palabra)
        if score > 0:
            mejores.append((score, parrafo))

    if not mejores:
        # Si ningún párrafo tiene match directo, tomar el primero
        return parrafos[0][:max_chars]

    # Ordenar por score descendente
    mejores.sort(key=lambda x: x[0], reverse=True)

    # Combinar los mejores párrafos hasta llenar max_chars
    fragmento = ''
    for _, parrafo in mejores:
        if len(fragmento) + len(parrafo) + 2 <= max_chars:
            fragmento += parrafo + '\n\n'
        else:
            # Agregar lo que se pueda del siguiente párrafo
            espacio = max_chars - len(fragmento)
            if espacio > 50:
                fragmento += parrafo[:espacio] + '...'
            break

    return fragmento.strip()
