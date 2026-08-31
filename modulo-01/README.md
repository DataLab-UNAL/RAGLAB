# Módulo 1 - Fundamentos Técnicos

Este módulo prepara a los estudiantes para el resto del curso y está pensado para dos sesiones de 4 horas.

## Objetivo

Al finalizar, el estudiante debe poder:

- Instalar Miniconda, Git y PyCharm.
- Crear y usar una cuenta de GitHub.
- Hacer un fork del repositorio del curso.
- Clonar su fork y subir cambios.
- Crear el entorno `RAGLAB` desde `RAGLAB.yml`.
- Ejecutar scripts simples en Python.

## Estructura

- `ejercicios/01_hola_python.py`: primer script.
- `ejercicios/02_variables_y_tipos.py`: variables y tipos básicos.
- `ejercicios/03_condicionales_y_bucles.py`: decisiones y repeticiones.
- `ejercicios/04_funciones.py`: funciones simples.

## Flujo principal del curso

```bash
conda env create -f ../RAGLAB.yml
conda activate RAGLAB
```

Luego:

```bash
python ejercicios/01_hola_python.py
python ejercicios/02_variables_y_tipos.py
python ejercicios/03_condicionales_y_bucles.py
python ejercicios/04_funciones.py
```

## Contenidos sugeridos por sesión

### Sesión 1

- Instalación de Miniconda, Git y PyCharm.
- Creación de cuenta en GitHub.
- Explicación del concepto de fork.
- Clonado del repositorio.
- Primer commit y primer push.

### Sesión 2

- Creación del entorno `RAGLAB`.
- Activación del entorno y validación.
- Apertura del proyecto en PyCharm.
- Python básico.
- Práctica integradora con cambios versionados.
