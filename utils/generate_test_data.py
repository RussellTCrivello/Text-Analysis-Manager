"""
Test Data Generator
Generates large amounts of realistic test data in Arabic and English
for all database tables (sources, contents, content_analysis)
"""
import sys
import os
import random
from datetime import datetime, timedelta
from typing import List, Dict, Any

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from db.db_config import DatabaseConfig
from db.db_manager import DatabaseManager

# ============== TEST DATA DEFINITIONS ==============

# Source Types
SOURCE_TYPES = {
    'en': ['News Agency', 'Government', 'Social Media', 'Research Institute', 'NGO', 
           'Media Outlet', 'Academic', 'Corporate', 'Blog', 'Official Report',
           'Think Tank', 'International Organization', 'Diplomatic Mission', 'Military Source',
           'Intelligence Agency', 'Financial Institution', 'Technology Company', 'Healthcare Provider',
           'Educational Institution', 'Cultural Organization', 'Religious Institution', 'Trade Union',
           'Environmental Group', 'Human Rights Organization', 'Legal Firm', 'Consulting Agency',
           'Security Firm', 'Energy Company', 'Telecommunications', 'Transportation Company'],
    'ar': ['وكالة أنباء', 'حكومي', 'وسائل التواصل', 'معهد بحثي', 'منظمة غير حكومية',
           'وسيلة إعلامية', 'أكاديمي', 'شركة', 'مدونة', 'تقرير رسمي',
           'مركز تفكير', 'منظمة دولية', 'بعثة دبلوماسية', 'مصدر عسكري',
           'وكالة استخبارات', 'مؤسسة مالية', 'شركة تقنية', 'مقدم رعاية صحية',
           'مؤسسة تعليمية', 'منظمة ثقافية', 'مؤسسة دينية', 'نقابة عمالية',
           'مجموعة بيئية', 'منظمة حقوق إنسان', 'مكتب قانوني', 'وكالة استشارية',
           'شركة أمنية', 'شركة طاقة', 'الاتصالات', 'شركة نقل']
}

# Countries
COUNTRIES = {
    'en': ['United States', 'United Kingdom', 'Germany', 'France', 'Canada', 
           'Australia', 'Japan', 'South Korea', 'India', 'Brazil',
           'Saudi Arabia', 'UAE', 'Egypt', 'Jordan', 'Morocco',
           'Qatar', 'Kuwait', 'Oman', 'Bahrain', 'Tunisia',
           'China', 'Russia', 'Turkey', 'Iran', 'Pakistan',
           'Indonesia', 'Malaysia', 'Thailand', 'Vietnam', 'Philippines',
           'Nigeria', 'South Africa', 'Kenya', 'Ethiopia', 'Ghana',
           'Argentina', 'Mexico', 'Chile', 'Colombia', 'Peru',
           'Spain', 'Italy', 'Netherlands', 'Belgium', 'Switzerland',
           'Sweden', 'Norway', 'Denmark', 'Finland', 'Poland'],
    'ar': ['الولايات المتحدة', 'المملكة المتحدة', 'ألمانيا', 'فرنسا', 'كندا',
           'أستراليا', 'اليابان', 'كوريا الجنوبية', 'الهند', 'البرازيل',
           'المملكة العربية السعودية', 'الإمارات العربية المتحدة', 'مصر', 'الأردن', 'المغرب',
           'قطر', 'الكويت', 'عمان', 'البحرين', 'تونس',
           'الصين', 'روسيا', 'تركيا', 'إيران', 'باكستان',
           'إندونيسيا', 'ماليزيا', 'تايلاند', 'فيتنام', 'الفلبين',
           'نيجيريا', 'جنوب أفريقيا', 'كينيا', 'إثيوبيا', 'غانا',
           'الأرجنتين', 'المكسيك', 'تشيلي', 'كولومبيا', 'بيرو',
           'إسبانيا', 'إيطاليا', 'هولندا', 'بلجيكا', 'سويسرا',
           'السويد', 'النرويج', 'الدنمارك', 'فنلندا', 'بولندا']
}

# Cities
CITIES = {
    'en': ['New York', 'London', 'Berlin', 'Paris', 'Toronto', 'Sydney', 'Tokyo', 
           'Seoul', 'Mumbai', 'Sao Paulo', 'Riyadh', 'Dubai', 'Cairo', 'Amman',
           'Casablanca', 'Doha', 'Kuwait City', 'Muscat', 'Manama', 'Tunis',
           'Beijing', 'Shanghai', 'Moscow', 'Istanbul', 'Tehran', 'Karachi',
           'Jakarta', 'Bangkok', 'Manila', 'Lagos', 'Cape Town', 'Nairobi',
           'Buenos Aires', 'Mexico City', 'Santiago', 'Bogota', 'Lima',
           'Madrid', 'Rome', 'Amsterdam', 'Brussels', 'Zurich',
           'Stockholm', 'Oslo', 'Copenhagen', 'Helsinki', 'Warsaw'],
    'ar': ['نيويورك', 'لندن', 'برلين', 'باريس', 'تورونتو', 'سيدني', 'طوكيو',
           'سيول', 'مومباي', 'ساو باولو', 'الرياض', 'دبي', 'القاهرة', 'عمان',
           'الدار البيضاء', 'الدوحة', 'مدينة الكويت', 'مسقط', 'المنامة', 'تونس',
           'بكين', 'شنغهاي', 'موسكو', 'إسطنبول', 'طهران', 'كراتشي',
           'جاكرتا', 'بانكوك', 'مانيلا', 'لاغوس', 'كيب تاون', 'نيروبي',
           'بوينس آيرس', 'مكسيكو سيتي', 'سانتياغو', 'بوغوتا', 'ليما',
           'مدريد', 'روما', 'أمستردام', 'بروكسل', 'زيورخ',
           'ستوكهولم', 'أوسلو', 'كوبنهاغن', 'هلسنكي', 'وارسو']
}

# Ownership types
OWNERSHIP_TYPES = {
    'en': ['Private', 'Public', 'Government', 'Non-Profit', 'Mixed', 'Independent'],
    'ar': ['خاص', 'عام', 'حكومي', 'غير ربحي', 'مختلط', 'مستقل']
}

# Classifications for analysis
CLASSIFICATIONS = {
    'en': ['Political', 'Economic', 'Social', 'Military', 'Cultural', 'Environmental',
           'Technological', 'Health', 'Educational', 'Security', 'Diplomatic', 'Legal'],
    'ar': ['سياسي', 'اقتصادي', 'اجتماعي', 'عسكري', 'ثقافي', 'بيئي',
           'تكنولوجي', 'صحي', 'تعليمي', 'أمني', 'دبلوماسي', 'قانوني']
}

# Sample source names
SOURCE_NAMES_EN = [
    'Global News Network', 'The Daily Chronicle', 'World Report Agency', 'International Times',
    'Capital News Service', 'Metro Press', 'Central Information Bureau', 'United News Agency',
    'National Broadcasting Service', 'Pacific Media Group', 'Atlantic Press Agency',
    'Continental News Service', 'Federal Information Center', 'Regional News Network',
    'State Media Bureau', 'Independent News Source', 'Digital News Platform',
    'Online Media Channel', 'Broadcast News Service', 'Press Information Agency',
    'Tech News Today', 'Business Daily Report', 'Financial Times Review', 'Economic Observer',
    'Political Analysis Center', 'Security Studies Institute', 'Defense News Agency',
    'Health Information Service', 'Science News Network', 'Education News Bureau',
    'Middle East Monitor', 'Asia Pacific Review', 'European Affairs Journal', 'African Press Union',
    'Latin America Today', 'Arctic Research Center', 'Mediterranean Watch', 'Gulf Cooperation News',
    'Strategic Intelligence Group', 'Cybersecurity Alert', 'Energy Market Report', 'Climate Change Institute',
    'Human Rights Watch', 'International Development Agency', 'Diplomatic Relations Bureau', 'Trade Commission',
    'Cultural Exchange Foundation', 'Academic Research Council', 'Technology Innovation Lab', 'Healthcare Analytics',
    'Financial Intelligence Unit', 'Counter-Terrorism Center', 'Border Security Agency', 'Maritime Affairs Office',
    'Space Research Organization', 'Nuclear Energy Authority', 'Renewable Energy Council', 'Water Resources Institute',
    'Agricultural Development Board', 'Tourism Promotion Agency', 'Sports Federation', 'Arts and Culture Society',
    'Youth Development Program', 'Women\'s Rights Organization', 'Labor Relations Bureau', 'Consumer Protection Agency',
    'Environmental Protection Agency', 'Wildlife Conservation Fund', 'Urban Planning Department', 'Transportation Authority',
]

SOURCE_NAMES_AR = [
    'شبكة الأخبار العالمية', 'الصحيفة اليومية', 'وكالة التقارير الدولية', 'التايمز الدولية',
    'خدمة أخبار العاصمة', 'صحافة المدينة', 'مكتب المعلومات المركزي', 'وكالة الأنباء المتحدة',
    'خدمة البث الوطنية', 'مجموعة الإعلام الباسيفيكية', 'وكالة الأنباء الأطلسية',
    'خدمة الأخبار القارية', 'مركز المعلومات الفيدرالي', 'شبكة الأخبار الإقليمية',
    'مكتب الإعلام الرسمي', 'مصدر الأخبار المستقل', 'منصة الأخبار الرقمية',
    'قناة الإعلام الإلكتروني', 'خدمة أخبار البث', 'وكالة المعلومات الصحفية',
    'أخبار التقنية اليوم', 'تقرير الأعمال اليومي', 'مراجعة الأوقات المالية', 'المراقب الاقتصادي',
    'مركز التحليل السياسي', 'معهد الدراسات الأمنية', 'وكالة أخبار الدفاع',
    'خدمة المعلومات الصحية', 'شبكة أخبار العلوم', 'مكتب الأخبار التعليمية',
    'مراقب الشرق الأوسط', 'مراجعة آسيا والمحيط الهادئ', 'مجلة الشؤون الأوروبية', 'اتحاد الصحافة الأفريقية',
    'أمريكا اللاتينية اليوم', 'مركز البحوث القطبية', 'مراقب البحر المتوسط', 'أخبار التعاون الخليجي',
    'مجموعة الاستخبارات الاستراتيجية', 'تنبيه الأمن السيبراني', 'تقرير سوق الطاقة', 'معهد تغير المناخ',
    'مراقبة حقوق الإنسان', 'وكالة التنمية الدولية', 'مكتب العلاقات الدبلوماسية', 'لجنة التجارة',
    'مؤسسة التبادل الثقافي', 'مجلس البحوث الأكاديمية', 'مختبر الابتكار التقني', 'تحليلات الرعاية الصحية',
    'وحدة الاستخبارات المالية', 'مركز مكافحة الإرهاب', 'وكالة أمن الحدود', 'مكتب الشؤون البحرية',
    'منظمة أبحاث الفضاء', 'هيئة الطاقة النووية', 'مجلس الطاقة المتجددة', 'معهد الموارد المائية',
    'مجلس التنمية الزراعية', 'وكالة الترويج السياحي', 'الاتحاد الرياضي', 'جمعية الفنون والثقافة',
    'برنامج تنمية الشباب', 'منظمة حقوق المرأة', 'مكتب علاقات العمل', 'وكالة حماية المستهلك',
    'وكالة حماية البيئة', 'صندوق الحفاظ على الحياة البرية', 'إدارة التخطيط الحضري', 'هيئة النقل',
]

# Sample content titles
CONTENT_TITLES_EN = [
    'Breaking: Major Policy Changes Announced',
    'Economic Report Shows Growth Trends',
    'International Summit Concludes Successfully',
    'New Technology Breakthrough Revealed',
    'Security Council Meeting Updates',
    'Environmental Initiative Launched',
    'Healthcare Reform Progress Report',
    'Education System Improvements Planned',
    'Infrastructure Development Projects',
    'Trade Agreement Negotiations Continue',
    'Climate Change Conference Results',
    'Digital Transformation Strategy',
    'Public Health Advisory Issued',
    'Military Exercise Completed',
    'Cultural Exchange Program Announced',
    'Research Findings Published',
    'Market Analysis Report Released',
    'Regional Cooperation Agreement',
    'Social Development Program Update',
    'Government Budget Allocation Review',
    'Cybersecurity Threat Assessment', 'Energy Sector Investment Plan', 'Refugee Crisis Response',
    'Agricultural Innovation Program', 'Space Exploration Mission Update', 'Nuclear Safety Protocol',
    'Maritime Security Operations', 'Border Control Enhancement', 'Counter-Terrorism Strategy',
    'International Trade Dispute Resolution', 'Climate Adaptation Measures', 'Renewable Energy Expansion',
    'Urban Development Master Plan', 'Transportation Infrastructure Upgrade', 'Water Management Initiative',
    'Education Technology Integration', 'Healthcare System Modernization', 'Financial Market Regulation',
    'Cultural Heritage Preservation', 'Tourism Industry Recovery Plan', 'Sports Development Program',
    'Youth Employment Initiative', 'Women Empowerment Campaign', 'Labor Rights Protection',
    'Consumer Safety Standards', 'Wildlife Conservation Project', 'Disaster Preparedness Plan',
    'Technology Transfer Agreement', 'Research Collaboration Framework', 'Innovation Hub Launch',
    'Startup Ecosystem Development', 'Digital Economy Growth Strategy', 'Artificial Intelligence Ethics',
    'Data Privacy Regulations', 'Cybersecurity Framework Update', 'Blockchain Implementation',
    'Smart City Initiative', '5G Network Deployment', 'Internet of Things Expansion',
]

CONTENT_TITLES_AR = [
    'عاجل: إعلان تغييرات سياسية كبرى',
    'تقرير اقتصادي يظهر اتجاهات النمو',
    'القمة الدولية تختتم بنجاح',
    'الكشف عن اختراق تكنولوجي جديد',
    'تحديثات اجتماع مجلس الأمن',
    'إطلاق مبادرة بيئية جديدة',
    'تقرير تقدم الإصلاح الصحي',
    'خطط تحسين النظام التعليمي',
    'مشاريع تطوير البنية التحتية',
    'استمرار مفاوضات الاتفاقيات التجارية',
    'نتائج مؤتمر تغير المناخ',
    'استراتيجية التحول الرقمي',
    'إصدار استشارة الصحة العامة',
    'اكتمال التدريبات العسكرية',
    'إعلان برنامج التبادل الثقافي',
    'نشر نتائج البحث',
    'إصدار تقرير تحليل السوق',
    'اتفاقية التعاون الإقليمي',
    'تحديث برنامج التنمية الاجتماعية',
    'مراجعة تخصيص الميزانية الحكومية',
    'تقييم تهديد الأمن السيبراني', 'خطة استثمار قطاع الطاقة', 'استجابة أزمة اللاجئين',
    'برنامج الابتكار الزراعي', 'تحديث مهمة استكشاف الفضاء', 'بروتوكول السلامة النووية',
    'عمليات الأمن البحري', 'تعزيز مراقبة الحدود', 'استراتيجية مكافحة الإرهاب',
    'حل نزاعات التجارة الدولية', 'تدابير التكيف مع المناخ', 'توسيع الطاقة المتجددة',
    'الخطة الرئيسية للتنمية الحضرية', 'ترقية البنية التحتية للنقل', 'مبادرة إدارة المياه',
    'دمج تكنولوجيا التعليم', 'تحديث نظام الرعاية الصحية', 'تنظيم السوق المالي',
    'الحفاظ على التراث الثقافي', 'خطة انتعاش صناعة السياحة', 'برنامج تطوير الرياضة',
    'مبادرة توظيف الشباب', 'حملة تمكين المرأة', 'حماية حقوق العمال',
    'معايير سلامة المستهلك', 'مشروع الحفاظ على الحياة البرية', 'خطة التأهب للكوارث',
    'اتفاقية نقل التكنولوجيا', 'إطار التعاون البحثي', 'إطلاق مركز الابتكار',
    'تطوير نظام الشركات الناشئة', 'استراتيجية نمو الاقتصاد الرقمي', 'أخلاقيات الذكاء الاصطناعي',
    'لوائح خصوصية البيانات', 'تحديث إطار الأمن السيبراني', 'تنفيذ البلوك تشين',
    'مبادرة المدينة الذكية', 'نشر شبكة الجيل الخامس', 'توسيع إنترنت الأشياء',
]

# Sample content data paragraphs
CONTENT_PARAGRAPHS_EN = [
    "According to official sources, significant developments have been made in the ongoing negotiations between regional partners. The discussions focused on economic cooperation and security matters.",
    "The latest report indicates substantial progress in infrastructure development across multiple sectors. Investment in technology and innovation remains a top priority for stakeholders.",
    "Officials announced new measures to address emerging challenges in the region. The comprehensive plan includes initiatives for sustainable development and social welfare programs.",
    "Recent data analysis reveals changing trends in public sentiment regarding government policies. Survey results show increasing support for reform initiatives.",
    "International observers noted positive developments in diplomatic relations between neighboring countries. The bilateral agreements are expected to enhance cooperation.",
    "The research findings highlight the importance of investing in education and healthcare systems. Experts recommend increased funding for these critical sectors.",
    "Market indicators suggest a stable economic outlook for the coming quarter. Analysts project moderate growth in key industries and employment sectors.",
    "Security assessments indicate improved conditions following recent coordination efforts. Joint operations have successfully addressed key concerns.",
    "Environmental monitoring data shows progress in conservation efforts. Sustainability programs have gained momentum with public and private sector support.",
    "Technological advancements continue to transform various industries. Digital transformation initiatives are reshaping business operations and service delivery.",
    "Cybersecurity experts warn of increasing threats targeting critical infrastructure. Organizations are urged to strengthen their defense mechanisms and update security protocols.",
    "Energy sector analysts predict significant shifts in global markets. Renewable energy investments are reaching record levels while traditional sources face new challenges.",
    "Humanitarian organizations report urgent needs in conflict-affected regions. Emergency response teams are coordinating relief efforts across multiple countries.",
    "Agricultural researchers announce breakthrough in sustainable farming techniques. New methods promise higher yields with reduced environmental impact.",
    "Space agencies collaborate on ambitious exploration missions. International partnerships are advancing our understanding of the universe.",
    "Nuclear safety authorities implement enhanced monitoring systems. Stringent protocols ensure the safe operation of power facilities worldwide.",
    "Maritime security forces conduct joint patrols in strategic waterways. Enhanced cooperation aims to combat piracy and ensure safe passage.",
    "Border control agencies deploy advanced screening technologies. New systems improve detection capabilities while streamlining legitimate travel.",
    "Counter-terrorism units share intelligence across international networks. Coordinated efforts have prevented multiple potential attacks.",
    "Trade negotiators work toward resolving complex disputes. Multilateral discussions focus on fair market access and dispute resolution mechanisms.",
    "Climate scientists document accelerating environmental changes. Adaptation strategies are being developed to address rising sea levels and extreme weather.",
    "Renewable energy projects receive unprecedented funding. Solar and wind installations are expanding rapidly across multiple continents.",
    "Urban planners unveil comprehensive development strategies. Smart city technologies are being integrated into infrastructure projects.",
    "Transportation authorities announce major infrastructure upgrades. High-speed rail networks and modernized ports will enhance connectivity.",
    "Water management experts address growing scarcity concerns. Conservation programs and desalination projects are being prioritized.",
    "Educational institutions adopt innovative teaching methods. Technology integration is transforming learning experiences for students worldwide.",
    "Healthcare systems implement digital health solutions. Telemedicine and electronic records are improving patient care accessibility.",
    "Financial regulators introduce new compliance frameworks. Enhanced oversight aims to prevent fraud and protect investors.",
    "Cultural preservation efforts receive international support. Heritage sites are being restored and protected for future generations.",
    "Tourism industry stakeholders develop recovery strategies. Safety protocols and marketing campaigns aim to restore visitor confidence.",
    "Sports organizations announce development programs. Youth initiatives and infrastructure investments will promote athletic participation.",
    "Employment agencies launch job creation initiatives. Training programs and incentives aim to reduce unemployment rates.",
    "Women's rights advocates celebrate legislative victories. New laws strengthen protections and promote gender equality.",
    "Labor unions negotiate improved working conditions. Collective bargaining agreements address wages, benefits, and workplace safety.",
    "Consumer protection agencies investigate product safety concerns. Recalls and warnings protect public health and safety.",
    "Wildlife conservationists report success in species recovery programs. Protected areas and breeding initiatives show positive results.",
    "Emergency management teams conduct disaster preparedness exercises. Simulation scenarios test response capabilities and coordination.",
    "Technology transfer programs facilitate knowledge sharing. International partnerships accelerate innovation and development.",
    "Research institutions establish collaborative networks. Joint studies address global challenges and advance scientific understanding.",
    "Innovation hubs attract startups and entrepreneurs. Supportive ecosystems provide funding, mentorship, and infrastructure.",
    "Digital economy initiatives promote online business growth. E-commerce platforms and digital services are expanding rapidly.",
    "Artificial intelligence ethics committees develop guidelines. Responsible AI development addresses bias, privacy, and accountability.",
    "Data protection authorities enforce privacy regulations. Compliance requirements protect personal information and digital rights.",
    "Cybersecurity frameworks are updated to address emerging threats. Best practices and standards guide organizational security.",
    "Blockchain implementations transform financial transactions. Distributed ledger technology improves transparency and reduces fraud.",
    "Smart city projects integrate IoT sensors and data analytics. Real-time monitoring optimizes urban services and resource management.",
    "5G network deployments accelerate connectivity improvements. High-speed wireless infrastructure enables new applications and services.",
]

CONTENT_PARAGRAPHS_AR = [
    "وفقاً للمصادر الرسمية، تم إحراز تطورات كبيرة في المفاوضات الجارية بين الشركاء الإقليميين. ركزت المناقشات على التعاون الاقتصادي والمسائل الأمنية.",
    "يشير التقرير الأخير إلى تقدم كبير في تطوير البنية التحتية عبر قطاعات متعددة. يظل الاستثمار في التكنولوجيا والابتكار أولوية قصوى لأصحاب المصلحة.",
    "أعلن المسؤولون عن تدابير جديدة لمواجهة التحديات الناشئة في المنطقة. تتضمن الخطة الشاملة مبادرات للتنمية المستدامة وبرامج الرعاية الاجتماعية.",
    "يكشف تحليل البيانات الأخير عن اتجاهات متغيرة في الرأي العام حول السياسات الحكومية. تظهر نتائج الاستطلاع دعماً متزايداً لمبادرات الإصلاح.",
    "لاحظ المراقبون الدوليون تطورات إيجابية في العلاقات الدبلوماسية بين الدول المجاورة. من المتوقع أن تعزز الاتفاقيات الثنائية التعاون.",
    "تسلط نتائج البحث الضوء على أهمية الاستثمار في أنظمة التعليم والرعاية الصحية. يوصي الخبراء بزيادة التمويل لهذه القطاعات الحيوية.",
    "تشير مؤشرات السوق إلى توقعات اقتصادية مستقرة للربع القادم. يتوقع المحللون نمواً معتدلاً في الصناعات الرئيسية وقطاعات التوظيف.",
    "تشير التقييمات الأمنية إلى تحسن الأوضاع بعد جهود التنسيق الأخيرة. نجحت العمليات المشتركة في معالجة المخاوف الرئيسية.",
    "تظهر بيانات الرصد البيئي تقدماً في جهود الحفاظ على البيئة. اكتسبت برامج الاستدامة زخماً بدعم من القطاعين العام والخاص.",
    "تستمر التطورات التكنولوجية في تحويل مختلف الصناعات. تعيد مبادرات التحول الرقمي تشكيل العمليات التجارية وتقديم الخدمات.",
    "يحذر خبراء الأمن السيبراني من تزايد التهديدات التي تستهدف البنية التحتية الحيوية. يُنصح المنظمات بتعزيز آليات الدفاع وتحديث بروتوكولات الأمان.",
    "يتوقع محللو قطاع الطاقة تحولات كبيرة في الأسواق العالمية. تصل استثمارات الطاقة المتجددة إلى مستويات قياسية بينما تواجه المصادر التقليدية تحديات جديدة.",
    "تقرر المنظمات الإنسانية باحتياجات عاجلة في المناطق المتأثرة بالصراعات. تنسق فرق الاستجابة الطارئة جهود الإغاثة عبر عدة دول.",
    "يعلن باحثون زراعيون عن اختراق في تقنيات الزراعة المستدامة. تعد الأساليب الجديدة بإنتاجية أعلى مع تأثير بيئي أقل.",
    "تتعاون وكالات الفضاء في مهمات استكشاف طموحة. تدفع الشراكات الدولية فهمنا للكون إلى الأمام.",
    "تنفذ سلطات السلامة النووية أنظمة مراقبة محسنة. تضمن البروتوكولات الصارمة التشغيل الآمن للمنشآت في جميع أنحاء العالم.",
    "تجري قوات الأمن البحري دوريات مشتركة في الممرات المائية الاستراتيجية. يهدف التعاون المعزز إلى مكافحة القرصنة وضمان المرور الآمن.",
    "تنشر وكالات مراقبة الحدود تقنيات فحص متقدمة. تحسن الأنظمة الجديدة قدرات الكشف مع تبسيط السفر المشروع.",
    "تشارك وحدات مكافحة الإرهاب المعلومات عبر الشبكات الدولية. منعت الجهود المنسقة هجمات محتملة متعددة.",
    "يعمل مفاوضو التجارة نحو حل النزاعات المعقدة. تركز المناقشات متعددة الأطراف على الوصول العادل للسوق وآليات حل النزاعات.",
    "يوثق علماء المناخ تسارع التغيرات البيئية. يتم تطوير استراتيجيات التكيف لمعالجة ارتفاع مستويات البحر والطقس المتطرف.",
    "تتلقى مشاريع الطاقة المتجددة تمويلاً غير مسبوق. تتوسع التركيبات الشمسية وطاقة الرياح بسرعة عبر قارات متعددة.",
    "يكشف مخططو المدن عن استراتيجيات تنمية شاملة. يتم دمج تقنيات المدن الذكية في مشاريع البنية التحتية.",
    "تعلن سلطات النقل عن ترقيات كبيرة للبنية التحتية. ستزيد شبكات السكك الحديدية عالية السرعة والموانئ الحديثة من الاتصال.",
    "يعالج خبراء إدارة المياه مخاوف الندرة المتزايدة. يتم إعطاء الأولوية لبرامج الحفظ ومشاريع تحلية المياه.",
    "تتبنى المؤسسات التعليمية طرق تدريس مبتكرة. يحول دمج التكنولوجيا تجارب التعلم للطلاب في جميع أنحاء العالم.",
    "تنفذ أنظمة الرعاية الصحية حلول الصحة الرقمية. تحسن التطبيب عن بُعد والسجلات الإلكترونية إمكانية الوصول إلى رعاية المرضى.",
    "تقدم الجهات التنظيمية المالية أطر امتثال جديدة. يهدف الإشراف المعزز إلى منع الاحتيال وحماية المستثمرين.",
    "تتلقى جهود الحفاظ على التراث الثقافي دعماً دولياً. يتم ترميم المواقع التراثية وحمايتها للأجيال القادمة.",
    "يطور أصحاب المصلحة في صناعة السياحة استراتيجيات الانتعاش. تهدف بروتوكولات السلامة وحملات التسويق إلى استعادة ثقة الزوار.",
    "تعلن المنظمات الرياضية عن برامج التنمية. ستشجع مبادرات الشباب واستثمارات البنية التحتية على المشاركة الرياضية.",
    "تطلق وكالات التوظيف مبادرات خلق الوظائف. تهدف برامج التدريب والحوافز إلى تقليل معدلات البطالة.",
    "تحتفل دعاة حقوق المرأة بانتصارات تشريعية. تقوي القوانين الجديدة الحماية وتعزز المساواة بين الجنسين.",
    "تتفاوض النقابات العمالية على تحسين ظروف العمل. تتناول اتفاقيات التفاوض الجماعي الأجور والفوائد وسلامة مكان العمل.",
    "تحقق وكالات حماية المستهلك في مخاوف سلامة المنتجات. تحمي عمليات الاستدعاء والتحذيرات الصحة والسلامة العامة.",
    "يبلغ دعاة الحفاظ على الحياة البرية عن نجاح في برامج استعادة الأنواع. تظهر المناطق المحمية ومبادرات التربية نتائج إيجابية.",
    "تجري فرق إدارة الطوارئ تمارين التأهب للكوارث. تختبر سيناريوهات المحاكاة قدرات الاستجابة والتنسيق.",
    "تسهل برامج نقل التكنولوجيا مشاركة المعرفة. تسرع الشراكات الدولية الابتكار والتنمية.",
    "تنشئ المؤسسات البحثية شبكات تعاونية. تعالج الدراسات المشتركة التحديات العالمية وتدفع الفهم العلمي.",
    "تجذب مراكز الابتكار الشركات الناشئة ورجال الأعمال. توفر النظم البيئية الداعمة التمويل والإرشاد والبنية التحتية.",
    "تعزز مبادرات الاقتصاد الرقمي نمو الأعمال عبر الإنترنت. تتوسع منصات التجارة الإلكترونية والخدمات الرقمية بسرعة.",
    "تطور لجان أخلاقيات الذكاء الاصطناعي إرشادات. يعالج تطوير الذكاء الاصطناعي المسؤول التحيز والخصوصية والمساءلة.",
    "تطبق سلطات حماية البيانات لوائح الخصوصية. تحمي متطلبات الامتثال المعلومات الشخصية والحقوق الرقمية.",
    "يتم تحديث أطر الأمن السيبراني لمعالجة التهديدات الناشئة. توجه أفضل الممارسات والمعايير أمن المنظمات.",
    "تحول تطبيقات البلوك تشين المعاملات المالية. تحسن تقنية دفتر الأستاذ الموزع الشفافية وتقلل الاحتيال.",
    "تدمج مشاريع المدن الذكية أجهزة استشعار إنترنت الأشياء وتحليلات البيانات. تحسن المراقبة في الوقت الفعلي الخدمات الحضرية وإدارة الموارد.",
    "تسرع عمليات نشر شبكات الجيل الخامس تحسينات الاتصال. تمكن البنية التحتية اللاسلكية عالية السرعة تطبيقات وخدمات جديدة.",
]

# Sample people names
PEOPLE_NAMES_EN = [
    "Dr. James Wilson", "Prof. Sarah Mitchell", "Gen. Michael Thompson", "Amb. Elizabeth Brown",
    "Minister John Davis", "Secretary Maria Garcia", "Director Robert Anderson", "Chairman David Lee",
    "President Thomas White", "CEO Jennifer Taylor", "Dr. William Harris", "Prof. Emily Clark",
    "Lt. Gen. Christopher Martin", "Senator Patricia Moore", "Gov. Richard Jackson", "Mayor Susan Hall",
]

PEOPLE_NAMES_AR = [
    "د. أحمد محمد", "أ.د. فاطمة علي", "اللواء خالد إبراهيم", "السفير نورة الأحمد",
    "الوزير عبدالله السعيد", "الأمين سارة الحسن", "المدير محمد الفهد", "الرئيس عمر الشمري",
    "الدكتور يوسف العتيبي", "المهندس ليلى القحطاني", "أ.د. سلطان الدوسري", "د. مريم الغامدي",
    "الفريق ناصر العنزي", "النائب هند المطيري", "المحافظ سعود الرشيد", "العمدة نوف الهاشمي",
]

# Sample place names
PLACES_EN = [
    "Central District", "Northern Region", "Southern Province", "Eastern Zone",
    "Western Territory", "Capital Area", "Industrial Zone", "Commercial District",
    "Residential Area", "Border Region", "Coastal Zone", "Mountain Region",
    "Desert Area", "Agricultural Zone", "Urban Center", "Rural District",
]

PLACES_AR = [
    "المنطقة المركزية", "الإقليم الشمالي", "المحافظة الجنوبية", "المنطقة الشرقية",
    "الإقليم الغربي", "منطقة العاصمة", "المنطقة الصناعية", "الحي التجاري",
    "المنطقة السكنية", "منطقة الحدود", "المنطقة الساحلية", "منطقة الجبال",
    "المنطقة الصحراوية", "المنطقة الزراعية", "المركز الحضري", "المنطقة الريفية",
]

# Sample sides/parties
SIDES_EN = [
    "Government Officials", "Opposition Groups", "International Organizations",
    "Private Sector", "Civil Society", "Academic Institutions", "Media Organizations",
    "Local Communities", "Regional Partners", "Foreign Investors", "Labor Unions",
    "Environmental Groups", "Youth Organizations", "Women's Groups", "Professional Associations",
]

SIDES_AR = [
    "المسؤولون الحكوميون", "مجموعات المعارضة", "المنظمات الدولية",
    "القطاع الخاص", "المجتمع المدني", "المؤسسات الأكاديمية", "المنظمات الإعلامية",
    "المجتمعات المحلية", "الشركاء الإقليميون", "المستثمرون الأجانب", "النقابات العمالية",
    "المجموعات البيئية", "منظمات الشباب", "المجموعات النسائية", "الجمعيات المهنية",
]


# ============== DATA GENERATION FUNCTIONS ==============

def random_date(start_days_ago: int = 365, end_days_ago: int = 0) -> datetime:
    """Generate a random date within the specified range"""
    days_ago = random.randint(end_days_ago, start_days_ago)
    return datetime.now() - timedelta(days=days_ago)


def random_coordinates() -> str:
    """Generate random GPS coordinates"""
    lat = round(random.uniform(-90, 90), 6)
    lon = round(random.uniform(-180, 180), 6)
    return f"{lat}, {lon}"


def generate_source_data(index: int) -> Dict[str, Any]:
    """Generate a single source record"""
    lang = random.choice(['en', 'ar'])
    
    if lang == 'en':
        base_name = random.choice(SOURCE_NAMES_EN)
        name = f"{base_name} {index}"
    else:
        base_name = random.choice(SOURCE_NAMES_AR)
        name = f"{base_name} {index}"
    
    country_idx = random.randint(0, len(COUNTRIES['en']) - 1)
    
    return {
        'name': name,
        'type': random.choice(SOURCE_TYPES[lang]),
        'link_sources': f"https://source{index}.example.com",
        'importance': round(random.uniform(0.1, 1.0), 2),
        'country': COUNTRIES[lang][country_idx],
        'city': CITIES[lang][country_idx % len(CITIES[lang])],
        'description': f"{'وصف المصدر رقم' if lang == 'ar' else 'Source description for'} {name}. " + 
                      (CONTENT_PARAGRAPHS_AR[index % len(CONTENT_PARAGRAPHS_AR)] if lang == 'ar' 
                       else CONTENT_PARAGRAPHS_EN[index % len(CONTENT_PARAGRAPHS_EN)]),
        'accounts': f"@source{index}, contact@source{index}.com",
        'note': f"{'ملاحظات حول المصدر' if lang == 'ar' else 'Notes about source'} {index}",
        'ownership': random.choice(OWNERSHIP_TYPES[lang]),
        'date_entry': random_date(730, 30),
        'date_creation': datetime.now()
    }


def generate_content_data(source_id: int, index: int) -> Dict[str, Any]:
    """Generate a single content record"""
    lang = random.choice(['en', 'ar'])
    
    title = random.choice(CONTENT_TITLES_AR if lang == 'ar' else CONTENT_TITLES_EN)
    title = f"{title} - {index}"
    
    # Generate 2-5 paragraphs of content
    num_paragraphs = random.randint(2, 5)
    paragraphs = CONTENT_PARAGRAPHS_AR if lang == 'ar' else CONTENT_PARAGRAPHS_EN
    content = "\n\n".join(random.sample(paragraphs, min(num_paragraphs, len(paragraphs))))
    
    return {
        'title': title,
        'content_data': content,
        'attachments': f"file{index}.pdf, image{index}.jpg" if random.random() > 0.5 else None,
        'note': f"{'ملاحظة المحتوى' if lang == 'ar' else 'Content note'} {index}",
        'importance': round(random.uniform(0.1, 1.0), 2),
        'date_content': random_date(365, 1),
        'date_creation': datetime.now(),
        'sources_id': source_id
    }


def generate_analysis_data(content_id: int, index: int) -> Dict[str, Any]:
    """Generate a single analysis record"""
    lang = random.choice(['en', 'ar'])
    
    # Generate lists of names
    num_people = random.randint(1, 5)
    num_places = random.randint(1, 4)
    num_sides = random.randint(1, 3)
    
    people = PEOPLE_NAMES_AR if lang == 'ar' else PEOPLE_NAMES_EN
    places = PLACES_AR if lang == 'ar' else PLACES_EN
    sides = SIDES_AR if lang == 'ar' else SIDES_EN
    
    return {
        'content_id': content_id,
        'list_names_people': ", ".join(random.sample(people, min(num_people, len(people)))),
        'list_names_places': ", ".join(random.sample(places, min(num_places, len(places)))),
        'coordinates': random_coordinates() if random.random() > 0.3 else None,
        'classification': random.choice(CLASSIFICATIONS[lang]),
        'list_sides': ", ".join(random.sample(sides, min(num_sides, len(sides)))),
        'date_analysis': random_date(180, 1),
    }


# ============== MAIN DATA GENERATION ==============

def generate_all_data(num_sources: int = 100, contents_per_source: int = 5, 
                      analysis_ratio: float = 0.8, show_progress: bool = True):
    """
    Generate test data for all tables
    
    Args:
        num_sources: Number of sources to create
        contents_per_source: Average number of contents per source
        analysis_ratio: Percentage of contents that get analysis (0.0-1.0)
        show_progress: Whether to print progress messages
    """
    
    print("=" * 60)
    print("TEST DATA GENERATOR")
    print("=" * 60)
    
    # Initialize database
    print("\nInitializing database...")
    success, error = DatabaseConfig.initialize_database()
    if not success:
        print(f"Database initialization failed: {error}")
        return False
    
    print(f"Database path: {DatabaseConfig.get_db_path()}")
    
    # Statistics
    sources_created = 0
    contents_created = 0
    analyses_created = 0
    errors = []
    
    # Generate Sources
    print(f"\n[1/3] Generating {num_sources} sources...")
    source_ids = []
    
    for i in range(num_sources):
        try:
            data = generate_source_data(i + 1)
            source_id = DatabaseManager.add_source(data)
            source_ids.append(source_id)
            sources_created += 1
            
            if show_progress and (i + 1) % 10 == 0:
                print(f"      Sources: {i + 1}/{num_sources}")
                
        except Exception as e:
            errors.append(f"Source {i + 1}: {str(e)}")
    
    print(f"      Created {sources_created} sources")
    
    # Generate Contents
    total_contents = num_sources * contents_per_source
    print(f"\n[2/3] Generating ~{total_contents} contents...")
    content_ids = []
    
    content_index = 0
    for source_id in source_ids:
        # Random number of contents per source (1 to 2x average)
        num_contents = random.randint(1, contents_per_source * 2)
        
        for j in range(num_contents):
            try:
                content_index += 1
                data = generate_content_data(source_id, content_index)
                content_id = DatabaseManager.add_content(data)
                content_ids.append(content_id)
                contents_created += 1
                
                if show_progress and contents_created % 50 == 0:
                    print(f"      Contents: {contents_created}")
                    
            except Exception as e:
                errors.append(f"Content {content_index}: {str(e)}")
    
    print(f"      Created {contents_created} contents")
    
    # Generate Analysis
    num_to_analyze = int(len(content_ids) * analysis_ratio)
    print(f"\n[3/3] Generating ~{num_to_analyze} analysis records...")
    
    contents_to_analyze = random.sample(content_ids, min(num_to_analyze, len(content_ids)))
    
    for i, content_id in enumerate(contents_to_analyze):
        try:
            data = generate_analysis_data(content_id, i + 1)
            DatabaseManager.add_content_analysis(data)
            analyses_created += 1
            
            if show_progress and (i + 1) % 50 == 0:
                print(f"      Analysis: {i + 1}/{num_to_analyze}")
                
        except Exception as e:
            errors.append(f"Analysis {i + 1}: {str(e)}")
    
    print(f"      Created {analyses_created} analysis records")
    
    # Summary
    print("\n" + "=" * 60)
    print("GENERATION COMPLETE")
    print("=" * 60)
    print(f"\nStatistics:")
    print(f"  - Sources created:  {sources_created}")
    print(f"  - Contents created: {contents_created}")
    print(f"  - Analyses created: {analyses_created}")
    print(f"  - Total records:    {sources_created + contents_created + analyses_created}")
    
    if errors:
        print(f"\nErrors ({len(errors)}):")
        for err in errors[:10]:  # Show first 10 errors
            print(f"  - {err}")
        if len(errors) > 10:
            print(f"  ... and {len(errors) - 10} more errors")
    
    print("\n" + "=" * 60)
    return True


def clear_all_data():
    """Clear all data from the database (for fresh testing)"""
    print("\nWARNING: This will delete ALL data from the database!")
    confirm = input("Type 'YES' to confirm: ")
    
    if confirm != 'YES':
        print("Operation cancelled.")
        return
    
    try:
        conn = DatabaseConfig.get_connection()
        cursor = conn.cursor()
        
        # Delete in order due to foreign keys
        cursor.execute("DELETE FROM content_analysis")
        cursor.execute("DELETE FROM contents")
        cursor.execute("DELETE FROM sources")
        
        conn.commit()
        cursor.close()
        
        print("All data cleared successfully!")
        
    except Exception as e:
        print(f"Error clearing data: {e}")


def main():
    """Main function with command line options"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Generate test data for the database')
    parser.add_argument('--sources', type=int, default=100, 
                       help='Number of sources to generate (default: 100)')
    parser.add_argument('--contents', type=int, default=5,
                       help='Average contents per source (default: 5)')
    parser.add_argument('--analysis-ratio', type=float, default=0.8,
                       help='Ratio of contents with analysis (default: 0.8)')
    parser.add_argument('--clear', action='store_true',
                       help='Clear all existing data first')
    parser.add_argument('--small', action='store_true',
                       help='Generate small dataset (20 sources)')
    parser.add_argument('--medium', action='store_true',
                       help='Generate medium dataset (100 sources)')
    parser.add_argument('--large', action='store_true',
                       help='Generate large dataset (500 sources)')
    parser.add_argument('--xlarge', action='store_true',
                       help='Generate extra large dataset (1000 sources)')
    
    args = parser.parse_args()
    
    if args.clear:
        clear_all_data()
    
    # Preset sizes
    if args.small:
        num_sources = 20
        contents_per = 3
    elif args.medium:
        num_sources = 100
        contents_per = 5
    elif args.large:
        num_sources = 500
        contents_per = 5
    elif args.xlarge:
        num_sources = 1000
        contents_per = 5
    else:
        num_sources = args.sources
        contents_per = args.contents
    
    generate_all_data(
        num_sources=num_sources,
        contents_per_source=contents_per,
        analysis_ratio=args.analysis_ratio
    )


if __name__ == '__main__':
    main()
