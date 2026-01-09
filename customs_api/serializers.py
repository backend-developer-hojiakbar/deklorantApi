from rest_framework import serializers
from .models import (
    User, HsCode, ClassificationRuling, OptimizationTip, ProductItem, ValidationIssue,
    Declaration, AuditResult, CalculationResult, HsCodePrediction, PriceRiskAnalysis,
    ChatMessage, DecisionTreeQuestion, IncotermRecommendation, TradeRouteOption, CurrencyRate,
    HsCodePassport, UserTemplate, DocumentGeneration, ClassificationSearch
)


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = [
            'id', 'phone', 'first_name', 'last_name', 'role', 'plan', 
            'plan_expiry', 'avatar', 'username', 'email', 'is_active'
        ]
        read_only_fields = ['id', 'username', 'is_active']


class HsCodeSerializer(serializers.ModelSerializer):
    class Meta:
        model = HsCode
        fields = '__all__'


class ClassificationRulingSerializer(serializers.ModelSerializer):
    class Meta:
        model = ClassificationRuling
        fields = '__all__'


class OptimizationTipSerializer(serializers.ModelSerializer):
    class Meta:
        model = OptimizationTip
        fields = '__all__'


class ValidationIssueSerializer(serializers.ModelSerializer):
    class Meta:
        model = ValidationIssue
        fields = '__all__'


class CalculationResultSerializer(serializers.ModelSerializer):
    class Meta:
        model = CalculationResult
        fields = '__all__'


class PriceRiskAnalysisSerializer(serializers.ModelSerializer):
    class Meta:
        model = PriceRiskAnalysis
        fields = '__all__'


class ProductItemSerializer(serializers.ModelSerializer):
    calculation = CalculationResultSerializer(read_only=True)
    price_risk_analysis = PriceRiskAnalysisSerializer(read_only=True)
    validation_issues = ValidationIssueSerializer(many=True, read_only=True)

    class Meta:
        model = ProductItem
        fields = '__all__'
        read_only_fields = ['id', 'user', 'created_at', 'updated_at']


class DeclarationSerializer(serializers.ModelSerializer):
    products = ProductItemSerializer(many=True)
    validation_issues = ValidationIssueSerializer(many=True, read_only=True)
    audit = serializers.SerializerMethodField()

    class Meta:
        model = Declaration
        fields = '__all__'
        read_only_fields = ['id', 'user', 'created_at', 'updated_at']

    def get_audit(self, obj):
        try:
            audit = obj.audit
            return {
                'id': audit.id,
                'score': audit.score,
                'risk_level': audit.risk_level,
                'summary': audit.summary,
                'created_at': audit.created_at
            }
        except AuditResult.DoesNotExist:
            return None

    def create(self, validated_data):
        products_data = validated_data.pop('products', [])
        declaration = Declaration.objects.create(**validated_data)
        
        for product_data in products_data:
            product = ProductItem.objects.create(user=declaration.user, **product_data)
            declaration.products.add(product)
        
        return declaration

    def update(self, instance, validated_data):
        products_data = validated_data.pop('products', None)
        
        # Update declaration fields
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        
        # Update products if provided
        if products_data is not None:
            instance.products.clear()
            for product_data in products_data:
                product = ProductItem.objects.create(user=instance.user, **product_data)
                instance.products.add(product)
        
        return instance


class AuditResultSerializer(serializers.ModelSerializer):
    issues = ValidationIssueSerializer(many=True, read_only=True)

    class Meta:
        model = AuditResult
        fields = '__all__'


class HsCodePredictionSerializer(serializers.ModelSerializer):
    class Meta:
        model = HsCodePrediction
        fields = '__all__'


class ChatMessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ChatMessage
        fields = '__all__'
        read_only_fields = ['id', 'user', 'timestamp']


class DecisionTreeQuestionSerializer(serializers.ModelSerializer):
    class Meta:
        model = DecisionTreeQuestion
        fields = '__all__'


class IncotermRecommendationSerializer(serializers.ModelSerializer):
    class Meta:
        model = IncotermRecommendation
        fields = '__all__'


class TradeRouteOptionSerializer(serializers.ModelSerializer):
    class Meta:
        model = TradeRouteOption
        fields = '__all__'


class CurrencyRateSerializer(serializers.ModelSerializer):
    class Meta:
        model = CurrencyRate
        fields = '__all__'


class HsCodePassportSerializer(serializers.ModelSerializer):
    class Meta:
        model = HsCodePassport
        fields = '__all__'
        read_only_fields = ['user', 'created_at']

    def create(self, validated_data):
        user = self.context['request'].user
        passport = HsCodePassport.objects.create(user=user, **validated_data)
        return passport


class UserTemplateSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserTemplate
        fields = '__all__'
        read_only_fields = ['id', 'user', 'created_at', 'updated_at']


    def create(self, validated_data):
        user = self.context['request'].user
        template = UserTemplate.objects.create(user=user, **validated_data)
        return template


class DocumentGenerationSerializer(serializers.ModelSerializer):
    class Meta:
        model = DocumentGeneration
        fields = '__all__'
        read_only_fields = ['id', 'user', 'created_at']

    def create(self, validated_data):
        user = self.context['request'].user
        document = DocumentGeneration.objects.create(user=user, **validated_data)
        return document


class ClassificationSearchSerializer(serializers.ModelSerializer):
    class Meta:
        model = ClassificationSearch
        fields = '__all__'
        read_only_fields = ['user', 'created_at']

    def create(self, validated_data):
        user = self.context['request'].user
        search = ClassificationSearch.objects.create(user=user, **validated_data)
        return search