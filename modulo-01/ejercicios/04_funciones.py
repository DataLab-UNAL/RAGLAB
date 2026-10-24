def saludar_estudiante(nombre):
    return f"Bienvenido, {nombre}. Ya estás listo para construir proyectos en Python."


def calcular_total(sesiones, horas_por_sesion):
    return sesiones * horas_por_sesion


nombre_estudiante = "juan jose"

print(saludar_estudiante(nombre_estudiante))
print("Horas del módulo:", calcular_total(2, 4))
