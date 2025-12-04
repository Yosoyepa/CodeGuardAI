def complex_logic_example(x, y, z):
    """
    Esta función está diseñada intencionalmente para tener baja calidad:
    1. Alta complejidad ciclomática (muchos if/else anidados).
    2. Función demasiado larga.
    3. Código duplicado.
    """
    result = 0

    # 1. Alta Complejidad Ciclomática
    if x > 0:
        if y > 0:
            if z > 0:
                result = x + y + z
                if result > 100:
                    print("Big number")
                else:
                    print("Small number")
            else:
                result = x + y - z
        else:
            if z > 0:
                result = x - y + z
            else:
                result = x - y - z
    else:
        if y > 0:
            result = -x + y
        else:
            result = -x - y

    # 2. Código Duplicado (Bloque A)
    print("Calculando métricas complejas...")
    val1 = x * 2
    val2 = y * 3
    total = val1 + val2
    if total > 10:
        print("Total es mayor a 10")
    else:
        print("Total es menor o igual a 10")

    # Relleno para hacer la función larga (> 25 líneas suele ser warning)
    a = 1
    b = 2
    c = 3
    d = 4
    e = 5
    f = 6
    g = 7
    h = 8
    i = 9
    j = 10

    # 2. Código Duplicado (Bloque A - Copia Exacta)
    print("Calculando métricas complejas...")
    val1 = x * 2
    val2 = y * 3
    total = val1 + val2
    if total > 10:
        print("Total es mayor a 10")
    else:
        print("Total es menor o igual a 10")

    return result
