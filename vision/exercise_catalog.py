"""
Catálogo Centralizado de Ejercicios Ergonómicos de SmartBreak.
Define las modalidades de desbloqueo, con énfasis en ejercicios de escritorio
(sentado o de pie en plano cercano a la cámara) de alta fidelidad biomecánica.
"""

from __future__ import annotations
from dataclasses import dataclass
from typing import Dict, List, Tuple


@dataclass
class ExerciseMetadata:
    """Metadatos descriptivos y de configuración de un ejercicio."""
    id: str
    name: str
    category: str
    description: str
    metric_type: str            # "reps" o "time"
    default_target: int         # Ej. 10 reps o 45 segundos
    requires_standing: bool     # True solo si exige ver piernas/bipedestación
    tips: List[str]


EXERCISE_CATALOG: Dict[str, ExerciseMetadata] = {
    "shoulder_shrugs": ExerciseMetadata(
        id="shoulder_shrugs",
        name="Encogimiento de Hombros",
        category="Escritorio (Sentado o de Pie)",
        description="Eleva ambos hombros hacia las orejas, sostén 1 segundo y relájalos completamente hacia abajo.",
        metric_type="reps",
        default_target=10,
        requires_standing=False,
        tips=[
            "✓ Espalda recta y mirada al frente",
            "✓ Sube los hombros bien alto hacia las orejas",
            "✓ Relaja despacio soltando toda la tensión"
        ]
    ),
    "overhead_touch": ExerciseMetadata(
        id="overhead_touch",
        name="Toque de Manos sobre la Cabeza",
        category="Escritorio (Sentado o de Pie)",
        description="Junta las palmas de las manos sobre tu cabeza con los brazos extendidos y desciende al pecho.",
        metric_type="reps",
        default_target=10,
        requires_standing=False,
        tips=[
            "✓ Junta ambas palmas por encima de la cabeza",
            "✓ Alarga la columna hacia arriba",
            "✓ Baja las manos al pecho en cada repetición"
        ]
    ),
    "cactus_arms": ExerciseMetadata(
        id="cactus_arms",
        name="Apertura Pectoral (Brazos Cactus)",
        category="Escritorio (Sentado o de Pie)",
        description="Con codos a 90° a la altura de hombros, abre amplio expandiendo el pecho y junta los codos al frente.",
        metric_type="reps",
        default_target=10,
        requires_standing=False,
        tips=[
            "✓ Codos alineados a la altura de los hombros",
            "✓ Abre los brazos hacia atrás abriendo el pecho",
            "✓ Junta los antebrazos frente al rostro"
        ]
    ),
    "neck_stretch": ExerciseMetadata(
        id="neck_stretch",
        name="Estiramiento Lateral de Cuello",
        category="Escritorio (Sentado o de Pie)",
        description="Inclina la cabeza lateralmente acercando la oreja al hombro, alternando izquierda y derecha con suavidad.",
        metric_type="reps",
        default_target=8,
        requires_standing=False,
        tips=[
            "✓ Movimiento suave y controlado sin forzar",
            "✓ Acerca la oreja hacia el hombro",
            "✓ Mantén los hombros relajados sin levantarlos"
        ]
    ),
    "overhead_stretch": ExerciseMetadata(
        id="overhead_stretch",
        name="Estiramiento de Brazos Overhead",
        category="Cuerpo Superior",
        description="Eleva ambos brazos rectos hacia el techo con los codos extendidos y mantén la posición.",
        metric_type="time",
        default_target=45,
        requires_standing=False,
        tips=[
            "✓ Brazos rectos extendidos hacia el techo",
            "✓ Codos estirados y palmas hacia el frente",
            "✓ Respiración rítmica y profunda"
        ]
    ),
    "squats": ExerciseMetadata(
        id="squats",
        name="Sentadillas Profundas",
        category="Cuerpo Completo (De Pie)",
        description="Ponte de pie frente a la cámara, flexiona rodillas a 90° con la espalda recta y regresa arriba.",
        metric_type="reps",
        default_target=10,
        requires_standing=True,
        tips=[
            "✓ Requiere estar de pie frente a la cámara",
            "✓ Desciende las caderas hasta 90° de flexión",
            "✓ Espalda recta y mirada al frente"
        ]
    ),
}


def get_exercise_metadata(exercise_id: str) -> ExerciseMetadata:
    """Retorna los metadatos del ejercicio o fallback seguro a shoulder_shrugs."""
    return EXERCISE_CATALOG.get(exercise_id, EXERCISE_CATALOG["shoulder_shrugs"])


def list_exercise_choices() -> List[Tuple[str, str, str]]:
    """
    Retorna la lista de ejercicios para combos en UI:
    [(id, nombre_formateado, categoria)]
    """
    choices = []
    for ex_id, meta in EXERCISE_CATALOG.items():
        formatted_name = f"{meta.name} ({meta.category})"
        choices.append((ex_id, formatted_name, meta.category))
    return choices
