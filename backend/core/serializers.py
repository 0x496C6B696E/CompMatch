from rest_framework import serializers

from . import services
from .models import (
    DEFAULT_LANG,
    Component,
    CustomsSettings,
    Laptop,
    Profession,
    ProfessionCategory,
    Program,
    ProgramGroup,
    tr,
)


class LangMixin:
    @property
    def lang(self):
        return self.context.get("lang", DEFAULT_LANG)

    def _tr(self, obj, field):
        return tr(obj, field, self.lang)


class ProfessionCategorySerializer(LangMixin, serializers.ModelSerializer):
    name = serializers.SerializerMethodField()

    class Meta:
        model = ProfessionCategory
        fields = ("id", "name", "icon", "order")

    def get_name(self, obj):
        return self._tr(obj, "name")


class ProfessionSerializer(LangMixin, serializers.ModelSerializer):
    name = serializers.SerializerMethodField()
    description = serializers.SerializerMethodField()
    category = ProfessionCategorySerializer(read_only=True)

    class Meta:
        model = Profession
        fields = ("id", "name", "description", "icon", "order", "category")

    def get_name(self, obj):
        return self._tr(obj, "name")

    def get_description(self, obj):
        return self._tr(obj, "description")


class ProgramGroupSerializer(LangMixin, serializers.ModelSerializer):
    name = serializers.SerializerMethodField()

    class Meta:
        model = ProgramGroup
        fields = ("id", "name", "order")

    def get_name(self, obj):
        return self._tr(obj, "name")


class ProgramSerializer(LangMixin, serializers.ModelSerializer):
    blurb = serializers.SerializerMethodField()
    group = ProgramGroupSerializer(read_only=True)

    class Meta:
        model = Program
        fields = (
            "id", "name", "icon", "blurb", "group", "professions",
            "min_cpu_score", "rec_cpu_score", "min_gpu_score", "rec_gpu_score",
            "min_ram_gb", "rec_ram_gb", "min_ssd_gb", "rec_ssd_gb",
        )

    def get_blurb(self, obj):
        return self._tr(obj, "blurb")


class LaptopSerializer(serializers.ModelSerializer):
    class Meta:
        model = Laptop
        fields = (
            "id", "name", "brand", "cpu", "gpu", "ram_gb", "ssd_gb",
            "cpu_score", "gpu_score", "screen", "weight_kg", "image_url",
        )


class ComponentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Component
        fields = (
            "id", "category", "name", "brand", "score", "capacity_gb",
            "socket", "ram_type", "tdp_watts", "psu_watts", "weight_kg", "image_url",
        )


class CatalogMixin(LangMixin):
    """Katalog listeleri: fiyat karşılaştırması + 'hangi meslekler için uygun'. context: settings, prof_reqs."""

    def get_prices(self, obj):
        return services.compare_prices(obj, self.context["settings"])

    def _fits(self, pairs):
        return [{"id": p.id, "name": self._tr(p, "name"), "level": level} for p, level in pairs]


class LaptopCatalogSerializer(CatalogMixin, LaptopSerializer):
    prices = serializers.SerializerMethodField()
    fits = serializers.SerializerMethodField()

    class Meta(LaptopSerializer.Meta):
        fields = LaptopSerializer.Meta.fields + ("prices", "fits")

    def get_fits(self, obj):
        return self._fits(services.laptop_fits(obj, self.context["prof_reqs"]))


class ComponentCatalogSerializer(CatalogMixin, ComponentSerializer):
    prices = serializers.SerializerMethodField()
    fits = serializers.SerializerMethodField()

    class Meta(ComponentSerializer.Meta):
        fields = ComponentSerializer.Meta.fields + ("prices", "fits")

    def get_fits(self, obj):
        return self._fits(services.component_fits(obj, self.context["prof_reqs"]))


class CustomsSettingsSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomsSettings
        fields = ("duty_free_limit_usd", "duty_rate", "declaration_fee_usd", "usd_azn_rate", "shipping_per_kg_usd")


class MatchRequestSerializer(serializers.Serializer):
    program_ids = serializers.ListField(child=serializers.IntegerField(), allow_empty=False)
    device_type = serializers.ChoiceField(choices=["laptop", "pc"])


# services.match() çıktısını JSON'a çevirir.
def serialize_match(result):
    out = {
        "device_type": result["device_type"],
        "requirements": result["requirements"],
        "settings": CustomsSettingsSerializer(result["settings"]).data,
    }
    if "laptops" in result:
        out["laptops"] = [
            {**p, "laptop": LaptopSerializer(p["laptop"]).data} for p in result["laptops"]
        ]
    if "components" in result:
        out["components"] = [
            {**p, "component": ComponentSerializer(p["component"]).data if p["component"] else None}
            for p in result["components"]
        ]
    return out
