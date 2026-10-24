from rest_framework import serializers

from .models import Component, CustomsSettings, Laptop, Profession, Program


class ProfessionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Profession
        fields = ("id", "name", "icon", "description")


class ProgramSerializer(serializers.ModelSerializer):
    class Meta:
        model = Program
        fields = (
            "id", "name", "icon", "professions",
            "min_cpu_score", "rec_cpu_score", "min_gpu_score", "rec_gpu_score",
            "min_ram_gb", "rec_ram_gb", "min_ssd_gb", "rec_ssd_gb",
        )


class LaptopSerializer(serializers.ModelSerializer):
    class Meta:
        model = Laptop
        fields = (
            "id", "name", "brand", "cpu", "gpu", "ram_gb", "ssd_gb",
            "cpu_score", "gpu_score", "screen", "weight_kg", "image_url",
        )


class ComponentSerializer(serializers.ModelSerializer):
    category_label = serializers.CharField(source="get_category_display", read_only=True)

    class Meta:
        model = Component
        fields = (
            "id", "category", "category_label", "name", "brand", "score", "capacity_gb",
            "socket", "ram_type", "tdp_watts", "psu_watts", "weight_kg", "image_url",
        )


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
