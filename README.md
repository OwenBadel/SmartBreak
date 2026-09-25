# 🧘 SmartBreak - Monitor Ergonómico y Pausas Activas Forzadas

SmartBreak es una aplicación de escritorio nativa para Windows orientada a desarrolladores de software y trabajadores de oficina. Opera en segundo plano a bajo consumo monitoreando la presencia física y la calidad postural del usuario frente al computador. Cuando se detecta fatiga crítica (50 minutos de trabajo sentado continuo o 15 minutos continuos de mala postura), la aplicación despliega una **pantalla de bloqueo estricto a pantalla completa** que solo puede desactivarse poniéndose de pie y realizando un ejercicio frente a la cámara web.

---

## 🏛️ Características Principales

1. **Bandeja del Sistema (System Tray) Silenciosa:**
   - Integrada con `pystray`.
   - Menú contextual:
     - 📊 *Estado actual:* Muestra minutos sentado, calidad postural y cuenta regresiva.
     - ⚡ *Forzar pausa activa:* Dispara manualmente el entrenamiento o descanso.
     - ⚙️ *Configurar intervalos:* Diálogo gráfico para ajustar tiempos, ejercicios y cámara.
     - ❌ *Salir:* Cierre ordenado liberando cámara e hilos.

2. **Motor de Visión de Bajo Consumo (MediaPipe Tasks + OpenCV):**
   - **Fase pasiva (1-2 FPS):** Muestreo eficiente para no consumir CPU/GPU mientras programas.
   - **Detección de presencia:** Valida si el usuario está físicamente frente al monitor.
   - **Cálculo trigonométrico ergonómico:**
     - *Inclinación cervical / Cuello adelantado ($\theta_{cuello}$):* Ángulo entre el vector hombro $\to$ oreja y el eje vertical imaginario. Alerta si $\ge 35^\circ$.
     - *Inclinación torácica / Columna encorvada ($\theta_{torso}$):* Ángulo entre el vector cadera $\to$ hombro y la vertical. Alerta si $\ge 22^\circ$.
     - *Desnivel de hombros:* Detección de asimetría postural.
   - **Acumulador de fatiga:** Activa la pausa al alcanzar 50 minutos de sedentarismo o 15 minutos continuos de mala postura.

3. **Pantalla de Bloqueo Estricto (PyQt6):**
   - Ventana sin marco (`frameless`), a pantalla completa y fija al frente (`WindowStaysOnTopHint`).
   - Intercepción de atajos y eventos de teclado (`Alt+F4`, `Esc`, etc.) para impedir que se cierre prematuramente.
   - Feed de la cámara en vivo con esqueleto anatómico neón renderizado en tiempo real (30 FPS).
   - Panel HUD con telemetría biomecánica: ángulo de rodilla, repeticiones, barra de progreso y temporizador.

4. **Verificación de Ejercicio Físico para Desbloqueo:**
   - **Detección de bipedestación:** Valida que el usuario se haya levantado del escritorio verificando el ángulo cadera-rodilla-tobillo ($\theta_{rodilla} > 165^\circ$).
   - **Ejercicios soportados:**
     - *Brazos sobre la cabeza (Overhead Arm Stretch):* Ambos brazos elevados por encima de la cabeza con codos extendidos durante 60 segundos o 10 elevaciones.
     - *Sentadillas profundas (Squats):* 10 repeticiones completas validadas por una máquina de estados finitos (`DE_PIE` $\to$ `FLEXION` $\to$ `ASCENSO`).
   - Al completar la meta, la pantalla se destruye automáticamente, limpia el acumulador de fatiga y retorna a la bandeja.

---

## 📁 Estructura del Proyecto

```
PROJ_010_SmartBreak/
│
├── AGENTS.md                          # Directiva agéntica OKF de la Fábrica
├── requirements.txt                   # Dependencias fijadas (OpenCV, MediaPipe, PyQt6, pystray, pillow, pywin32)
├── run.py                             # Punto de entrada principal
├── README.md                          # Documentación técnica completa
│
├── config/
│   ├── __init__.py
│   └── settings.py                    # Umbrales ergonómicos, temporizadores y persistencia JSON (~/.smartbreak)
│
├── core/
│   ├── __init__.py
│   ├── fatigue_tracker.py             # Acumulador de tiempo sentado y mala postura sostenida
│   └── orchestrator.py                # Coordinador central de hilos pasivo/activo, cámara y UI
│
├── vision/
│   ├── __init__.py
│   ├── pose_detector.py               # Wrapper unificado de MediaPipe Pose (Tasks API y Solutions)
│   ├── posture_analyzer.py            # Fórmulas trigonométricas (cuello, torso, hombros, presencia)
│   └── exercise_verifier.py           # Máquina de estados: de pie (>165°), brazos arriba y sentadillas
│
├── ui/
│   ├── __init__.py
│   ├── tray_manager.py                # Integración System Tray con pystray y notificaciones
│   ├── lock_window.py                 # Ventana PyQt6 de pantalla completa y bloqueo estricto
│   ├── video_canvas.py                # Lienzo de renderizado de feed con HUD ergonómico
│   └── config_dialog.py               # Diálogo de configuración de intervalos
│
├── models/
│   └── pose_landmarker_lite.task      # Modelo pre-entrenado de MediaPipe PoseLandmarker
│
├── assets/
│   ├── generate_assets.py             # Generador de iconos
│   ├── icon.ico                       # Icono para Windows System Tray y ejecutable
│   └── icon.png                       # Asset gráfico de alta resolución
│
├── packaging/
│   ├── smartbreak.spec                # Configuración PyInstaller (--noconsole, onedir)
│   ├── build_executable.bat           # Script de compilación automática
│   └── SmartBreak_Setup.iss           # Script de Inno Setup (instalador con autoarranque)
│
└── tests/
    ├── __init__.py
    ├── test_posture_math.py           # Pruebas unitarias de trigonometría y máquinas de estados
    └── test_vision_pipeline.py        # Pruebas de integración del pipeline de visión
```

---

## 🚀 Puesta en Marcha en Desarrollo

### 1. Requisitos Previos
- Python 3.10 o superior (verificado en Python 3.12).
- Cámara web integrada o USB.

### 2. Instalación de Dependencias
```bash
pip install -r requirements.txt --trusted-host pypi.org --trusted-host files.pythonhosted.org
```

### 3. Ejecutar la Aplicación
```bash
python run.py
```
La aplicación se iniciará silenciosamente en la bandeja del sistema (junto al reloj de Windows). Haz clic derecho en el icono de SmartBreak para interactuar con el menú contextual.

### 4. Ejecutar las Pruebas Unitarias
```bash
python -m unittest discover tests
```

---

## 📦 Compilación y Generación del Instalador para Windows

### Paso 1: Generar el Ejecutable con PyInstaller
Ejecuta el script por lotes:
```cmd
packaging\build_executable.bat
```
O directamente por consola:
```cmd
pyinstaller --clean -y packaging\smartbreak.spec
```
Esto generará la carpeta distribuible en `dist\SmartBreak\SmartBreak.exe` en modo silencioso (`--noconsole`).

### Paso 2: Generar el Instalador con Inno Setup
1. Abre [Inno Setup Compiler](https://jrsoftware.org/isdl.php).
2. Abre el archivo `packaging\SmartBreak_Setup.iss`.
3. Presiona **Ctrl + F9** (o Menú *Build $\to$ Compile*).
4. El instalador `SmartBreak_Setup_v1.0.0.exe` quedará listo en la carpeta `installer_output/`.
5. Durante la instalación, el usuario podrá marcar la casilla:
   - ✅ *"Iniciar SmartBreak automáticamente al encender Windows"* (configurada en el registro de Windows `HKCU\Software\Microsoft\Windows\CurrentVersion\Run`).

---

## 📐 Fundamentos Matemáticos de Ergonomía

1. **Ángulo entre Tres Articulaciones ($A, B, C$):**
   $$\theta = \arccos\left(\frac{\vec{BA} \cdot \vec{BC}}{\|\vec{BA}\| \|\vec{BC}\|}\right) \times \frac{180^\circ}{\pi}$$

2. **Inclinación respecto al Eje Vertical:**
   $$\theta_{vertical} = \arctan2(|x_{destino} - x_{origen}|, y_{origen} - y_{destino}) \times \frac{180^\circ}{\pi}$$

3. **Criterios Biomecánicos:**
   - **Cuello erguido:** $< 32^\circ$. Adelantado: $\ge 35^\circ$.
   - **Torso vertical:** $< 15^\circ$. Encorvado: $\ge 22^\circ$.
   - **De pie (Extensión de rodilla):** $\theta_{rodilla} > 165^\circ$.
   - **Sentadilla válida:** $\theta_{rodilla} \le 105^\circ$ en el fondo, retornando a $\ge 160^\circ$.
