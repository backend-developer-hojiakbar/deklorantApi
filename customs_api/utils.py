from decimal import Decimal
from .models import HsCode, ProductItem, CurrencyRate
import random
import requests
from datetime import datetime


def calculate_customs_duties(data):
    """
    Calculate customs duties based on product data
    """
    # Extract parameters
    hs_code = data.get('hs_code', '')
    price = Decimal(str(data.get('price', 0)))
    currency = data.get('currency', 'USD')
    origin = data.get('origin', 'OTHER')
    has_certificate = data.get('has_certificate', False)
    mode = data.get('mode', 'IM_40')
    product_type = data.get('product_type', 'GENERAL')
    engine_volume = Decimal(str(data.get('engine_volume', 0)))
    manufacture_year = data.get('manufacture_year', datetime.now().year)
    
    # Get exchange rate
    try:
        rate_obj = CurrencyRate.objects.filter(code=currency).latest('date')
        ex_rate = Decimal(str(rate_obj.rate))
    except CurrencyRate.DoesNotExist:
        # Default rate if not found
        ex_rate = Decimal('12850.00')  # USD default
    
    # Convert to UZS
    price_uzs = price * ex_rate
    
    # Initialize rates
    duty_rate = Decimal('10.00')  # Default 10%
    vat_rate = Decimal('12.00')  # Default 12%
    excise_rate = Decimal('0.00')  # Default 0%
    customs_fee_rate = Decimal('0.20')  # 0.2%
    
    # Calculate duties based on product type and other factors
    calculated_duty = Decimal('0.00')
    calculated_excise = Decimal('0.00')
    calculated_vat = Decimal('0.00')
    calculated_fee = Decimal('0.00')
    
    # Special handling for automobiles
    if product_type == 'AUTO':
        current_year = datetime.now().year
        age = current_year - manufacture_year
        
        # Electric vehicles
        if hs_code.startswith('870380'):  # Electric cars
            duty_rate = Decimal('0.00')
            excise_rate = Decimal('0.00')
            # VAT might also be 0 for individuals importing EVs
            vat_rate = Decimal('0.00')
        # Petrol/Diesel vehicles
        else:
            if age > 3:  # Old cars (>3 years) have higher rates
                duty_rate = Decimal('40.00')  # Base ad valorem
                # Specific rate calculation (example: $3 per cc)
                specific_rate = engine_volume * Decimal('3.00')
                calculated_duty = max(price_uzs * Decimal('0.40'), specific_rate * ex_rate)
            else:  # New cars
                if engine_volume < 1200:
                    duty_rate = Decimal('15.00')
                elif engine_volume > 3000:
                    duty_rate = Decimal('30.00')
                    excise_rate = Decimal('20.00')  # Luxury tax
                else:
                    duty_rate = Decimal('15.00')
    
    # Apply duty calculation if not already calculated
    if calculated_duty == 0:
        calculated_duty = price_uzs * (duty_rate / 100)
    
    # Special handling for CIS countries with ST-1 certificate
    if origin == 'CIS' and has_certificate and mode == 'IM_40':
        calculated_duty = Decimal('0.00')
        duty_rate = Decimal('0.00')
    
    # Calculate excise (on base of price + duty)
    excise_base = price_uzs + calculated_duty
    calculated_excise = excise_base * (excise_rate / 100)
    
    # Calculate VAT (on base of price + duty + excise)
    vat_base = price_uzs + calculated_duty + calculated_excise
    calculated_vat = vat_base * (vat_rate / 100)
    
    # Calculate customs fee (0.2% of customs value)
    calculated_fee = price_uzs * (customs_fee_rate / 100)
    
    # Export duties for EK-10 mode
    if mode == 'EK_10':  # Export
        calculated_duty = Decimal('0.00')
        calculated_vat = Decimal('0.00')
        calculated_excise = Decimal('0.00')
        calculated_fee = price_uzs * Decimal('0.001')  # Lower fee for exports
    
    # Calculate total
    total = calculated_duty + calculated_excise + calculated_vat + calculated_fee
    
    result = {
        'customs_duty': float(calculated_duty),
        'vat': float(calculated_vat),
        'customs_fee': float(calculated_fee),
        'excise': float(calculated_excise),
        'total': float(total),
        'currency': 'UZS',
        'duty_rate': float(duty_rate),
        'vat_rate': float(vat_rate),
        'excise_rate': float(excise_rate),
        'customs_fee_rate': float(customs_fee_rate)
    }
    
    return result


def perform_risk_analysis(data):
    """
    Perform risk analysis on a product
    """
    product_id = data.get('product_id')
    declared_price = Decimal(str(data.get('declared_price', 0)))
    customs_price = Decimal(str(data.get('customs_price', 0)))
    
    # Calculate price difference
    if customs_price > 0:
        price_diff = ((declared_price - customs_price) / customs_price) * 100
    else:
        price_diff = Decimal('0.00')
    
    # Determine risk level based on price difference
    if abs(price_diff) <= 5:
        risk_level = 'LOW'
        message = 'Declared price is within acceptable range of customs valuation'
        required_docs = ['Commercial Invoice', 'Packing List']
    elif abs(price_diff) <= 20:
        risk_level = 'MEDIUM'
        message = 'Declared price differs significantly from customs valuation, additional documentation required'
        required_docs = ['Commercial Invoice', 'Packing List', 'Proforma Invoice', 'Price Justification Letter']
    else:
        risk_level = 'HIGH'
        message = 'Declared price significantly differs from customs valuation, thorough review required'
        required_docs = [
            'Commercial Invoice', 
            'Packing List', 
            'Proforma Invoice', 
            'Price Justification Letter',
            'Contract with Supplier',
            'Market Price Analysis'
        ]
    
    result = {
        'risk_level': risk_level,
        'average_price': float(customs_price),
        'message': message,
        'required_documents': required_docs,
        'price_difference_percent': float(price_diff),
        'declared_price': float(declared_price),
        'customs_price': float(customs_price)
    }
    
    return result


def search_hs_codes_semantic(query):
    """
    Search HS codes semantically (mock implementation)
    In a real implementation, this would use AI/Gemini API
    """
    # This is a mock implementation - in real app, this would call an AI service
    # For now, return some example results based on the query
    
    # Mock HS codes database (in real app, this would be from actual DB or API)
    mock_hs_codes = {
        'laptop': [
            {'code': '8471301000', 'description': 'Personal computers', 'description_ru': 'Персональные компьютеры', 'confidence': 95, 'reasoning': 'Standard classification for laptops and personal computers', 'sources': []},
            {'code': '8471309000', 'description': 'Other portable computers', 'description_ru': 'Другие портативные компьютеры', 'confidence': 85, 'reasoning': 'Alternative classification for portable computing devices', 'sources': []}
        ],
        'mobile phone': [
            {'code': '8517120000', 'description': 'Mobile telephones', 'description_ru': 'Мобильные телефоны', 'confidence': 98, 'reasoning': 'Standard classification for mobile phones', 'sources': []},
            {'code': '8517629500', 'description': 'Smartphones', 'description_ru': 'Смартфоны', 'confidence': 92, 'reasoning': 'Smartphone classification', 'sources': []}
        ],
        'car': [
            {'code': '8703231981', 'description': 'Cars with spark-ignition internal combustion piston engine', 'description_ru': 'Легковые автомобили с поршневым двигателем внутреннего сгорания', 'confidence': 90, 'reasoning': 'Standard classification for gasoline cars', 'sources': []},
            {'code': '8703801000', 'description': 'Electric cars', 'description_ru': 'Электромобили', 'confidence': 88, 'reasoning': 'Electric vehicle classification', 'sources': []}
        ],
        'textile': [
            {'code': '6101300000', 'description': 'T-shirts', 'description_ru': 'Футболки', 'confidence': 80, 'reasoning': 'Cotton t-shirts classification', 'sources': []},
            {'code': '6203420000', 'description': 'Trousers', 'description_ru': 'Брюки', 'confidence': 75, 'reasoning': 'Cotton trousers classification', 'sources': []}
        ]
    }
    
    # Find closest match based on query
    query_lower = query.lower()
    results = []
    
    for keyword, codes in mock_hs_codes.items():
        if keyword in query_lower or query_lower in keyword:
            results.extend(codes)
            break
    
    # If no direct match, return some general results
    if not results:
        results = [
            {'code': '9999999999', 'description': 'General merchandise', 'description_ru': 'Общие товары', 'confidence': 50, 'reasoning': 'Generic classification when specific code not found', 'sources': []},
            {'code': '8471301000', 'description': 'Electronic equipment', 'description_ru': 'Электронное оборудование', 'confidence': 45, 'reasoning': 'Generic electronic classification', 'sources': []}
        ]
    
    # Limit to top 10 results
    return results[:10]


def get_hs_code_details(code):
    """
    Get detailed information about an HS code (mock implementation)
    In a real implementation, this would fetch from database or API
    """
    try:
        # Try to get from database first
        hs_code_obj = HsCode.objects.get(code=code)
        
        details = {
            'code': hs_code_obj.code,
            'description': hs_code_obj.description_uz,
            'description_ru': hs_code_obj.description_ru,
            'hierarchy': hs_code_obj.hierarchy,
            'duty_rate': float(hs_code_obj.duty_rate),
            'vat_rate': float(hs_code_obj.vat_rate),
            'excise_rate': float(hs_code_obj.excise_rate),
            'is_sanctioned': hs_code_obj.is_sanctioned,
            'required_certs': hs_code_obj.required_certs,
            'rulings': [],  # This would come from ClassificationRuling model
            'optimization': [],  # This would come from OptimizationTip model
            'history': hs_code_obj.history,
            'cis_hint': hs_code_obj.cis_hint,
            'version_status': hs_code_obj.version_status,
            'sources': hs_code_obj.sources
        }
        
        # Add related optimization tips if any
        optimization_tips = hs_code_obj.optimization_tips.all()
        for tip in optimization_tips:
            details['optimization'].append({
                'alternative_code': tip.alternative_code,
                'description': tip.description,
                'duty_rate': float(tip.duty_rate),
                'savings_potential': tip.savings_potential,
                'conditions': tip.conditions
            })
        
        return details
        
    except HsCode.DoesNotExist:
        # Return mock data if not found in DB
        mock_details = {
            'code': code,
            'description': f'HS Code {code} - General merchandise',
            'description_ru': f'HS код {code} - Общие товары',
            'hierarchy': ['Section XV', 'Chapter 84', 'Heading 8471'],
            'duty_rate': 10.0,
            'vat_rate': 12.0,
            'excise_rate': 0.0,
            'is_sanctioned': False,
            'required_certs': ['Certificate of Conformity'],
            'rulings': [],
            'optimization': [],
            'history': 'No history available',
            'cis_hint': None,
            'version_status': 'ACTIVE',
            'sources': []
        }
        
        return mock_details


def extract_document_data(file_path):
    """
    Extract data from document (mock implementation)
    In a real implementation, this would use OCR/AI to extract data
    """
    # This is a mock implementation
    # In real app, this would process the document and extract structured data
    mock_data = {
        'contract_number': 'CONTRACT-2024-001',
        'partner_name': 'Example Partner LLC',
        'invoice_date': '2024-01-15',
        'products': [
            {
                'name': 'Laptop Computer',
                'hs_code': '8471301000',
                'price': 1200.00,
                'quantity': 10,
                'unit': 'dona',
                'netto': 2.5,
                'brutto': 3.0
            },
            {
                'name': 'Mobile Phone',
                'hs_code': '8517120000',
                'price': 500.00,
                'quantity': 20,
                'unit': 'dona',
                'netto': 0.2,
                'brutto': 0.3
            }
        ]
    }
    
    return mock_data


def perform_ar_inspection(image_data):
    """
    Perform AR inspection of goods (mock implementation)
    """
    # This is a mock implementation
    # In real app, this would use computer vision/AI to count and inspect items
    mock_result = {
        'status': 'SUCCESS',
        'actual_count': 10,
        'expected_count': 10,
        'issues': [],
        'inspection_report': 'All items counted and verified'
    }
    
    return mock_result


def generate_appeal_letter(product, declared_price, customs_price):
    """
    Generate appeal letter for price disputes (mock implementation)
    """
    appeal_text = f"""
    Subject: Appeal for Price Assessment of {product}

    Dear Sir/Madam,

    We are writing to appeal the price assessment made for the above-mentioned goods. 
    The declared price of ${declared_price} is based on genuine commercial transactions 
    and market conditions.

    The customs valuation of ${customs_price} appears to be higher than the actual 
    commercial value of the goods. We respectfully request a review of the assessment 
    based on the supporting documentation we are providing.

    We appreciate your consideration of this matter.

    Sincerely,
    [Your Company Name]
    """
    
    return appeal_text


def detect_chat_intent(message):
    """
    Detect intent from chat message (mock implementation)
    """
    message_lower = message.lower()
    
    # Simple keyword-based intent detection
    if any(word in message_lower for word in ['calculate', 'duty', 'tax', 'cost', 'price']):
        intent = 'CALCULATE_DUTY'
    elif any(word in message_lower for word in ['classify', 'code', 'hs', 'tovar kod', 'tovar kodi']):
        intent = 'CLASSIFY_PRODUCT'
    elif any(word in message_lower for word in ['audit', 'check', 'verify', 'review']):
        intent = 'AUDIT_DECLARATION'
    elif any(word in message_lower for word in ['optimize', 'better', 'improve']):
        intent = 'OPTIMIZE'
    elif any(word in message_lower for word in ['add', 'create', 'new product']):
        intent = 'ADD_PRODUCT'
    else:
        intent = 'GENERAL_QUERY'
    
    result = {
        'intent': intent,
        'confidence': 85,  # Mock confidence
        'responseMessage': 'I understand your request and will help you with it.'
    }
    
    return result


def generate_decision_tree_questions(product_name):
    """
    Generate decision tree questions for product classification (mock implementation)
    """
    questions = [
        {
            'id': 'q1',
            'question': f'What is the primary function of {product_name}?',
            'options': [
                'Industrial use',
                'Commercial use',
                'Personal use',
                'Medical use'
            ]
        },
        {
            'id': 'q2', 
            'question': f'What materials is {product_name} primarily made of?',
            'options': [
                'Metal',
                'Plastic',
                'Textile',
                'Electronic components'
            ]
        },
        {
            'id': 'q3',
            'question': f'What is the main purpose of {product_name}?',
            'options': [
                'Processing/Manufacturing',
                'Storage/Transport',
                'Measurement/Testing',
                'Entertainment'
            ]
        }
    ]
    
    return questions


def get_incoterms_advice(scenario):
    """
    Get Incoterms advice based on scenario (mock implementation)
    """
    advice = {
        'code': 'FOB',
        'name': 'Free on Board',
        'recommendation_reason': 'Suitable for sea freight with clear delivery point',
        'risk_transfer': 'Risk transfers when goods pass ship\'s rail',
        'cost_responsibility': 'Buyer pays for freight and insurance from port of loading',
        'best_for': 'Sea freight, buyer has good logistics network'
    }
    
    return advice


def optimize_product_descriptions(products):
    """
    Optimize product descriptions for customs compliance (mock implementation)
    """
    optimized_products = []
    
    for product in products:
        optimized_product = product.copy()
        # Add standard customs-compliant description
        if 'description' not in optimized_product or not optimized_product['description']:
            optimized_product['description'] = f"Complete technical description of {optimized_product['name']} with specifications, usage, and compliance certificates"
        
        optimized_products.append(optimized_product)
    
    return optimized_products


def generate_trade_strategy(query):
    """
    Generate trade strategy options (mock implementation)
    """
    options = [
        {
            'id': 'route1',
            'method': 'Sea Freight',
            'description': 'Standard sea freight via main port',
            'transit_time': '30-45 days',
            'estimated_cost': 5000.00,
            'savings': 200.00,
            'risk': 'MEDIUM'
        },
        {
            'id': 'route2',
            'method': 'Air Freight',
            'description': 'Express air freight for urgent delivery',
            'transit_time': '5-7 days',
            'estimated_cost': 12000.00,
            'savings': 0.00,
            'risk': 'LOW'
        },
        {
            'id': 'route3', 
            'method': 'Rail Freight',
            'description': 'Rail transport via Central Asia corridor',
            'transit_time': '15-20 days',
            'estimated_cost': 7500.00,
            'savings': 150.00,
            'risk': 'MEDIUM'
        }
    ]
    
    return options


def generate_business_document(doc_type, details, language='en'):
    """
    Generate business document (mock implementation)
    """
    if doc_type.lower() == 'commercial_invoice':
        doc_content = f"""
        COMMERCIAL INVOICE
        
        Invoice Number: {details.get('invoice_number', 'INV-001')}
        Date: {details.get('date', '2024-01-01')}
        Seller: {details.get('seller', 'Seller Company')}
        Buyer: {details.get('buyer', 'Buyer Company')}
        
        Description of Goods:
        """
        for item in details.get('items', []):
            doc_content += f"  - {item.get('name', 'N/A')}: {item.get('quantity', 0)} x {item.get('price', 0)} = {item.get('total', 0)}\n"
        
        doc_content += f"\nTotal Amount: {details.get('total_amount', 0)}\n"
        doc_content += f"Terms of Delivery: {details.get('delivery_terms', 'FOB')}"
        
    else:
        doc_content = f"Generated {doc_type} document with provided details."
    
    return doc_content