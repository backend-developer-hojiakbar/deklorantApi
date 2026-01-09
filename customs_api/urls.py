from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()

# Register viewsets
# User registration handled separately as it's not a ViewSet
router.register(r'hs-codes', views.HsCodeViewSet)
router.register(r'classification-rulings', views.ClassificationRulingViewSet)
router.register(r'optimization-tips', views.OptimizationTipViewSet)
router.register(r'product-items', views.ProductItemViewSet)
router.register(r'validation-issues', views.ValidationIssueViewSet)
router.register(r'declarations', views.DeclarationViewSet)
router.register(r'audit-results', views.AuditResultViewSet)
router.register(r'calculation-results', views.CalculationResultViewSet)
router.register(r'hs-code-predictions', views.HsCodePredictionViewSet)
router.register(r'chat-messages', views.ChatMessageViewSet)
router.register(r'decision-tree-questions', views.DecisionTreeQuestionViewSet)
router.register(r'incoterm-recommendations', views.IncotermRecommendationViewSet)
router.register(r'trade-route-options', views.TradeRouteOptionViewSet)
router.register(r'currency-rates', views.CurrencyRateViewSet)
router.register(r'hs-code-passports', views.HsCodePassportViewSet)
router.register(r'user-templates', views.UserTemplateViewSet)
router.register(r'document-generations', views.DocumentGenerationViewSet)
router.register(r'classification-searches', views.ClassificationSearchViewSet)

urlpatterns = [
    # Authentication
    path('auth/register/', views.UserRegistrationView.as_view(), name='user-register'),
    path('auth/login/', views.UserLoginView.as_view(), name='user-login'),
    
    # Main API routes
    path('', include(router.urls)),
    
    # Custom calculation endpoints
    path('calculate-customs-duties/', views.calculate_customs_duties_api, name='calculate-customs-duties'),
    path('perform-risk-analysis/', views.perform_risk_analysis_api, name='perform-risk-analysis'),
    
    # HS Code search and details
    path('search-hs-codes/', views.search_hs_codes_api, name='search-hs-codes'),
    path('hs-code-details/<str:code>/', views.get_hs_code_details_api, name='get-hs-code-details'),
    
    # Declaration-specific endpoints
    path('declarations/<int:declaration_id>/audit/', views.audit_declaration_api, name='audit-declaration'),
    path('declarations/<int:declaration_id>/summary/', views.get_declaration_summary, name='declaration-summary'),
    path('declarations/<int:declaration_id>/export-xml/', views.ExportXmlView.as_view(), name='export-declaration-xml'),
    
    # Additional utility endpoints
    path('currency-rates/latest/', views.CurrencyRateViewSet.as_view({'get': 'list'}), name='latest-currency-rates'),
    
    # AI integration endpoints
    path('store-hs-code-search/', views.store_hs_code_search, name='store-hs-code-search'),
    path('store-hs-code-passport/', views.store_hs_code_passport, name='store-hs-code-passport'),
    path('store-document-generation/', views.store_document_generation, name='store-document-generation'),
    path('user-templates/', views.get_user_templates, name='get-user-templates'),
    path('user-templates/upload/', views.upload_user_template, name='upload-user-template'),
    path('dashboard-data/', views.get_dashboard_data, name='get-dashboard-data'),
]