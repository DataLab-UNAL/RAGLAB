# RAG-LAB | Fundamentos para crear chatbots inteligentes

Repositorio de materiales del curso **Diseño de agentes de I.A. RAG-LAB**. Actualmente incluye la guía de bienvenida y los recursos del primer módulo, que prepara a los estudiantes para trabajar con Python y avanzar hacia un prototipo de chatbot basado en RAG.

## Contenido del repositorio

- [`docs/index.html`](docs/index.html): bienvenida, objetivos y recorrido general del curso.
- [`docs/modulo-01.html`](docs/modulo-01.html): guía interactiva del módulo 1, con instrucciones, capturas y soporte.
- [`modulo-01/README.md`](modulo-01/README.md): objetivos, secuencia de trabajo y ejercicios del módulo.
- [`modulo-01/ejercicios/`](modulo-01/ejercicios/): scripts de práctica de Python.
- [`RAGLAB.yml`](RAGLAB.yml): definición del entorno de Conda para el curso.

## Módulo 1: fundamentos técnicos

El módulo introduce las herramientas y prácticas que se utilizarán durante el curso:

- Python y ejecución de scripts desde PyCharm o la terminal.
- Git y GitHub para registrar y compartir cambios.
- Fork y clonación del repositorio para el trabajo individual.
- Miniconda y el entorno `RAGLAB` para instalar dependencias.
- Kiro CLI y el plugin **Kiro with GUI** para PyCharm, con revisión y validación de los cambios propuestos.

Consulta la [guía del módulo](docs/modulo-01.html) para seguir la ruta paso a paso.

## Preparación del entorno

Desde la carpeta raíz del repositorio, crea y activa el entorno:

```bash
conda env create -f RAGLAB.yml
conda activate RAGLAB
```

Los ejercicios y las instrucciones completas están en [`modulo-01/README.md`](modulo-01/README.md) y en la guía interactiva.
