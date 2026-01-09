from django.contrib import admin
from django.contrib.auth import get_user_model
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import (
    User, HsCode, ClassificationRuling, OptimizationTip, ProductItem, ValidationIssue,
    Declaration, AuditResult, CalculationResult, HsCodePrediction, PriceRiskAnalysis,
    ChatMessage, DecisionTreeQuestion, IncotermRecommendation, TradeRouteOption, CurrencyRate,
    HsCodePassport, UserTemplate, DocumentGeneration, ClassificationSearch
)


User = get_user_model()


class SimpleUserAdmin(admin.ModelAdmin):
    list_display = ['id', 'username', 'phone', 'first_name', 'last_name', 'role', 'plan', 'is_active']
    list_filter = ['role', 'plan', 'is_active']
    search_fields = ['username', 'phone', 'first_name', 'last_name']
    fields = ['username', 'phone', 'first_name', 'last_name', 'role', 'plan', 'plan_expiry', 'avatar', 'is_active', 'is_staff']


class SimpleHsCodeAdmin(admin.ModelAdmin):
    list_display = ['code', 'description_uz', 'duty_rate', 'vat_rate', 'is_sanctioned']
    list_filter = ['is_sanctioned', 'version_status']
    search_fields = ['code', 'description_uz']


class SimpleProductItemAdmin(admin.ModelAdmin):
    list_display = ['id', 'name', 'hs_code', 'price', 'currency']
    list_filter = ['currency']
    search_fields = ['name', 'hs_code']


class SimpleDeclarationAdmin(admin.ModelAdmin):
    list_display = ['id', 'contract_number', 'partner_name', 'status', 'mode']
    list_filter = ['status', 'mode']
    search_fields = ['id', 'contract_number', 'partner_name']


class SimpleAuditResultAdmin(admin.ModelAdmin):
    list_display = ['id', 'score', 'risk_level']
    search_fields = ['id']
    list_per_page = 25


class SimpleCalculationResultAdmin(admin.ModelAdmin):
    list_display = ['id', 'customs_duty', 'vat', 'total']
    search_fields = ['id']


class SimpleHsCodePredictionAdmin(admin.ModelAdmin):
    list_display = ['id', 'code', 'confidence']
    list_filter = []
    search_fields = ['code', 'description']


class SimpleCurrencyRateAdmin(admin.ModelAdmin):
    list_display = ['code', 'name', 'rate', 'date', 'trend']
    list_filter = ['code', 'trend']
    search_fields = ['code', 'name']


class SimpleChatMessageAdmin(admin.ModelAdmin):
    list_display = ['id', 'role', 'timestamp']
    list_filter = ['role']
    search_fields = ['content']


class SimpleHsCodePassportAdmin(admin.ModelAdmin):
    list_display = ['id', 'code', 'duty_rate']
    list_filter = []
    search_fields = ['code', 'description']


class SimpleUserTemplateAdmin(admin.ModelAdmin):
    list_display = ['id', 'name', 'template_type', 'is_public']
    list_filter = ['template_type', 'is_public']
    search_fields = ['name']


class SimpleDocumentGenerationAdmin(admin.ModelAdmin):
    list_display = ['id', 'document_type']
    list_filter = ['document_type']


class SimpleClassificationSearchAdmin(admin.ModelAdmin):
    list_display = ['id', 'search_query', 'results_count']
    list_filter = []
    search_fields = ['search_query']


class SimplePriceRiskAnalysisAdmin(admin.ModelAdmin):
    list_display = ['id', 'risk_level', 'average_price']
    list_filter = ['risk_level']
    search_fields = ['id']


class SimpleDecisionTreeQuestionAdmin(admin.ModelAdmin):
    list_display = ['id', 'question']
    search_fields = ['question']


class SimpleIncotermRecommendationAdmin(admin.ModelAdmin):
    list_display = ['code', 'name']
    search_fields = ['code', 'name']


class SimpleTradeRouteOptionAdmin(admin.ModelAdmin):
    list_display = ['method', 'estimated_cost', 'risk']
    list_filter = ['risk']
    search_fields = ['method']


class SimpleOptimizationTipAdmin(admin.ModelAdmin):
    list_display = ['alternative_code', 'duty_rate', 'hs_code']
    search_fields = ['alternative_code', 'hs_code__code']


class SimpleValidationIssueAdmin(admin.ModelAdmin):
    list_display = ['type', 'message', 'field']
    list_filter = ['type']
    search_fields = ['message', 'field']


class SimpleClassificationRulingAdmin(admin.ModelAdmin):
    list_display = ['id', 'date', 'outcome_code']
    search_fields = ['id', 'outcome_code']


# Register all models with simple admin classes
admin.site.register(User, SimpleUserAdmin)
admin.site.register(HsCode, SimpleHsCodeAdmin)
admin.site.register(ProductItem, SimpleProductItemAdmin)
admin.site.register(Declaration, SimpleDeclarationAdmin)
admin.site.register(AuditResult, SimpleAuditResultAdmin)
admin.site.register(CalculationResult, SimpleCalculationResultAdmin)
admin.site.register(HsCodePrediction, SimpleHsCodePredictionAdmin)
admin.site.register(CurrencyRate, SimpleCurrencyRateAdmin)
admin.site.register(ChatMessage, SimpleChatMessageAdmin)
admin.site.register(HsCodePassport, SimpleHsCodePassportAdmin)
admin.site.register(UserTemplate, SimpleUserTemplateAdmin)
admin.site.register(DocumentGeneration, SimpleDocumentGenerationAdmin)
admin.site.register(ClassificationSearch, SimpleClassificationSearchAdmin)
admin.site.register(PriceRiskAnalysis, SimplePriceRiskAnalysisAdmin)
admin.site.register(DecisionTreeQuestion, SimpleDecisionTreeQuestionAdmin)
admin.site.register(IncotermRecommendation, SimpleIncotermRecommendationAdmin)
admin.site.register(TradeRouteOption, SimpleTradeRouteOptionAdmin)
admin.site.register(OptimizationTip, SimpleOptimizationTipAdmin)
admin.site.register(ValidationIssue, SimpleValidationIssueAdmin)
admin.site.register(ClassificationRuling, SimpleClassificationRulingAdmin)