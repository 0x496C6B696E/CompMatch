from django.contrib import admin

from .models import (
    Component,
    ComponentPrice,
    CustomsSettings,
    Laptop,
    LaptopPrice,
    Profession,
    ProfessionCategory,
    Program,
    ProgramGroup,
    Store,
)

admin.site.site_header = "CompMatch Yönetim Paneli"
admin.site.site_title = "CompMatch"
admin.site.index_title = "Donanım, mağaza ve gümrük yönetimi"

NAMES = ("name_az", "name_ru", "name_en")


@admin.register(ProfessionCategory)
class ProfessionCategoryAdmin(admin.ModelAdmin):
    list_display = (*NAMES, "icon", "order", "profession_count")
    list_editable = ("order",)
    search_fields = NAMES

    @admin.display(description="Meslek sayısı")
    def profession_count(self, obj):
        return obj.professions.count()


@admin.register(Profession)
class ProfessionAdmin(admin.ModelAdmin):
    list_display = (*NAMES, "category", "icon", "order", "program_count")
    list_editable = ("order",)
    list_filter = ("category",)
    search_fields = NAMES
    fieldsets = (
        (None, {"fields": ("category", "icon", "order")}),
        ("Ad", {"fields": NAMES}),
        ("Açıklama", {"fields": ("description_az", "description_ru", "description_en")}),
    )

    @admin.display(description="Program sayısı")
    def program_count(self, obj):
        return obj.programs.count()


@admin.register(ProgramGroup)
class ProgramGroupAdmin(admin.ModelAdmin):
    list_display = (*NAMES, "order", "program_count")
    list_editable = ("order",)
    search_fields = NAMES

    @admin.display(description="Program sayısı")
    def program_count(self, obj):
        return obj.programs.count()


@admin.register(Program)
class ProgramAdmin(admin.ModelAdmin):
    list_display = (
        "name", "group", "min_cpu_score", "rec_cpu_score", "min_gpu_score", "rec_gpu_score",
        "min_ram_gb", "rec_ram_gb", "min_ssd_gb", "rec_ssd_gb",
    )
    list_filter = ("group", "professions")
    search_fields = ("name",)
    filter_horizontal = ("professions",)
    fieldsets = (
        (None, {"fields": ("name", "icon", "group", "professions")}),
        ("Kısa açıklama (sade dil)", {"fields": ("blurb_az", "blurb_ru", "blurb_en")}),
        ("Minimum gereksinimler", {"fields": ("min_cpu_score", "min_gpu_score", "min_ram_gb", "min_ssd_gb")}),
        ("Önerilen gereksinimler", {"fields": ("rec_cpu_score", "rec_gpu_score", "rec_ram_gb", "rec_ssd_gb")}),
    )


@admin.register(Store)
class StoreAdmin(admin.ModelAdmin):
    list_display = ("name", "kind", "website", "shipping_per_kg_usd")
    list_filter = ("kind",)
    search_fields = ("name",)


class LaptopPriceInline(admin.TabularInline):
    model = LaptopPrice
    extra = 1
    fields = ("store", "price", "currency", "in_stock", "url")
    autocomplete_fields = ("store",)


@admin.register(Laptop)
class LaptopAdmin(admin.ModelAdmin):
    list_display = (
        "name", "brand", "cpu", "gpu", "ram_gb", "ssd_gb",
        "cpu_score", "gpu_score", "weight_kg", "price_count",
    )
    list_filter = ("brand",)
    search_fields = ("name", "cpu", "gpu")
    inlines = [LaptopPriceInline]

    @admin.display(description="Fiyat kaydı")
    def price_count(self, obj):
        return obj.prices.count()


class ComponentPriceInline(admin.TabularInline):
    model = ComponentPrice
    extra = 1
    fields = ("store", "price", "currency", "in_stock", "url")
    autocomplete_fields = ("store",)


@admin.register(Component)
class ComponentAdmin(admin.ModelAdmin):
    list_display = (
        "name", "category", "brand", "score", "capacity_gb", "socket",
        "ram_type", "tdp_watts", "psu_watts", "weight_kg",
    )
    list_filter = ("category", "brand", "socket", "ram_type")
    search_fields = ("name",)
    inlines = [ComponentPriceInline]
    fieldsets = (
        (None, {"fields": ("category", "name", "brand", "weight_kg", "image_url")}),
        ("Performans (CPU/GPU)", {"fields": ("score", "tdp_watts")}),
        ("Kapasite (RAM/SSD)", {"fields": ("capacity_gb",)}),
        ("Uyumluluk", {"fields": ("socket", "ram_type")}),
        ("Güç (Kasa+PSU)", {"fields": ("psu_watts",)}),
    )


@admin.register(CustomsSettings)
class CustomsSettingsAdmin(admin.ModelAdmin):
    list_display = (
        "__str__", "duty_free_limit_usd", "duty_rate", "declaration_fee_usd",
        "usd_azn_rate", "shipping_per_kg_usd",
    )

    def has_add_permission(self, request):
        return not CustomsSettings.objects.exists()

    def has_delete_permission(self, request, obj=None):
        return False
