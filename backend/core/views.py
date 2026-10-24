from rest_framework import status, viewsets
from rest_framework.response import Response
from rest_framework.views import APIView

from . import services
from .models import CustomsSettings, Profession, Program
from .serializers import (
    CustomsSettingsSerializer,
    MatchRequestSerializer,
    ProfessionSerializer,
    ProgramSerializer,
    serialize_match,
)


class ProfessionViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Profession.objects.all()
    serializer_class = ProfessionSerializer


class ProgramViewSet(viewsets.ReadOnlyModelViewSet):
    """GET /api/programs/?profession=<id> ile mesleğe göre filtre."""
    serializer_class = ProgramSerializer

    def get_queryset(self):
        qs = Program.objects.prefetch_related("professions")
        profession = self.request.query_params.get("profession")
        return qs.filter(professions__id=profession) if profession else qs


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
