from django.db import models


class GeoAreaType(models.TextChoices):
    ERGA_OMNES = "ERGA_OMNES", "All countries (erga omnes)"
    GROUP = "GROUP", "A group of countries"
    COUNTRY = "COUNTRY", "Specific countries or regions"


ERGA_OMNES_EXCLUSIONS_PREFIX = "erga_omnes_exclusions"
ERGA_OMNES_EXCLUSIONS_FORMSET_PREFIX = (
    f"{ERGA_OMNES_EXCLUSIONS_PREFIX}_formset"  # /PS-IGNORE
)
GROUP_EXCLUSIONS_PREFIX = "geo_group_exclusions"
GROUP_EXCLUSIONS_FORMSET_PREFIX = f"{GROUP_EXCLUSIONS_PREFIX}_formset"

GEO_GROUP_PREFIX = "geographical_area_group"
GEO_GROUP_FORMSET_PREFIX = f"{GEO_GROUP_PREFIX}_formset"

COUNTRY_REGION_PREFIX = "country_region"
COUNTRY_REGION_FORMSET_PREFIX = f"{COUNTRY_REGION_PREFIX}_formset"


SUBFORM_PREFIX_MAPPING = {
    GeoAreaType.GROUP: GEO_GROUP_PREFIX,
    GeoAreaType.COUNTRY: COUNTRY_REGION_FORMSET_PREFIX,
}

FORMSET_PREFIX_MAPPING = {
    GeoAreaType.ERGA_OMNES: ERGA_OMNES_EXCLUSIONS_FORMSET_PREFIX,
    GeoAreaType.GROUP: GROUP_EXCLUSIONS_FORMSET_PREFIX,
    GeoAreaType.COUNTRY: COUNTRY_REGION_FORMSET_PREFIX,
}

EXCLUSIONS_FORMSET_PREFIX_MAPPING = {
    GeoAreaType.ERGA_OMNES: ERGA_OMNES_EXCLUSIONS_FORMSET_PREFIX,
    GeoAreaType.GROUP: GROUP_EXCLUSIONS_FORMSET_PREFIX,
    GeoAreaType.COUNTRY: None,
}

FIELD_NAME_MAPPING = {
    GeoAreaType.ERGA_OMNES: "erga_omnes_exclusion",
    GeoAreaType.GROUP: "geo_group_exclusion",
    GeoAreaType.COUNTRY: "geographical_area_country_or_region",
}
