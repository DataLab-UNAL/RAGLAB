# Módulo 1 | Fundamentos técnicos

Este módulo prepara al grupo para el resto del curso mediante una introducción práctica a Git, GitHub, Miniconda, PyCharm y Python. La duración sugerida es de **dos sesiones de cuatro horas**.

## Resultados de aprendizaje

Al finalizar el módulo, cada estudiante podrá:

- Crear una cuenta de GitHub, configurar Git y crear un fork del repositorio del curso.
- Clonar su fork y trabajar con la rama `DEV` desde PyCharm.
- Crear y activar el entorno Conda `RAGLAB` definido en `RAGLAB.yml`.
- Ejecutar y modificar scripts introductorios de Python.
- Plantear un cambio acotado a Kiro, revisar el código propuesto y validar su comportamiento.
- Crear un commit y subir a GitHub un cambio que comprenda y haya comprobado.

## Ejercicios

| Archivo | Tema |
| --- | --- |
| `ejercicios/01_hola_python.py` | Primer programa en Python |
| `ejercicios/02_variables_y_tipos.py` | Variables y tipos de datos |
| `ejercicios/03_condicionales_y_bucles.py` | Condiciones y repeticiones |
| `ejercicios/04_funciones.py` | Funciones y parámetros |

## Preparar y activar el entorno

Ejecuta estos comandos desde la carpeta raíz del repositorio:

```bash
conda env create -f RAGLAB.yml
conda activate RAGLAB
```

En Windows, abre **Anaconda Prompt** para usar Conda. Para comprobar el entorno y practicar Python, ejecuta los ejercicios desde la raíz:

```bash
python modulo-01/ejercicios/01_hola_python.py
python modulo-01/ejercicios/02_variables_y_tipos.py
python modulo-01/ejercicios/03_condicionales_y_bucles.py
python modulo-01/ejercicios/04_funciones.py
```

También puedes abrir y ejecutar cada archivo desde PyCharm. Selecciona `RAGLAB` como intérprete del proyecto.

## Secuencia sugerida

### Sesión 1 | Configuración y primeros ejercicios

- Presentación del curso y de las herramientas.
- Creación de la cuenta de GitHub y configuración de Git.
- Creación del fork y clonación del repositorio en PyCharm.
- Instalación de Miniconda, creación del entorno `RAGLAB` y selección del intérprete.
- Ejecución guiada de los ejercicios de Python.

### Sesión 2 | Programación y cambios versionados

- Repaso de variables, condiciones, ciclos y funciones.
- Práctica de una mejora pequeña con Kiro CLI y Kiro with GUI.
- Revisión del plan y del diff; ejecución del programa y validación de los resultados.
- Creación de un commit y Push a la rama `DEV` del fork personal.

## Instalar y configurar Kiro

Kiro apoya el trabajo de programación, pero no sustituye la comprensión del código. Cada estudiante revisa los cambios y verifica que cumplan el requerimiento antes de guardarlos.

1. Instala **Kiro CLI** siguiendo la [guía oficial](https://kiro.dev/docs/getting-started/installation/) y completa el inicio de sesión:

   ```bash
   kiro-cli --version
   kiro-cli login
   kiro-cli doctor
   ```

2. En PyCharm 2025.1 o posterior, abre **File → Settings → Plugins → Marketplace**, busca e instala [**Kiro with GUI**](https://plugins.jetbrains.com/plugin/30960-kiro-with-gui). Acepta el aviso de plugin de terceros si aparece y reinicia PyCharm cuando se solicite.
3. Abre Kiro desde el icono que aparece en la barra lateral del IDE.
4. En **Manage → Settings**, confirma que la ruta de Kiro CLI esté configurada. En **Manage → Auth**, verifica que la sesión esté activa. Si PyCharm no detecta `kiro-cli`, indica su ruta completa.
5. En la práctica, pide primero un plan, revisa el diff, ejecuta el script y valida los resultados esperados. Si hace falta, ajusta el requerimiento y repite la comprobación.
6. Cuando comprendas el cambio, revisa `git diff`, crea un commit y súbelo a tu fork desde la rama `DEV` con `git push origin DEV`.

La disponibilidad de modelos, créditos y funciones depende del plan vigente. Consulta la [lista de modelos](https://kiro.dev/docs/models/available-models/) y los [precios de Kiro](https://kiro.dev/pricing/) antes de la sesión.

## Guía paso a paso

La [guía interactiva del módulo 1](../docs/modulo-01.html) incluye instrucciones visuales para configurar GitHub, Miniconda, PyCharm y Kiro, además de recomendaciones para resolver problemas comunes.
