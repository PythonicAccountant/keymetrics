from django.contrib import admin

import keymetrics.financials.models as m

admin.site.register(m.TimeDimension)


@admin.register(m.Company)
class CompanyAdmin(admin.ModelAdmin):
    list_filter = ("istracked",)
    search_fields = ["ticker", "name"]
    readonly_fields = ["sec_submissions_url", "sec_facts_url"]
    fieldsets = (
        (None, {"fields": ("name", "ticker", "CIK", "istracked")}),
        ("SEC URLS", {"fields": ("sec_submissions_url", "sec_facts_url")}),
    )


@admin.register(m.FinancialConcept)
class FinancialConceptAdmin(admin.ModelAdmin):
    list_filter = ("type",)
    search_fields = ["name"]


@admin.register(m.FinancialFact)
class FinancialFactAdmin(admin.ModelAdmin):
    search_fields = ["concept__name"]
    readonly_fields = [
        "company",
        "filing",
        "concept",
        "period",
        "formatted_value",
        "million_value",
    ]
    exclude = ["value"]

    def get_queryset(self, request):
        queryset = (
            super()
            .get_queryset(request)
            .select_related("company", "filing", "concept", "period")
        )
        return queryset

    def formatted_value(self, obj):
        return f"{obj.value:,} {obj.concept.unit}"

    def million_value(self, obj):
        return f"{int(round(obj.value/1000000,0))}M {obj.concept.unit}"


@admin.register(m.Filing)
class FilingAdmin(admin.ModelAdmin):
    list_filter = ("type",)
    search_fields = ["company__name"]

    def get_queryset(self, request):
        queryset = super().get_queryset(request).select_related("company")
        return queryset


@admin.register(m.Checksum)
class ChecksumAdmin(admin.ModelAdmin):
    list_filter = ("api_type",)
    search_fields = ["company__name"]
    readonly_fields = ["company", "api_type", "checksum"]

    def get_queryset(self, request):
        queryset = super().get_queryset(request).select_related("company")
        return queryset
