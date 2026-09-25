"""
Módulo de Detección y Gestión de Cámaras Web para Windows.
Obtiene los nombres descriptivos reales (Friendly Names) de los dispositivos de video
conectados utilizando DirectShow (pygrabber / comtypes) alineados con los índices de OpenCV.
"""

from typing import List, Tuple
import cv2


def get_available_cameras() -> List[Tuple[int, str]]:
    """
    Detecta y retorna la lista de cámaras web conectadas al sistema con sus nombres reales.
    
    Retorna:
        List[Tuple[int, str]]: Lista de pares (índice_opencv, nombre_amigable_del_dispositivo).
        Ejemplo: [(0, "Camera (NVIDIA Broadcast)"), (1, "OBS Virtual Camera")]
    """
    cameras: List[Tuple[int, str]] = []

    # 1. Intentar obtención de nombres reales vía DirectShow con pygrabber
    try:
        from pygrabber.dshow_graph import FilterGraph
        graph = FilterGraph()
        device_names = graph.get_input_devices()
        if device_names:
            for idx, name in enumerate(device_names):
                cameras.append((idx, f"{name} (Índice {idx})"))
            return cameras
    except Exception as e:
        print(f"[CameraManager] DirectShow pygrabber no disponible o generó error: {e}")

    # 2. Respaldo por sondeo directo con OpenCV si pygrabber no detecta
    try:
        for idx in range(4):
            cap = cv2.VideoCapture(idx, cv2.CAP_DSHOW)
            if cap.isOpened():
                cameras.append((idx, f"Dispositivo de Video #{idx} (Activo)"))
                cap.release()
            else:
                cap.release()
    except Exception as e:
        print(f"[CameraManager] Error en sondeo OpenCV de respaldo: {e}")

    # 3. Dispositivo predeterminado de respaldo si no hay dispositivos accesibles
    if not cameras:
        cameras.append((0, "Cámara 0 (Predeterminada del sistema)"))

    return cameras
