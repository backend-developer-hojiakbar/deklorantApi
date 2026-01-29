from rest_framework import generics, status, viewsets
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.views import APIView
from django.contrib.auth import authenticate
from django.contrib.auth.hashers import make_password
from django.shortcuts import get_object_or_404
from django.db.models import Q
from decimal import Decimal
from datetime import datetime
from .models import (
    User, HsCode, ClassificationRuling, OptimizationTip, ProductItem, ValidationIssue,
    Declaration, AuditResult, CalculationResult, HsCodePrediction, PriceRiskAnalysis,
    ChatMessage, DecisionTreeQuestion, IncotermRecommendation, TradeRouteOption, CurrencyRate,
    HsCodePassport, UserTemplate, DocumentGeneration, ClassificationSearch
)
from .serializers import (
    UserSerializer, HsCodeSerializer, ClassificationRulingSerializer, OptimizationTipSerializer,
    ProductItemSerializer, ValidationIssueSerializer, DeclarationSerializer, AuditResultSerializer,
    CalculationResultSerializer, HsCodePredictionSerializer, PriceRiskAnalysisSerializer,
    ChatMessageSerializer, DecisionTreeQuestionSerializer, IncotermRecommendationSerializer,
    TradeRouteOptionSerializer, CurrencyRateSerializer,
    HsCodePassportSerializer, UserTemplateSerializer, DocumentGenerationSerializer, ClassificationSearchSerializer
)
from .utils import calculate_customs_duties, perform_risk_analysis, get_hs_code_details, search_hs_codes_semantic

from rest_framework.authtoken.models import Token

class UserRegistrationView(generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [AllowAny]

    def post(self, request):
        data = request.data
        # Check if user with phone already exists
        if User.objects.filter(phone=data.get('phone')).exists():
            return Response({'error': 'User with this phone already exists'}, 
                          status=status.HTTP_400_BAD_REQUEST)
        
        # Create user
        user = User.objects.create(
            username=data.get('phone'),
            phone=data.get('phone'),
            first_name=data.get('first_name', ''),
            last_name=data.get('last_name', ''),
            password=make_password(data.get('password'))
        )
        
        # Create token for the new user
        token, created = Token.objects.get_or_create(user=user)
        
        serializer = UserSerializer(user)
        return Response({
            'user': serializer.data,
            'token': token.key
        }, status=status.HTTP_201_CREATED)

class UserLoginView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        phone = request.data.get('phone')
        password = request.data.get('password')

        if not phone or not password:
            return Response({'error': 'Phone and password required'}, 
                          status=status.HTTP_400_BAD_REQUEST)

        user = authenticate(username=phone, password=password)
        if user:
            # Get or create token for the user
            token, created = Token.objects.get_or_create(user=user)
            serializer = UserSerializer(user)
            return Response({
                'user': serializer.data,
                'token': token.key
            }, status=status.HTTP_200_OK)
        
        return Response({'error': 'Invalid credentials'}, status=status.HTTP_401_UNAUTHORIZED)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_dashboard_data(request):
    """
    Get dashboard analytics data for the authenticated user
    Returns KPIs, recent activity, and other dashboard metrics
    """
    user = request.user
    
    # Get recent declarations for the user
    recent_declarations = Declaration.objects.filter(user=user).order_by('-created_at')[:5]
    
    # Get recent calculations
    recent_calculations = CalculationResult.objects.filter(
        product_item__user=user
    ).order_by('-calculated_at')[:5]
    
    # Get recent HS code searches
    recent_searches = ClassificationSearch.objects.filter(user=user).order_by('-created_at')[:5]
    
    # Get dashboard KPIs
    total_declarations = Declaration.objects.filter(user=user).count()
    total_products = ProductItem.objects.filter(user=user).count()
    pending_declarations = Declaration.objects.filter(user=user, status='QORALAMA').count()
    
    # Get financial data for chart (last 6 months)
    from datetime import datetime, timedelta
    six_months_ago = datetime.now() - timedelta(days=180)
    monthly_data = []
    
    for i in range(6):
        month_start = six_months_ago + timedelta(days=i*30)
        month_end = month_start + timedelta(days=30)
        
        # Get declarations for this month
        month_declarations = Declaration.objects.filter(
            user=user,
            created_at__gte=month_start,
            created_at__lte=month_end
        )
        
        # Calculate import value and duties
        month_total_value = sum(float(d.total_value) for d in month_declarations)
        
        # Calculate duties from related products
        month_duties = 0
        for decl in month_declarations:
            for product in decl.products.all():
                if hasattr(product, 'calculation'):
                    month_duties += float(product.calculation.customs_duty)
        
        # Month name for chart
        month_name = month_start.strftime('%b')
        
        monthly_data.append({
            'name': month_name,
            'value': month_total_value,
            'duty': month_duties,
            'speed': 24 - i * 2  # Simulated speed improvement
        })
    
    # Get urgent tasks
    urgent_tasks = []
    pending_declarations_db = Declaration.objects.filter(user=user, status='QORALAMA')[:3]
    for decl in pending_declarations_db:
        urgent_tasks.append({
            'id': decl.id,
            'type': 'Draft',
            'msg': f'Deklaratsiya to\'ldirilmadi',
            'action': 'Tahrirlash',
            'date': decl.created_at.strftime('%d-%m-%Y, %H:%M')
        })
    
    # Get currency rates
    latest_rates = CurrencyRate.objects.order_by('-date')[:4]
    
    dashboard_data = {
        'kpis': {
            'total_declarations': total_declarations,
            'total_products': total_products,
            'pending_declarations': pending_declarations,
            'completed_declarations': total_declarations - pending_declarations,
        },
        'monthly_data': monthly_data,
        'recent_activity': {
            'declarations': DeclarationSerializer(recent_declarations, many=True).data,
            'calculations': CalculationResultSerializer(recent_calculations, many=True).data,
            'searches': ClassificationSearchSerializer(recent_searches, many=True).data,
        },
        'urgent_tasks': urgent_tasks,
        'currency_rates': CurrencyRateSerializer(latest_rates, many=True).data,
    }
    
    return Response(dashboard_data, status=status.HTTP_200_OK)


class HsCodeViewSet(viewsets.ModelViewSet):
    queryset = HsCode.objects.all()
    serializer_class = HsCodeSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        queryset = HsCode.objects.all()
        # Search by code or description
        search = self.request.query_params.get('search', None)
        if search:
            queryset = queryset.filter(
                Q(code__icontains=search) | 
                Q(description_uz__icontains=search) | 
                Q(description_ru__icontains=search)
            )
        return queryset


class ClassificationRulingViewSet(viewsets.ModelViewSet):
    queryset = ClassificationRuling.objects.all()
    serializer_class = ClassificationRulingSerializer
    permission_classes = [IsAuthenticated]


class OptimizationTipViewSet(viewsets.ModelViewSet):
    queryset = OptimizationTip.objects.all()
    serializer_class = OptimizationTipSerializer
    permission_classes = [IsAuthenticated]


class ProductItemViewSet(viewsets.ModelViewSet):
    queryset = ProductItem.objects.all()
    serializer_class = ProductItemSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return ProductItem.objects.filter(user=self.request.user)


class ValidationIssueViewSet(viewsets.ModelViewSet):
    queryset = ValidationIssue.objects.all()
    serializer_class = ValidationIssueSerializer
    permission_classes = [IsAuthenticated]


class DeclarationViewSet(viewsets.ModelViewSet):
    queryset = Declaration.objects.all()
    serializer_class = DeclarationSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Declaration.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class AuditResultViewSet(viewsets.ModelViewSet):
    queryset = AuditResult.objects.all()
    serializer_class = AuditResultSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return AuditResult.objects.filter(declaration__user=self.request.user)


class CalculationResultViewSet(viewsets.ModelViewSet):
    queryset = CalculationResult.objects.all()
    serializer_class = CalculationResultSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return CalculationResult.objects.filter(product_item__user=self.request.user)


class HsCodePredictionViewSet(viewsets.ModelViewSet):
    queryset = HsCodePrediction.objects.all()
    serializer_class = HsCodePredictionSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return HsCodePrediction.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class ChatMessageViewSet(viewsets.ModelViewSet):
    queryset = ChatMessage.objects.all()
    serializer_class = ChatMessageSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return ChatMessage.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class DecisionTreeQuestionViewSet(viewsets.ModelViewSet):
    queryset = DecisionTreeQuestion.objects.all()
    serializer_class = DecisionTreeQuestionSerializer
    permission_classes = [IsAuthenticated]


class IncotermRecommendationViewSet(viewsets.ModelViewSet):
    queryset = IncotermRecommendation.objects.all()
    serializer_class = IncotermRecommendationSerializer
    permission_classes = [IsAuthenticated]


class TradeRouteOptionViewSet(viewsets.ModelViewSet):
    queryset = TradeRouteOption.objects.all()
    serializer_class = TradeRouteOptionSerializer
    permission_classes = [IsAuthenticated]


class CurrencyRateViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = CurrencyRate.objects.all()
    serializer_class = CurrencyRateSerializer
    permission_classes = [AllowAny]

    def get_queryset(self):
        # Return latest rates for each currency
        latest_date = CurrencyRate.objects.order_by('-date').first()
        if latest_date:
            return CurrencyRate.objects.filter(date=latest_date.date)
        return CurrencyRate.objects.none()



class HsCodePassportViewSet(viewsets.ModelViewSet):
    queryset = HsCodePassport.objects.all()
    serializer_class = HsCodePassportSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return HsCodePassport.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class UserTemplateViewSet(viewsets.ModelViewSet):
    queryset = UserTemplate.objects.all()
    serializer_class = UserTemplateSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        # Users can access their own templates and public templates
        return UserTemplate.objects.filter(
            Q(user=self.request.user) | Q(is_public=True)
        )

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class DocumentGenerationViewSet(viewsets.ModelViewSet):
    queryset = DocumentGeneration.objects.all()
    serializer_class = DocumentGenerationSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return DocumentGeneration.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class ClassificationSearchViewSet(viewsets.ModelViewSet):
    queryset = ClassificationSearch.objects.all()
    serializer_class = ClassificationSearchSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return ClassificationSearch.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


# Custom API views for specific functionality
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def calculate_customs_duties_api(request):
    """
    Calculate customs duties for a given product
    Expected data: {
        'hs_code': 'string',
        'price': 'decimal',
        'currency': 'string',
        'origin': 'string',
        'has_certificate': 'boolean',
        'mode': 'string',
        'product_type': 'string',
        'engine_volume': 'decimal',
        'manufacture_year': 'int'
    }
    """
    try:
        result = calculate_customs_duties(request.data)
        return Response(result, status=status.HTTP_200_OK)
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def perform_risk_analysis_api(request):
    """
    Perform risk analysis on a product
    Expected data: {
        'product_id': 'int',
        'declared_price': 'decimal',
        'customs_price': 'decimal'
    }
    """
    try:
        result = perform_risk_analysis(request.data)
        return Response(result, status=status.HTTP_200_OK)
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
@permission_classes([AllowAny])
def search_hs_codes_api(request):
    """
    Search HS codes semantically using AI
    Query param: q (search query)
    """
    query = request.query_params.get('q', '')
    if not query:
        return Response({'error': 'Query parameter "q" is required'}, 
                       status=status.HTTP_400_BAD_REQUEST)
    
    try:
        results = search_hs_codes_semantic(query)
        return Response(results, status=status.HTTP_200_OK)
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_hs_code_details_api(request, code):
    """
    Get detailed information about an HS code
    """
    try:
        result = get_hs_code_details(code)
        return Response(result, status=status.HTTP_200_OK)
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def audit_declaration_api(request, declaration_id):
    """
    Perform deep audit on a declaration
    """
    declaration = get_object_or_404(Declaration, id=declaration_id, user=request.user)
    
    # This would typically involve complex logic and possibly AI integration
    # For now, returning a mock response
    audit_result = {
        'score': 85,
        'risk_level': 'MEDIUM',
        'summary': 'Declaration appears to be in good order with minor issues identified',
        'issues': [
            {
                'type': 'WARNING',
                'message': 'Price seems slightly below market average',
                'field': 'price',
                'suggestion': 'Consider providing additional documentation for price justification'
            }
        ]
    }
    
    # Create or update audit result in database
    audit, created = AuditResult.objects.update_or_create(
        declaration=declaration,
        defaults={
            'score': audit_result['score'],
            'risk_level': audit_result['risk_level'],
            'summary': audit_result['summary']
        }
    )
    
    # Add issues to the audit
    for issue_data in audit_result['issues']:
        issue, _ = ValidationIssue.objects.get_or_create(
            type=issue_data['type'],
            message=issue_data['message'],
            field=issue_data.get('field'),
            suggestion=issue_data.get('suggestion')
        )
        audit.issues.add(issue)
    
    serializer = AuditResultSerializer(audit)
    return Response(serializer.data, status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_declaration_summary(request, declaration_id):
    """
    Get a summary of a declaration with all calculations
    """
    declaration = get_object_or_404(Declaration, id=declaration_id, user=request.user)
    
    total_customs_duty = sum(
        product.calculation.customs_duty if hasattr(product, 'calculation') else 0
        for product in declaration.products.all()
    )
    
    total_vat = sum(
        product.calculation.vat if hasattr(product, 'calculation') else 0
        for product in declaration.products.all()
    )
    
    total_excise = sum(
        product.calculation.excise if hasattr(product, 'calculation') else 0
        for product in declaration.products.all()
    )
    
    total_fee = sum(
        product.calculation.customs_fee if hasattr(product, 'calculation') else 0
        for product in declaration.products.all()
    )
    
    summary = {
        'declaration_id': declaration.id,
        'contract_number': declaration.contract_number,
        'partner_name': declaration.partner_name,
        'total_value': float(declaration.total_value),
        'total_customs_duty': float(total_customs_duty),
        'total_vat': float(total_vat),
        'total_excise': float(total_excise),
        'total_fee': float(total_fee),
        'total_payments': float(total_customs_duty + total_vat + total_excise + total_fee),
        'status': declaration.status,
        'product_count': declaration.products.count()
    }
    
    return Response(summary, status=status.HTTP_200_OK)


class ExportXmlView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, declaration_id):
        """
        Export declaration data in XML format for customs system
        """
        declaration = get_object_or_404(Declaration, id=declaration_id, user=request.user)
        
        # Generate XML content similar to frontend
        import xml.etree.ElementTree as ET
        from xml.dom import minidom
        
        root = ET.Element("GTDDocument")
        root.set("xmlns", "http://www.customs.uz/gtd/2024")
        
        # Header
        header = ET.SubElement(root, "Header")
        doc_id = ET.SubElement(header, "DocumentID")
        doc_id.text = declaration.id
        export_date = ET.SubElement(header, "ExportDate")
        export_date.text = datetime.now().isoformat()
        software = ET.SubElement(header, "Software")
        software.text = "AI-TradeAssist v2.0 (Autonomous)"
        
        # Declaration
        decl = ET.SubElement(root, "Declaration")
        
        contract = ET.SubElement(decl, "Contract")
        contract_num = ET.SubElement(contract, "Number")
        contract_num.text = declaration.contract_number
        contract_date = ET.SubElement(contract, "Date")
        contract_date.text = str(declaration.invoice_date)
        currency_code = ET.SubElement(contract, "CurrencyCode")
        currency_code.text = declaration.currency
        total_amount = ET.SubElement(contract, "TotalAmount")
        total_amount.text = str(declaration.total_value)
        partner = ET.SubElement(contract, "Partner")
        partner.text = declaration.partner_name
        
        # Goods List
        goods_list = ET.SubElement(decl, "GoodsList")
        for idx, product in enumerate(declaration.products.all(), 1):
            good_item = ET.SubElement(goods_list, "GoodItem")
            good_item.set("SerialNumber", str(idx))
            
            description = ET.SubElement(good_item, "Description")
            description.text = f"{product.name} - {product.description or ''}"
            hs_code_elem = ET.SubElement(good_item, "HSCode")
            hs_code_elem.text = product.hs_code
            weight_netto = ET.SubElement(good_item, "WeightNetto")
            weight_netto.text = str(product.netto)
            weight_brutto = ET.SubElement(good_item, "WeightBrutto")
            weight_brutto.text = str(product.brutto)
            invoice_value = ET.SubElement(good_item, "InvoiceValue")
            invoice_value.text = str(product.price)
            
            # Add calculation if available
            if hasattr(product, 'calculation'):
                customs_value = ET.SubElement(good_item, "CustomsValue")
                customs_value.text = str(product.calculation.total * 0.8)  # Approximation
            
            # Required certificates
            req_certs = ET.SubElement(good_item, "RequiredCertificates")
            for cert in product.required_certificates:
                cert_type = ET.SubElement(req_certs, "CertificateType")
                cert_type.text = cert
        
        # Calculated Payments
        calc_payments = ET.SubElement(decl, "CalculatedPayments")
        total_payments = ET.SubElement(calc_payments, "TotalPayments")
        total_payments.text = str(sum(
            p.calculation.total if hasattr(p, 'calculation') else 0
            for p in declaration.products.all()
        ))
        
        # Convert to string with proper formatting
        rough_string = ET.tostring(root, 'utf-8')
        reparsed = minidom.parseString(rough_string)
        xml_string = reparsed.toprettyxml(indent="  ")
        
        # Remove extra blank lines
        xml_string = '\n'.join([line for line in xml_string.split('\n') if line.strip()])
        
        # Return as XML response
        from django.http import HttpResponse
        response = HttpResponse(xml_string, content_type='application/xml')
        response['Content-Disposition'] = f'attachment; filename="AI-DECL-{declaration.id}.xml"'
        return response


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def store_hs_code_search(request):
    """
    Store HS code classification search in database for tracking
    Expected data: {
        'search_query': 'string',
        'results_count': 'number'
    }
    """
    try:
        serializer = ClassificationSearchSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            search = serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def store_hs_code_passport(request):
    """
    Store HS code passport information from AI in database
    Expected data: {
        'code': 'string',
        'description': 'string',
        'description_ru': 'string',
        'duty_rate': 'number',
        'vat_rate': 'number',
        'excise_rate': 'number',
        'required_certs': 'array',
        'sources': 'array'
    }
    """
    try:
        serializer = HsCodePassportSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            passport = serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def store_document_generation(request):
    """
    Store document generation activity in database
    Expected data: {
        'document_type': 'string',
        'content': 'object',
        'generated_data': 'object',
        'template_used': 'string'  # optional
    }
    """
    try:
        serializer = DocumentGenerationSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            document = serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_user_templates(request):
    """
    Get templates available to the user (own + public)
    """
    templates = UserTemplate.objects.filter(
        Q(user=request.user) | Q(is_public=True)
    )
    serializer = UserTemplateSerializer(templates, many=True)
    return Response(serializer.data, status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def upload_user_template(request):
    """
    Upload a new template for the user
    Expected data: {
        'name': 'string',
        'description': 'string',
        'template_type': 'string',
        'template_data': 'object',
        'is_public': 'boolean'
    }
    """
    try:
        serializer = UserTemplateSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            template = serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
