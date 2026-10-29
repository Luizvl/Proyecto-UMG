from django.db.models import Q

from apps.solicitudes.models import Solicitud

from .models import Pago

ESTADOS_PAGO_ACTIVO = (Pago.PENDIENTE, Pago.APROBADO)


def solicitudes_por_pagar(usuario):
    """APROBADAS, con cobertura definida menor a 100% y sin pago en revisión o aprobado."""
    return (
        Solicitud.objects
        .filter(estudiante=usuario, estado=Solicitud.APROBADA, condicion_pago__isnull=False)
        .exclude(condicion_pago__cobertura_porcentaje=100)
        .exclude(pagos__estado__in=ESTADOS_PAGO_ACTIVO)
        .select_related("convocatoria", "condicion_pago")
    )


def estado_de_pagos(usuario):
    """Datos para el banner que ve el estudiante."""
    primera = solicitudes_por_pagar(usuario).first()
    aprobadas = Solicitud.objects.filter(estudiante=usuario, estado=Solicitud.APROBADA)
    return {
        "debe_pagar": primera is not None,
        "solicitud_por_pagar": primera,
        "condicion_por_pagar": primera.condicion_pago if primera else None,
        "pago_en_revision": Pago.objects.filter(estudiante=usuario, estado=Pago.PENDIENTE).exists(),
        "pendiente_definicion": (
            aprobadas.filter(condicion_pago__isnull=True)
            .exclude(pagos__estado=Pago.APROBADO)
            .exists()
        ),
        "beca_activa": aprobadas.filter(
            Q(condicion_pago__cobertura_porcentaje=100) | Q(pagos__estado=Pago.APROBADO)
        ).exists(),
    }