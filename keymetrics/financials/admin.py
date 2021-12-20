from django.contrib import admin

import keymetrics.financials.models as m

# Register your models here.
# admin.site.register(m.Company)
# admin.site.register(m.Filing)
admin.site.register(m.TimeDimension)
# admin.site.register(m.FinancialConcept)
# admin.site.register(m.FinancialFact)


@admin.register(m.Company)
class CompanyAdmin(admin.ModelAdmin):
    list_filter = ("istracked",)
    search_fields = ["ticker", "name"]
    readonly_fields = ["sec_submissions_url", "sec_facts_url"]
    fieldsets = (
        (None, {"fields": ("name", "ticker", "CIK")}),
        ("SEC URLS", {"fields": ("sec_submissions_url", "sec_facts_url")}),
    )


@admin.register(m.FinancialConcept)
class FinancialConceptAdmin(admin.ModelAdmin):
    list_filter = ("type",)
    search_fields = ["name"]


@admin.register(m.FinancialFact)
class FinancialFactAdmin(admin.ModelAdmin):
    search_fields = ["concept__name"]
    readonly_fields = ["company", "filing", "concept", "period", "value"]

    def get_queryset(self, request):
        queryset = (
            super()
            .get_queryset(request)
            .select_related("company", "filing", "concept", "period")
        )
        return queryset


@admin.register(m.Filing)
class FilingAdmin(admin.ModelAdmin):
    list_filter = ("type",)
    search_fields = ["company__name"]
