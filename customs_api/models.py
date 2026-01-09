from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils import timezone
from decimal import Decimal


class User(AbstractUser):
    ROLE_CHOICES = [
        ('admin', 'Admin'),
        ('user', 'User'),
    ]
    
    PLAN_CHOICES = [
        ('free', 'Free'),
        ('pro_6', 'Pro 6 Months'),
        ('pro_9', 'Pro 9 Months'),
        ('pro_12', 'Pro 12 Months'),
    ]
    
    phone = models.CharField(max_length=15, unique=True)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='user')
    plan = models.CharField(max_length=20, choices=PLAN_CHOICES, default='free')
    plan_expiry = models.DateTimeField(null=True, blank=True)
    avatar = models.URLField(null=True, blank=True)
    
    USERNAME_FIELD = 'phone'
    REQUIRED_FIELDS = ['username']
    
    def __str__(self):
        return f"{self.phone} ({self.first_name} {self.last_name})"


class HsCode(models.Model):
    """HS Code database with rates and requirements"""
    code = models.CharField(max_length=20, unique=True)
    description_uz = models.TextField()
    description_ru = models.TextField(blank=True, null=True)
    hierarchy = models.JSONField(default=list)  # Section -> Chapter -> Heading
    duty_rate = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal('0.00'))  # %
    vat_rate = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal('0.00'))  # %
    excise_rate = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal('0.00'))  # %
    is_sanctioned = models.BooleanField(default=False)
    required_certs = models.JSONField(default=list)
    history = models.TextField(blank=True)  # User's usage history
    cis_hint = models.CharField(max_length=500, blank=True, null=True)  # CIS Compatibility Warning
    version_status = models.CharField(max_length=20, default='ACTIVE')  # ACTIVE/DEPRECATED
    sources = models.JSONField(default=list, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.code} - {self.description_uz[:50]}..."

    class Meta:
        verbose_name = "HS Code"
        verbose_name_plural = "HS Codes"


class ClassificationRuling(models.Model):
    """Classification ruling records"""
    id = models.CharField(max_length=50, unique=True, primary_key=True)
    date = models.DateField()
    summary = models.TextField()
    official_doc_url = models.URLField()
    outcome_code = models.CharField(max_length=20)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.id} - {self.outcome_code}"


class OptimizationTip(models.Model):
    """Optimization tips for HS codes"""
    alternative_code = models.CharField(max_length=20)
    description = models.TextField()
    duty_rate = models.DecimalField(max_digits=5, decimal_places=2)
    savings_potential = models.CharField(max_length=100)
    conditions = models.TextField()  # e.g. "Must be for laptop use"
    hs_code = models.ForeignKey(HsCode, on_delete=models.CASCADE, related_name='optimization_tips')

    def __str__(self):
        return f"{self.alternative_code} - {self.description[:30]}..."


class ProductItem(models.Model):
    """Product item in a declaration"""
    UNIT_CHOICES = [
        ('kg', 'Kilogram'),
        ('m2', 'Square Meter'),
        ('dona', 'Piece'),
        ('liter', 'Liter'),
        ('set', 'Set'),
    ]
    
    ORIGIN_CHOICES = [
        ('CIS', 'CIS Countries'),
        ('VN', 'Vietnam'),
        ('OTHER', 'Other Countries'),
    ]
    
    RISK_LEVEL_CHOICES = [
        ('LOW', 'Low'),
        ('MEDIUM', 'Medium'),
        ('HIGH', 'High'),
    ]

    id = models.CharField(max_length=50, unique=True, primary_key=True)
    name = models.CharField(max_length=200)  # Tovar nomi
    description = models.TextField(blank=True, null=True)  # Bojxona uchun to'liq tavsif (31-grafa)
    hs_code = models.CharField(max_length=20)  # This might not exist in DB yet
    quantity = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    unit = models.CharField(max_length=20, choices=UNIT_CHOICES, default='dona')
    netto = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    brutto = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    price = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    currency = models.CharField(max_length=3, default='USD')
    origin_country = models.CharField(max_length=100, blank=True, null=True)  # Kelib chiqish mamlakati
    package_type = models.CharField(max_length=100, blank=True, null=True)  # O'rash turi
    manufacturer = models.CharField(max_length=200, blank=True, null=True)  # Ishlab chiqaruvchi

    # AI Attributes
    confidence_score = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    risk_alert = models.CharField(max_length=500, blank=True, null=True)
    risk_level = models.CharField(max_length=10, choices=RISK_LEVEL_CHOICES, blank=True, null=True)
    required_certificates = models.JSONField(default=list)  # Talab etiladigan sertifikatlar

    # Relations
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='product_items')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.name} - {self.hs_code}"

    class Meta:
        verbose_name = "Product Item"
        verbose_name_plural = "Product Items"


class ValidationIssue(models.Model):
    """Validation issues for declarations"""
    TYPE_CHOICES = [
        ('ERROR', 'Error'),
        ('WARNING', 'Warning'),
        ('INFO', 'Info'),
    ]

    type = models.CharField(max_length=10, choices=TYPE_CHOICES)
    message = models.TextField()
    field = models.CharField(max_length=100, blank=True, null=True)
    suggestion = models.TextField(blank=True, null=True)  # AI suggestion to fix
    product_item = models.ForeignKey(ProductItem, on_delete=models.CASCADE, related_name='validation_issues', null=True, blank=True)

    def __str__(self):
        return f"{self.type}: {self.message[:50]}..."


class Declaration(models.Model):
    """Customs declaration"""
    STATUS_CHOICES = [
        ('QORALAMA', 'Draft'),
        ('KUTILMOQDA', 'Pending'),
        ('TASDIQLANGAN', 'Approved'),
        ('RAD_ETILGAN', 'Rejected'),
    ]
    
    MODE_CHOICES = [
        ('IM_40', 'IM-40 (Erkin muomala)'),
        ('IM_70', 'IM-70 (Bojxona ombori)'),
        ('IM_74', 'IM-74 (Bojxona hududida qayta ishlash)'),
        ('EK_10', 'EK-10 (Eksport)'),
    ]

    id = models.CharField(max_length=50, unique=True, primary_key=True)
    contract_number = models.CharField(max_length=100)
    contract_date = models.DateField(null=True, blank=True)
    invoice_number = models.CharField(max_length=100, blank=True, null=True)
    invoice_date = models.DateField()
    partner_name = models.CharField(max_length=200)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='QORALAMA')
    mode = models.CharField(max_length=20, choices=MODE_CHOICES, default='IM_40')  # Customs Mode
    products = models.ManyToManyField(ProductItem, related_name='declarations')
    total_value = models.DecimalField(max_digits=15, decimal_places=2, default=Decimal('0.00'))
    currency = models.CharField(max_length=3, default='USD')
    transport_type = models.CharField(max_length=50, blank=True, null=True)  # Avto, Avia, Temir yo'l
    transport_number = models.CharField(max_length=100, blank=True, null=True)  # CMR / Truck ID

    # Relations
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='declarations')
    validation_issues = models.ManyToManyField(ValidationIssue, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Declaration {self.id} - {self.partner_name}"

    class Meta:
        verbose_name = "Declaration"
        verbose_name_plural = "Declarations"


class AuditResult(models.Model):
    """Audit result for declarations"""
    RISK_LEVEL_CHOICES = [
        ('LOW', 'Low'),
        ('MEDIUM', 'Medium'),
        ('HIGH', 'High'),
        ('CRITICAL', 'Critical'),
    ]

    declaration = models.OneToOneField(Declaration, on_delete=models.CASCADE, related_name='audit')
    score = models.IntegerField()  # 0-100
    risk_level = models.CharField(max_length=10, choices=RISK_LEVEL_CHOICES)
    summary = models.TextField()
    issues = models.ManyToManyField(ValidationIssue, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Audit for {self.declaration.id} - {self.risk_level}"


class CalculationResult(models.Model):
    """Calculation result for customs duties"""
    product_item = models.OneToOneField(ProductItem, on_delete=models.CASCADE, related_name='calculation')
    customs_duty = models.DecimalField(max_digits=15, decimal_places=2, default=Decimal('0.00'))  # Boj
    vat = models.DecimalField(max_digits=15, decimal_places=2, default=Decimal('0.00'))  # QQS
    customs_fee = models.DecimalField(max_digits=15, decimal_places=2, default=Decimal('0.00'))  # Yig'im (0.2%)
    excise = models.DecimalField(max_digits=15, decimal_places=2, default=Decimal('0.00'))  # Aksiz
    total = models.DecimalField(max_digits=15, decimal_places=2, default=Decimal('0.00'))
    currency = models.CharField(max_length=3, default='UZS')
    calculated_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Calculation for {self.product_item.name}"


class HsCodePrediction(models.Model):
    """HS Code prediction from AI"""
    code = models.CharField(max_length=20)
    description = models.TextField()  # UZ (TIF TN)
    description_ru = models.TextField(blank=True, null=True)  # RU (TN VED)
    confidence = models.DecimalField(max_digits=5, decimal_places=2)
    reasoning = models.TextField()
    sources = models.JSONField(default=list, blank=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='hs_predictions')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.code} - {self.confidence}%"


class PriceRiskAnalysis(models.Model):
    """Price risk analysis for products"""
    RISK_LEVEL_CHOICES = [
        ('LOW', 'Low'),
        ('MEDIUM', 'Medium'),
        ('HIGH', 'High'),
    ]

    product_item = models.OneToOneField(ProductItem, on_delete=models.CASCADE, related_name='price_risk_analysis')
    risk_level = models.CharField(max_length=10, choices=RISK_LEVEL_CHOICES)
    average_price = models.DecimalField(max_digits=12, decimal_places=2)
    message = models.TextField()
    required_documents = models.JSONField(default=list)
    analyzed_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Price Risk Analysis for {self.product_item.name}"


class ChatMessage(models.Model):
    """Chat messages for AI assistant"""
    ROLE_CHOICES = [
        ('user', 'User'),
        ('ai', 'AI'),
        ('system', 'System'),
    ]

    id = models.CharField(max_length=50, unique=True, primary_key=True)
    role = models.CharField(max_length=10, choices=ROLE_CHOICES)
    content = models.TextField()
    timestamp = models.DateTimeField(default=timezone.now)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='chat_messages')
    is_thinking = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.role}: {self.content[:50]}..."


class DecisionTreeQuestion(models.Model):
    """Decision tree questions for classification"""
    id = models.CharField(max_length=50, unique=True, primary_key=True)
    question = models.TextField()
    options = models.JSONField(default=list)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.question[:50]}..."


class IncotermRecommendation(models.Model):
    """Incoterm recommendations"""
    code = models.CharField(max_length=10)
    name = models.CharField(max_length=100)
    recommendation_reason = models.TextField()
    risk_transfer = models.TextField()
    cost_responsibility = models.TextField()
    best_for = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.code} - {self.name}"


class TradeRouteOption(models.Model):
    """Trade route options"""
    RISK_CHOICES = [
        ('LOW', 'Low'),
        ('MEDIUM', 'Medium'),
        ('HIGH', 'High'),
    ]

    id = models.CharField(max_length=50, unique=True, primary_key=True)
    method = models.CharField(max_length=100)
    description = models.TextField()
    transit_time = models.CharField(max_length=50)
    estimated_cost = models.DecimalField(max_digits=12, decimal_places=2)
    savings = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    risk = models.CharField(max_length=10, choices=RISK_CHOICES)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.method} - {self.estimated_cost}"


class CurrencyRate(models.Model):
    """Currency rates from Central Bank"""
    code = models.CharField(max_length=3)  # USD, EUR, etc.
    name = models.CharField(max_length=100)
    rate = models.DecimalField(max_digits=10, decimal_places=4)
    diff = models.DecimalField(max_digits=10, decimal_places=4, default=Decimal('0.00'))
    trend = models.CharField(max_length=10, default='stable')  # up, down, stable
    date = models.DateField()
    
    class Meta:
        unique_together = ('code', 'date')
        ordering = ['-date', 'code']

    def __str__(self):
        return f"{self.code} - {self.rate}"


class HsCodePassport(models.Model):
    """HS Code passport information from AI"""
    code = models.CharField(max_length=20)
    description = models.TextField()  # UZ
    description_ru = models.TextField(blank=True, null=True)  # RU
    hierarchy = models.JSONField(default=list)  # Section -> Chapter -> Heading
    duty_rate = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal('0.00'))  # %
    vat_rate = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal('0.00'))  # %
    excise_rate = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal('0.00'))  # %
    is_sanctioned = models.BooleanField(default=False)
    required_certs = models.JSONField(default=list)
    cis_hint = models.CharField(max_length=500, blank=True, null=True)
    version_status = models.CharField(max_length=20, default='ACTIVE')
    sources = models.JSONField(default=list, blank=True)
    
    # Relations
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='hs_code_passports')
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.code} - {self.description[:50]}..."


class UserTemplate(models.Model):
    """User-uploaded templates for document generation"""
    TEMPLATE_TYPES = [
        ('INVOICE', 'Invoice'),
        ('PACKING_LIST', 'Packing List'),
        ('CERTIFICATE', 'Certificate'),
        ('CONTRACT', 'Contract'),
        ('OTHER', 'Other'),
    ]
    
    id = models.CharField(max_length=50, unique=True, primary_key=True)
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True, null=True)
    template_type = models.CharField(max_length=20, choices=TEMPLATE_TYPES)
    template_data = models.JSONField(default=dict)  # Store template layout and fields
    file_url = models.URLField(blank=True, null=True)  # URL to uploaded file
    is_public = models.BooleanField(default=False)  # Whether other users can use this template
    
    # Relations
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='templates')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.name} - {self.user.phone}"


class DocumentGeneration(models.Model):
    """Record of document generation activities"""
    DOCUMENT_TYPES = [
        ('INVOICE', 'Invoice'),
        ('PACKING_LIST', 'Packing List'),
        ('CERTIFICATE', 'Certificate'),
        ('CONTRACT', 'Contract'),
        ('CUSTOM', 'Custom'),
    ]
    
    id = models.CharField(max_length=50, unique=True, primary_key=True)
    document_type = models.CharField(max_length=20, choices=DOCUMENT_TYPES)
    content = models.JSONField(default=dict)  # Store the generated document content
    generated_data = models.JSONField(default=dict)  # Store data used for generation
    template_used = models.ForeignKey(UserTemplate, on_delete=models.SET_NULL, null=True, blank=True, related_name='document_generations')
    
    # Relations
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='document_generations')
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.document_type} - {self.user.phone}"


class ClassificationSearch(models.Model):
    """Record of HS code classification searches"""
    search_query = models.TextField()
    results_count = models.IntegerField(default=0)
    
    # Relations
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='classification_searches')
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.search_query[:30]}... - {self.user.phone}"