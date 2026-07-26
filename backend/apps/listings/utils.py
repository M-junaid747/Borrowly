from django.db.models import F, FloatField, ExpressionWrapper
from django.db.models.functions import ACos, Cos, Radians, Sin

EARTH_RADIUS_KM = 6371.0


def annotate_distance(queryset, lat, lng):
    """
    Annotate each row with `distance_km` from (lat, lng) using the
    great-circle (Haversine/spherical law of cosines) formula, computed
    directly in SQL so it works with plain lat/lng float columns on any
    database (SQLite for dev, Postgres for prod) without PostGIS.

    Coordinates are optional on a listing, so callers must run this only
    on a queryset already filtered to rows with non-null latitude/longitude
    (see listings/views.py) - the trig functions below don't handle NULLs.
    """
    distance_expr = ExpressionWrapper(
        EARTH_RADIUS_KM
        * ACos(
            Cos(Radians(lat))
            * Cos(Radians(F("latitude")))
            * Cos(Radians(F("longitude")) - Radians(lng))
            + Sin(Radians(lat)) * Sin(Radians(F("latitude")))
        ),
        output_field=FloatField(),
    )
    return queryset.annotate(distance_km=distance_expr)
