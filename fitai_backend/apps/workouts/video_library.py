# ============================================================
# 🎥 BIBLIOTECA DE VÍDEOS - PALAVRAS-CHAVE
# ============================================================
# Quando a IA criar exercício novo, buscar vídeo aqui

VIDEO_KEYWORDS = {
    # PEITO
    'flexao': 'https://youtube.com/watch?v=IODxDxX7oi4',
    'flexoes': 'https://youtube.com/watch?v=IODxDxX7oi4',
    'push up': 'https://youtube.com/watch?v=IODxDxX7oi4',
    'supino': 'https://youtube.com/watch?v=rT7DgCr-3pg',
    'crucifixo': 'https://youtube.com/watch?v=eozdVDA78K0',
    'peck deck': 'https://youtube.com/watch?v=Z71vBam6a1I',
    
    # COSTAS
    'remada': 'https://youtube.com/watch?v=GZbfZ033f74',
    'puxada': 'https://youtube.com/watch?v=CAwf7n6Luuc',
    'pulldown': 'https://youtube.com/watch?v=CAwf7n6Luuc',
    'barra fixa': 'https://youtube.com/watch?v=eGo4IYlbE5g',
    'pull up': 'https://youtube.com/watch?v=eGo4IYlbE5g',
    'levantamento terra': 'https://youtube.com/watch?v=op9kVnSso6Q',
    'deadlift': 'https://youtube.com/watch?v=op9kVnSso6Q',
    
    # PERNAS
    'agachamento': 'https://youtube.com/watch?v=aClxtDcdpsQ',
    'squat': 'https://youtube.com/watch?v=aClxtDcdpsQ',
    'leg press': 'https://youtube.com/watch?v=IZxyjW7MPJQ',
    'extensora': 'https://youtube.com/watch?v=YyvSfVjQeL0',
    'flexora': 'https://youtube.com/watch?v=1Tq3QdYUuHs',
    'afundo': 'https://youtube.com/watch?v=QOVaHwm-Q6U',
    'lunge': 'https://youtube.com/watch?v=QOVaHwm-Q6U',
    'stiff': 'https://youtube.com/watch?v=1uDiW5--rAE',
    'panturrilha': 'https://youtube.com/watch?v=JLbra33PE-o',
    'calf raise': 'https://youtube.com/watch?v=JLbra33PE-o',
    
    # OMBROS
    'desenvolvimento': 'https://youtube.com/watch?v=qEwKCR5JCog',
    'shoulder press': 'https://youtube.com/watch?v=qEwKCR5JCog',
    'elevacao lateral': 'https://youtube.com/watch?v=3VcKaXpzqRo',
    'lateral raise': 'https://youtube.com/watch?v=3VcKaXpzqRo',
    'elevacao frontal': 'https://youtube.com/watch?v=9gfirDFXBi8',
    'front raise': 'https://youtube.com/watch?v=9gfirDFXBi8',
    
    # BÍCEPS
    'rosca': 'https://youtube.com/watch?v=ykJmrZ5v0Oo',
    'curl': 'https://youtube.com/watch?v=ykJmrZ5v0Oo',
    'rosca direta': 'https://youtube.com/watch?v=ykJmrZ5v0Oo',
    'rosca alternada': 'https://youtube.com/watch?v=sAq_ocpRh_I',
    'rosca martelo': 'https://youtube.com/watch?v=zC3nLlEvin4',
    'hammer curl': 'https://youtube.com/watch?v=zC3nLlEvin4',
    
    # TRÍCEPS
    'triceps': 'https://youtube.com/watch?v=d_KZxkY_0cM',
    'tricep': 'https://youtube.com/watch?v=d_KZxkY_0cM',
    'testa': 'https://youtube.com/watch?v=d_KZxkY_0cM',
    'corda': 'https://youtube.com/watch?v=2-LAMcpzODU',
    'mergulho': 'https://youtube.com/watch?v=6kALZikXxLc',
    'dips': 'https://youtube.com/watch?v=6kALZikXxLc',
    
    # ABDÔMEN
    'abdominal': 'https://youtube.com/watch?v=1fbU_MkV7NE',
    'crunch': 'https://youtube.com/watch?v=1fbU_MkV7NE',
    'prancha': 'https://youtube.com/watch?v=pSHjTRCQxIw',
    'plank': 'https://youtube.com/watch?v=pSHjTRCQxIw',
    'bicicleta': 'https://youtube.com/watch?v=9FGilxCbdz8',
    
    # CARDIO
    'corrida': 'https://youtube.com/watch?v=brFHyOtTwH4',
    'burpee': 'https://youtube.com/watch?v=dZgVxmf6jkA',
    'jumping jack': 'https://youtube.com/watch?v=iSSAk4XCsRA',
    'polichinelo': 'https://youtube.com/watch?v=iSSAk4XCsRA',
    'mountain climber': 'https://youtube.com/watch?v=nmwgirgXLYM',
    'escalador': 'https://youtube.com/watch?v=nmwgirgXLYM',
}

# Vídeos padrão por grupo muscular (fallback)
DEFAULT_VIDEOS = {
    'chest': 'https://youtube.com/watch?v=IODxDxX7oi4',
    'back': 'https://youtube.com/watch?v=GZbfZ033f74',
    'legs': 'https://youtube.com/watch?v=aClxtDcdpsQ',
    'shoulders': 'https://youtube.com/watch?v=qEwKCR5JCog',
    'arms': 'https://youtube.com/watch?v=ykJmrZ5v0Oo',
    'abs': 'https://youtube.com/watch?v=1fbU_MkV7NE',
    'cardio': 'https://youtube.com/watch?v=dZgVxmf6jkA',
    'full_body': 'https://youtube.com/watch?v=IODxDxX7oi4',
}


def find_video_for_exercise(exercise_name, muscle_group=None):
    """
    🎥 Busca vídeo para exercício NOVO criado pela IA
    
    Estratégia:
    1. Busca palavra-chave no nome
    2. Fallback por grupo muscular
    3. Fallback geral
    
    Args:
        exercise_name: "Flexão de Braço Inclinada"
        muscle_group: "chest"
    
    Returns:
        str: URL do vídeo
    """
    if not exercise_name:
        return _get_fallback_video(muscle_group)
    
    # Normalizar nome
    name_lower = exercise_name.lower().strip()
    
    # Remover acentos
    replacements = {
        'á': 'a', 'ã': 'a', 'â': 'a',
        'é': 'e', 'ê': 'e',
        'í': 'i',
        'ó': 'o', 'ô': 'o', 'õ': 'o',
        'ú': 'u',
        'ç': 'c'
    }
    for old, new in replacements.items():
        name_lower = name_lower.replace(old, new)
    
    # 🔍 Buscar palavra-chave
    for keyword, video_url in VIDEO_KEYWORDS.items():
        if keyword in name_lower:
            print(f"   ✅ Vídeo encontrado: '{exercise_name}' → keyword '{keyword}'")
            return video_url
    
    # ⚠️ Não encontrou, usar fallback
    print(f"   ⚠️ Vídeo não encontrado: '{exercise_name}' → usando fallback")
    return _get_fallback_video(muscle_group)


def _get_fallback_video(muscle_group):
    """Retorna vídeo padrão por grupo muscular"""
    if muscle_group and muscle_group in DEFAULT_VIDEOS:
        return DEFAULT_VIDEOS[muscle_group]
    return DEFAULT_VIDEOS['full_body']