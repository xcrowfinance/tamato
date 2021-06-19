from additional_codes import import_parsers as parsers
from additional_codes import models
from additional_codes import serializers
from importer.handlers import BaseHandler
from importer.taric import RecordParser


@RecordParser.use_for_xml_serialization
class AdditionalCodeTypeHandler(BaseHandler):
    serializer_class = serializers.AdditionalCodeTypeSerializer
    xml_model = parsers.AdditionalCodeTypeParser


@AdditionalCodeTypeHandler.register_dependant
class AdditionalCodeTypeDescriptionHandler(BaseHandler):
    dependencies = [AdditionalCodeTypeHandler]
    serializer_class = serializers.AdditionalCodeTypeSerializer
    xml_model = parsers.AdditionalCodeTypeDescriptionParser


@RecordParser.use_for_xml_serialization
class AdditionalCodeHandler(BaseHandler):
    links = (
        {
            "model": models.AdditionalCodeType,
            "name": "type",
        },
    )
    serializer_class = serializers.AdditionalCodeImporterSerializer
    xml_model = parsers.AdditionalCodeParser


class BaseAdditionalCodeDescriptionHandler(BaseHandler):
    links = (
        {
            "identifying_fields": ("sid", "code", "type__sid"),
            "model": models.AdditionalCode,
            "name": "described_additionalcode",
        },
    )
    serializer_class = serializers.AdditionalCodeDescriptionImporterSerializer
    abstract = True

    def get_described_additionalcode_link(self, model, kwargs):
        code_type = models.AdditionalCodeType.objects.get_latest_version(
            sid=kwargs.pop("type__sid"),
        )
        obj = model.objects.get_latest_version(type=code_type, **kwargs)
        return obj


@RecordParser.use_for_xml_serialization
class AdditionalCodeDescriptionHandler(BaseAdditionalCodeDescriptionHandler):
    serializer_class = serializers.AdditionalCodeDescriptionImporterSerializer
    xml_model = parsers.AdditionalCodeDescriptionParser


@AdditionalCodeDescriptionHandler.register_dependant
class AdditionalCodeDescriptionPeriodHandler(BaseAdditionalCodeDescriptionHandler):
    dependencies = [AdditionalCodeDescriptionHandler]
    serializer_class = serializers.AdditionalCodeDescriptionImporterSerializer
    xml_model = parsers.AdditionalCodeDescriptionPeriodParser
