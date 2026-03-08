def preparar_resumen_contexto(detalles_zona: dict, sliders_usuario: dict) -> str:
    """
    Traduce los datos numéricos de la zona y las preferencias del usuario
    a un texto legible para que la IA entienda el contexto sin ruido.
    """
    
    # 1. ¿QUÉ HAY EN LA ZONA? (Filtramos ceros y ordenamos)
    # Convertimos {"Farmacias": 1.2, "Cines": 0} -> "Farmacias (Alta presencia)"
    items_presentes = []
    for k, v in detalles_zona.items():
        if v > 0.1: # Filtramos ruido
            intensidad = "presencia muy alta" if v > 2.0 else "presencia media" if v > 0.8 else "presencia baja"
            items_presentes.append(f"- {k}: {intensidad} ({v:.2f})")
            
    texto_zona = "\n".join(items_presentes) if items_presentes else "No se detectan servicios relevantes cerca."

    # 2. ¿QUÉ QUIERE EL USUARIO? (Solo lo importante)
    # Filtramos sliders que estén por encima de 3.5 (Interés alto)
    intereses = []
    for k, v in sliders_usuario.items():
        if v >= 3.5:
            intereses.append(f"- {k} (Prioridad ALTA)")
        elif v <= 1.5:
            intereses.append(f"- {k} (No le interesa)")
            
    texto_usuario = "\n".join(intereses) if intereses else "Perfil de usuario balanceado (sin preferencias extremas)."

    # 3. CONSTRUCCIÓN DEL PROMPT TÉCNICO
    return f"""
    CONTEXTO DE LA UBICACIÓN DETECTADA:
    {texto_zona}

    PREFERENCIAS DEL CIUDADANO:
    {texto_usuario}
    
    TAREA:
    Analiza si esta ubicación encaja con el ciudadano basándote en la correlación entre lo que hay y lo que busca.
    """