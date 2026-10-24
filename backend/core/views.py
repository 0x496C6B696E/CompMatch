from rest_framework import status, viewsets
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response
from rest_framework.views import APIView

from . import services
from .models import DEFAULT_LANG, LANGS, Component, CustomsSettings, Laptop, Profession, Program
from .serializers import (
    ComponentCatalogSerializer,
    CustomsSettingsSerializer,
    LaptopCatalogSerializer,
    MatchRequestSerializer,
    ProfessionSerializer,
    ProgramSerializer,
    serialize_match,
)


def get_lang(request):
    """?lang=az|ru|en, yoksa Accept-Language'ın ilk iki harfi, yoksa az."""
    lang = request.query_params.get("lang") or request.headers.get("Accept-Language", "")[:2].lower()
    return lang if lang in LANGS else DEFAULT_LANG


class LangViewSet(viewsets.ReadOnlyModelViewSet):
    def get_serializer_context(self):
        return {**super().get_serializer_context(), "lang": get_lang(self.request)}


class ProfessionViewSet(LangViewSet):
    queryset = Profession.objects.select_related("category")
    serializer_class = ProfessionSerializer


class ProgramViewSet(LangViewSet):
    """GET /api/programs/?profession=<id> ile mesleğe göre filtre."""
    serializer_class = ProgramSerializer

    def get_queryset(self):
        qs = Program.objects.select_related("group").prefetch_related("professions")
        profession = self.request.query_params.get("profession")
        if not profession:
            return qs
        if not profession.isdigit():
            raise ValidationError({"profession": "Geçersiz meslek id."})
        return qs.filter(professions__id=int(profession))


class CatalogViewSet(LangViewSet):
    """Fiyat karşılaştırması ve 'uygun meslekler' ile liste/detay. Küçük katalog: hepsi tek seferde."""

    def get_serializer_context(self):
        return {
            **super().get_serializer_context(),
            "settings": CustomsSettings.load(),
            "prof_reqs": services.profession_requirements(),
        }


class LaptopViewSet(CatalogViewSet):
    queryset = Laptop.objects.prefetch_related("prices__store")
    serializer_class = LaptopCatalogSerializer


class ComponentViewSet(CatalogViewSet):
    """GET /api/components/?category=cpu"""
    serializer_class = ComponentCatalogSerializer

    def get_queryset(self):
        qs = Component.objects.prefetch_related("prices__store")
        category = self.request.query_params.get("category")
        return qs.filter(category=category) if category else qs


class MatchView(APIView):
    """POST {program_ids: [..], device_type: 'laptop'|'pc'}"""

    def post(self, request):
        ser = MatchRequestSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        programs = Program.objects.filter(id__in=ser.validated_data["program_ids"])
        if not programs.exists():
            return Response({"detail": "Geçerli program bulunamadı."}, status=status.HTTP_400_BAD_REQUEST)
        result = services.match(programs, ser.validated_data["device_type"])
        return Response(serialize_match(result))


class SettingsView(APIView):
    def get(self, request):
        return Response(CustomsSettingsSerializer(CustomsSettings.load()).data)
