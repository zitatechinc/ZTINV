from django.core.management.base import BaseCommand
from catalog.models import (
    Category, ProductType, Brand, Languages, ProductGroup, Manufacturer, Product,Brand
)
from django.utils.text import slugify
from catalog.models import Category
from vendor.models import VendorType  # Assuming your VendorType model is defined in the catalog app
from django.db import IntegrityError
import random


class Command(BaseCommand):
    help = "Insert 50 Categories with proper parent-child hierarchy"

    def handle(self, *args, **kwargs):

        # --------------------------
        # ProductCategories data
        # --------------------------
        categories = [
            (1, 'Electronics', 'ELEC', 1, 'electronics gadgets', None),
            (2, 'Computers', 'COMPUT', 1, 'computers laptops desktops', 1),
            (3, 'Mobile Phones', 'MOBILE', 1, 'smartphones mobiles', 1),
            (4, 'Phone Accessories', 'PHONEACC', 1, 'chargers cases cables', 3),
            (5, 'Laptop Accessories', 'LAPACC', 1, 'laptop bags mouse keyboard', 2),
            (6, 'Home Appliances', 'HOMEAPP', 1, 'home appliances', None),
            (7, 'Kitchen Appliances', 'KITCHAPP', 1, 'kitchen machines', 6),
            (8, 'Cookware', 'COOK', 1, 'cookware utensils', 7),
            (9, 'Furniture', 'FURN', 1, 'home furniture', None),
            (10, 'Bedroom Furniture', 'BEDFURN', 1, 'beds wardrobes', 9),
            (11, 'Office Furniture', 'OFFFURN', 1, 'office tables chairs', 9),
            (12, 'Fashion', 'FASH', 1, 'clothing fashion', None),
            (13, 'Men Clothing', 'MENCL', 1, 'mens wear', 12),
            (14, 'Women Clothing', 'WOMCL', 1, 'womens wear', 12),
            (15, 'Footwear', 'FOOT', 1, 'shoes sandals', 12),
            (16, 'Sports', 'SPORTS', 1, 'sports items', None),
            (17, 'Fitness Equipment', 'FITNESS', 1, 'gym fitness', 16),
            (18, 'Books', 'BOOKS', 1, 'books novels education', None),
            (19, 'Stationery', 'STAT', 1, 'office stationery', 18),
            (20, 'Gaming', 'GAMING', 1, 'gaming consoles', None),
            (21, 'Gaming Consoles', 'GAMECON', 1, 'playstation xbox', 20),
            (22, 'Gaming Accessories', 'GAMEACC', 1, 'controllers headsets', 20),
            (23, 'Audio', 'AUDIO', 1, 'audio devices', None),
            (24, 'Headphones', 'HEADPH', 1, 'wired wireless headphones', 23),
            (25, 'Speakers', 'SPEAK', 1, 'bluetooth speakers', 23),
            (26, 'Cameras', 'CAM', 1, 'digital cameras', None),
            (27, 'DSLR Cameras', 'DSLR', 1, 'dslr cameras', 26),
            (28, 'Watches', 'WATCH', 1, 'smart watches', None),
            (29, 'Smart Watches', 'SWATCH', 1, 'fitness watches', 28),
            (30, 'Beauty', 'BEAUTY', 1, 'beauty products', None),
            (31, 'Skin Care', 'SKIN', 1, 'skin care products', 30),
            (32, 'Hair Care', 'HAIR', 1, 'hair care products', 30),
            (33, 'Health', 'HEALTH', 1, 'health products', None),
            (34, 'Medical Devices', 'MEDDEV', 1, 'medical tools', 33),
            (35, 'Automotive', 'AUTO', 1, 'vehicle accessories', None),
            (36, 'Car Accessories', 'CARACC', 1, 'car accessories', 35),
            (37, 'Tools', 'TOOLS', 1, 'hardware tools', None),
            (38, 'Power Tools', 'PTOOLS', 1, 'electric tools', 37),
            (39, 'Home Decor', 'HOMED', 1, 'home decoration', None),
            (40, 'Lighting', 'LIGHT', 1, 'lights lamps', 39),
            (41, 'Toys', 'TOYS', 1, 'kids toys', None),
            (42, 'Educational Toys', 'EDTOY', 1, 'learning toys', 41),
            (43, 'Pet Supplies', 'PET', 1, 'pet food toys', None),
            (44, 'Dog Supplies', 'DOG', 1, 'dog food toys', 43),
            (45, 'Garden', 'GARDEN', 1, 'garden tools', None),
            (46, 'Outdoor Furniture', 'OUTFURN', 1, 'outdoor furniture', 45),
            (47, 'Jewelry', 'JEWEL', 1, 'gold silver jewelry', None),
            (48, 'Perfumes', 'PERF', 1, 'fragrances perfumes', None),
            (49, 'Storage', 'STOR', 1, 'storage devices', None),
            (50, 'Networking', 'NET', 1, 'network devices', 49),
        ]

        for cid, name, code, status, keywords, parent_id in categories:
            parent = Category.objects.filter(id=parent_id).first() if parent_id else None

            obj, created = Category.objects.update_or_create(
                code=code.strip().upper(),   # ✅ LOOKUP FIELD
                defaults={
                    "name": name,
                    "status": status,
                    "search_keywords": keywords,
                    "parent": parent,
                    "slug": slugify(name),
                }
            )

            self.stdout.write(
                f"{'Inserted' if created else 'Updated'} Category: {obj.name} | Parent: {parent.name if parent else 'ROOT'}"
            )

        # --------------------------
        # ProductType data
        # --------------------------
        product_types = [
            (1,'Standard','STD',1,'standard type','standard'),
            (2,'Digital','DIGI',1,'digital products','digital'),
            (3,'Service','SERV',1,'services','service'),
            (4,'Subscription','SUB',1,'subscription','subscription'),
            (5,'Bundle','BNDL',1,'bundle packs','bundle'),
            (6,'Premium','PREM',1,'premium products','premium'),
            (7,'Economy','ECON',1,'budget products','economy'),
            (8,'Limited Edition','LTD',1,'limited edition','limited-edition'),
            (9,'Exclusive','EXCL',1,'exclusive items','exclusive'),
            (10,'Refurbished','REF',1,'refurbished products','refurbished'),
            (11,'Custom','CUST',1,'custom products','custom'),
            (12,'Imported','IMP',1,'imported goods','imported'),
            (13,'Exported','EXP',1,'exported items','exported'),
            (14,'Seasonal','SEAS',1,'seasonal products','seasonal'),
            (15,'Clearance','CLR',1,'clearance sale','clearance'),
            (16,'Organic','ORG',1,'organic products','organic'),
            (17,'Handmade','HAND',1,'handmade goods','handmade'),
            (18,'Eco-Friendly','ECO',1,'eco friendly','eco-friendly'),
            (19,'Luxury','LUX',1,'luxury items','luxury'),
            (20,'Smart','SMART',1,'smart devices','smart'),
            (21,'Portable','PORT',1,'portable devices','portable'),
            (22,'Stationery','STAT',1,'office stationery','stationery'),
            (23,'Accessory','ACC',1,'product accessory','accessory'),
            (24,'Furniture','FURN',1,'furniture type','furniture'),
            (25,'Appliance','APP',1,'home appliance','appliance'),
            (26,'Toy','TOY',1,'toy product','toy'),
            (27,'Beauty','BEAUTY',1,'beauty type','beauty'),
            (28,'Automotive','AUTO',1,'auto product','automotive'),
            (29,'Sports','SPORTS',1,'sporting products','sports'),
            (30,'Garden','GARD',1,'garden type','garden'),
            (31,'Music','MUSIC',1,'musical items','music'),
            (32,'Health','HEALTH',1,'health products','health'),
            (33,'Baby','BABY',1,'baby products','baby'),
            (34,'Pet','PET',1,'pet products','pet'),
            (35,'Electronics','ELEC',1,'electronics','electronics'),
            (36,'Camera','CAM',1,'camera type','camera'),
            (37,'Audio','AUD',1,'audio type','audio'),
            (38,'Video','VID',1,'video type','video'),
            (39,'Smartwatch','SWATCH',1,'smartwatch','smartwatch'),
            (40,'Laptop','LAP',1,'laptop','laptop'),
            (41,'Mobile','MOB',1,'mobile','mobile'),
            (42,'Tablet','TAB',1,'tablet','tablet'),
            (43,'Accessory Premium','ACCP',1,'premium accessory','accessory-premium'),
            (44,'DIY Kit','DIYK',1,'do it yourself kit','diy-kit'),
            (45,'Home Decor','HDEC',1,'home decoration','home-decor'),
            (46,'Collectible','COLL',1,'collectible item','collectible'),
            (47,'Tool','TOOL',1,'tool item','tool'),
            (48,'Gadget','GAD',1,'gadget','gadget'),
            (49,'Furniture Premium','FURNP',1,'premium furniture','furniture-premium'),
            (50,'Kitchenware','KIT',1,'kitchen items','kitchenware'),
        ]

        for id, name, code, status, keywords, slug in product_types:
            obj, created = ProductType.objects.update_or_create(
                id=id,
                defaults={
                    'name': name,
                    'code': code,
                    'status': status,
                    'search_keywords': keywords,
                    'slug': slugify(slug)
                }
            )
            self.stdout.write(f"{'Inserted' if created else 'Updated'} ProductType: {obj.name}")

        self.stdout.write(self.style.SUCCESS("All ProductTypes processed."))

        # --------------------------
        # Brand Data
        # --------------------------

        brands = [
            (1,'Zenith','ZEN',1,'zenith brand','zenith'),
            (2,'Apex','APX',1,'apex brand','apex'),
            (3,'Vertex','VERT',1,'vertex brand','vertex'),
            (4,'Omni','OMNI',1,'omni brand','omni'),
            (5,'Nova','NOVA',1,'nova brand','nova'),
            (6,'Echo','ECHO',1,'echo brand','echo'),
            (7,'Pinnacle','PIN',1,'pinnacle','pinnacle'),
            (8,'Fusion','FUS',1,'fusion','fusion'),
            (9,'Pulse','PULSE',1,'pulse','pulse'),
            (10,'Cosmo','COS',1,'cosmo','cosmo'),
            (11,'Alpha','ALPHA',1,'alpha brand','alpha'),
            (12,'Beta','BETA',1,'beta brand','beta'),
            (13,'Gamma','GAMMA',1,'gamma brand','gamma'),
            (14,'Delta','DEL',1,'delta brand','delta'),
            (15,'Omega','OMEGA',1,'omega brand','omega'),
            (16,'Sigma','SIG',1,'sigma brand','sigma'),
            (17,'Epsilon','EPS',1,'epsilon brand','epsilon'),
            (18,'Zeta','ZETA',1,'zeta brand','zeta'),
            (19,'Theta','THETA',1,'theta brand','theta'),
            (20,'Kappa','KAPPA',1,'kappa brand','kappa'),
            (21,'Lambda','LAMBDA',1,'lambda brand','lambda'),
            (22,'Mu','MU',1,'mu brand','mu'),
            (23,'Nu','NU',1,'nu brand','nu'),
            (24,'Xi','XI',1,'xi brand','xi'),
            (25,'Omicron','OMIC',1,'omicron brand','omicron'),
            (26,'Pi','PI',1,'pi brand','pi'),
            (27,'Rho','RHO',1,'rho brand','rho'),
            (28,'Tau','TAU',1,'tau brand','tau'),
            (29,'Upsilon','UPS',1,'upsilon brand','upsilon'),
            (30,'Phi','PHI',1,'phi brand','phi'),
            (31,'Chi','CHI',1,'chi brand','chi'),
            (32,'Psi','PSI',1,'psi brand','psi'),
            (33,'AlphaTech','ALPHATECH',1,'alpha tech brand','alphatech'),
            (34,'BetaTech','BETATECH',1,'beta tech brand','betatech'),
            (35,'GammaTech','GAMMATECH',1,'gamma tech brand','gammatech'),
            (36,'DeltaTech','DELTATECH',1,'delta tech brand','deltatech'),
            (37,'OmegaTech','OMEGATECH',1,'omega tech brand','omegatech'),
            (38,'SigmaTech','SIGMATECH',1,'sigma tech brand','sigmatech'),
            (39,'EpsilonTech','EPSILONTECH',1,'epsilon tech','epsilontech'),
            (40,'ZetaTech','ZETATECH',1,'zeta tech','zetatech'),
            (41,'ThetaTech','THETATECH',1,'theta tech','thetatech'),
            (42,'KappaTech','KAPPATECH',1,'kappa tech','kappatech'),
            (43,'LambdaTech','LAMBDATECH',1,'lambda tech','lambdatech'),
            (44,'MuTech','MUTECH',1,'mu tech','mutech'),
            (45,'NuTech','NUTECH',1,'nu tech','nutech'),
            (46,'XiTech','XITECH',1,'xi tech','xitech'),
            (47,'OmicronTech','OMICRONTECH',1,'omicron tech','omicrontech'),
            (48,'PiTech','PITECH',1,'pi tech','pitech'),
            (49,'RhoTech','RHOTECH',1,'rho tech','rhotech'),
            (50,'TauTech','TAUTECH',1,'tau tech','tautech'),
        ]

        for b in brands:
            Brand.objects.update_or_create(
                id=b[0],
                defaults={
                    "name": b[1],
                    "code": b[2],
                    "status": b[3],
                    "search_keywords": b[4],
                    "slug": b[5]
                }
            )
        self.stdout.write(self.style.SUCCESS('Inserted 50 brands'))

        # --------------------------
        # LANGUAGES Data
        # --------------------------
        languages = [
            (1,'English','en',1,'english','english'),
            (2,'Spanish','es',1,'spanish','spanish'),
            (3,'French','fr',1,'french','french'),
            (4,'German','de',1,'german','german'),
            (5,'Hindi','hi',1,'hindi','hindi'),
            (6,'Mandarin','zh',1,'mandarin','mandarin'),
            (7,'Arabic','ar',1,'arabic','arabic'),
            (8,'Portuguese','pt',1,'portuguese','portuguese'),
            (9,'Bengali','bn',1,'bengali','bengali'),
            (10,'Russian','ru',1,'russian','russian'),
            (11,'Japanese','ja',1,'japanese','japanese'),
            (12,'Punjabi','pa',1,'punjabi','punjabi'),
            (13,'Javanese','jv',1,'javanese','javanese'),
            (14,'Korean','ko',1,'korean','korean'),
            (15,'Vietnamese','vi',1,'vietnamese','vietnamese'),
            (16,'Telugu','te',1,'telugu','telugu'),
            (17,'Marathi','mr',1,'marathi','marathi'),
            (18,'Tamil','ta',1,'tamil','tamil'),
            (19,'Urdu','ur',1,'urdu','urdu'),
            (20,'Turkish','tr',1,'turkish','turkish'),
            (21,'Italian','it',1,'italian','italian'),
            (22,'Thai','th',1,'thai','thai'),
            (23,'Gujarati','gu',1,'gujarati','gujarati'),
            (24,'Kannada','kn',1,'kannada','kannada'),
            (25,'Polish','pl',1,'polish','polish'),
            (26,'Ukrainian','uk',1,'ukrainian','ukrainian'),
            (27,'Persian','fa',1,'persian','persian'),
            (28,'Malay','ms',1,'malay','malay'),
            (29,'Sinhala','si',1,'sinhala','sinhala'),
            (30,'Burmese','my',1,'burmese','burmese'),
            (31,'Dutch','nl',1,'dutch','dutch'),
            (32,'Romanian','ro',1,'romanian','romanian'),
            (33,'Greek','el',1,'greek','greek'),
            (34,'Czech','cs',1,'czech','czech'),
            (35,'Hungarian','hu',1,'hungarian','hungarian'),
            (36,'Swedish','sv',1,'swedish','swedish'),
            (37,'Norwegian','no',1,'norwegian','norwegian'),
            (38,'Finnish','fi',1,'finnish','finnish'),
            (39,'Danish','da',1,'danish','danish'),
            (40,'Hebrew','he',1,'hebrew','hebrew'),
            (41,'Malayalam','ml',1,'malayalam','malayalam'),
            (42,'Odia','or',1,'odia','odia'),
            (43,'Assamese','as',1,'assamese','assamese'),
            (44,'Maori','mi',1,'maori','maori'),
            (45,'Swahili','sw',1,'swahili','swahili'),
            (46,'Zulu','zu',1,'zulu','zulu'),
            (47,'Xhosa','xh',1,'xhosa','xhosa'),
            (48,'Igbo','ig',1,'igbo','igbo'),
            (49,'Hausa','ha',1,'hausa','hausa'),
            (50,'Filipino','fil',1,'filipino','filipino')
        ]

        for l in languages:
            Languages.objects.update_or_create(
                id=l[0],
                defaults={
                    "name": l[1],
                    "code": l[2],
                    "status": l[3],
                    "search_keywords": l[4],
                    "slug": l[5]
                }
            )
        self.stdout.write(self.style.SUCCESS('Inserted 50 languages'))
        # --------------------------
        # PRODUCT GROUPS Data
        # --------------------------
        product_groups = [
            (1,'Smartphones','SPHN',1,'smartphones','smartphones'),
            (2,'Laptops','LAPT',1,'laptops','laptops'),
            (3,'Tablets','TAB',1,'tablets','tablets'),
            (4,'Headphones','HEAD',1,'headphones','headphones'),
            (5,'Speakers','SPKR',1,'speakers','speakers'),
            (6,'Monitors','MON',1,'monitors','monitors'),
            (7,'Cameras','CAM',1,'cameras','cameras'),
            (8,'Wearables','WEAR',1,'wearables','wearables'),
            (9,'Printers','PRNT',1,'printers','printers'),
            (10,'Networking','NET',1,'networking devices','networking'),
            (11,'Home Audio','HAUD',1,'home audio','home-audio'),
            (12,'Gaming Consoles','GAME',1,'gaming consoles','gaming-consoles'),
            (13,'Smart Home','SHOME',1,'smart home','smart-home'),
            (14,'Kitchen Appliances','KITCH',1,'kitchen appliances','kitchen-appliances'),
            (15,'Furniture','FURN',1,'home furniture','furniture'),
            (16,'Toys','TOYS',1,'toys','toys'),
            (17,'Office Supplies','OFF',1,'office supplies','office-supplies'),
            (18,'Books','BOOK',1,'books','books'),
            (19,'Sports Equipment','SPORT',1,'sports equipment','sports-equipment'),
            (20,'Beauty','BEAUTY',1,'beauty products','beauty'),
            (21,'Health Care','HEALTH',1,'health care','health-care'),
            (22,'Automotive','AUTO',1,'automotive items','automotive'),
            (23,'Jewelry','JEWEL',1,'jewelry','jewelry'),
            (24,'Footwear','FOOT',1,'footwear','footwear'),
            (25,'Bedding','BED',1,'bedding','bedding'),
            (26,'Lighting','LIGHT',1,'lighting','lighting'),
            (27,'Gardening','GARD',1,'gardening','gardening'),
            (28,'Pet Supplies','PET',1,'pet supplies','pet-supplies'),
            (29,'Musical Instruments','MUSIC',1,'musical instruments','musical-instruments'),
            (30,'Art Supplies','ART',1,'art supplies','art-supplies'),
            (31,'Stationery','STAT',1,'stationery','stationery'),
            (32,'DIY','DIY',1,'diy products','diy'),
            (33,'Smart Accessories','SACC',1,'smart accessories','smart-accessories'),
            (34,'Phone Accessories','PACC',1,'phone accessories','phone-accessories'),
            (35,'Laptop Accessories','LACC',1,'laptop accessories','laptop-accessories'),
            (36,'Camera Accessories','CACC',1,'camera accessories','camera-accessories'),
            (37,'Audio Accessories','AACC',1,'audio accessories','audio-accessories'),
            (38,'Video Accessories','VACC',1,'video accessories','video-accessories'),
            (39,'Outdoor Gear','OUT',1,'outdoor gear','outdoor-gear'),
            (40,'Seasonal','SEAS',1,'seasonal items','seasonal'),
            (41,'Collectibles','COLL',1,'collectibles','collectibles'),
            (42,'Luxury Items','LUX',1,'luxury items','luxury-items'),
            (43,'Refurbished Items','REF',1,'refurbished','refurbished-items'),
            (44,'Organic Products','ORG',1,'organic products','organic-products'),
            (45,'Handmade','HAND',1,'handmade','handmade'),
            (46,'Eco-Friendly','ECO',1,'eco-friendly','eco-friendly'),
            (47,'Limited Edition','LTD',1,'limited edition','limited-edition'),
            (48,'Premium Furniture','PFURN',1,'premium furniture','premium-furniture'),
            (49,'Cookware','COOK',1,'cookware','cookware'),
            (50,'Home Decor','HDEC',1,'home decor','home-decor')
        ]

        for pg in product_groups:
            ProductGroup.objects.update_or_create(
                id=pg[0],
                defaults={
                    "name": pg[1],
                    "code": pg[2],
                    "status": pg[3],
                    "search_keywords": pg[4],
                    "slug": pg[5]
                }
            )
        self.stdout.write(self.style.SUCCESS('Inserted 50 product groups'))
        # --------------------------
        # MANUFACTURERS Data
        # --------------------------
        manufacturers = [
            (1,'Samsung','SAM',1,'samsung electronics','samsung'),
            (2,'Apple','APL',1,'apple electronics','apple'),
            (3,'Sony','SON',1,'sony electronics','sony'),
            (4,'LG','LG',1,'lg electronics','lg'),
            (5,'Dell','DEL',1,'dell computers','dell'),
            (6,'HP','HP',1,'hp computers','hp'),
            (7,'Lenovo','LEN',1,'lenovo computers','lenovo'),
            (8,'Asus','ASUS',1,'asus computers','asus'),
            (9,'Acer','ACER',1,'acer computers','acer'),
            (10,'Microsoft','MS',1,'microsoft software','microsoft'),
            (11,'Google','GOO',1,'google','google'),
            (12,'Panasonic','PAN',1,'panasonic electronics','panasonic'),
            (13,'Canon','CAN',1,'canon cameras','canon'),
            (14,'Nikon','NIK',1,'nikon cameras','nikon'),
            (15,'Bose','BOSE',1,'bose audio','bose'),
            (16,'JBL','JBL',1,'jbl audio','jbl'),
            (17,'Beats','BEATS',1,'beats audio','beats'),
            (18,'Fujifilm','FUJI',1,'fujifilm cameras','fujifilm'),
            (19,'Huawei','HUA',1,'huawei phones','huawei'),
            (20,'Xiaomi','XIA',1,'xiaomi phones','xiaomi'),
            (21,'OnePlus','ONEP',1,'oneplus phones','oneplus'),
            (22,'Oppo','OPP',1,'oppo phones','oppo'),
            (23,'Vivo','VIVO',1,'vivo phones','vivo'),
            (24,'Motorola','MOT',1,'motorola phones','motorola'),
            (25,'Lenox','LNX',1,'lenox appliances','lenox'),
            (26,'Whirlpool','WHI',1,'whirlpool appliances','whirlpool'),
            (27,'Philips','PHI',1,'philips appliances','philips'),
            (28,'KitchenAid','KA',1,'kitchenaid appliances','kitchenaid'),
            (29,'Rolex','ROLEX',1,'rolex watches','rolex'),
            (30,'Casio','CAS',1,'casio watches','casio'),
            (31,'Timex','TIM',1,'timex watches','timex'),
            (32,'Nike','NIKE',1,'nike shoes','nike'),
            (33,'Adidas','ADID',1,'adidas shoes','adidas'),
            (34,'Puma','PUMA',1,'puma shoes','puma'),
            (35,'Reebok','REEB',1,'reebok shoes','reebok'),
            (36,'Under Armour','UA',1,'under armour','under-armour'),
            (37,'Fossil','FOS',1,'fossil jewelry','fossil'),
            (38,'Tiffany','TIFF',1,'tiffany jewelry','tiffany'),
            (39,'Cartier','CART',1,'cartier jewelry','cartier'),
            (40,'Gucci','GUCCI',1,'gucci jewelry','gucci'),
            (41,'Hugo Boss','HUG',1,'hugo boss fashion','hugo-boss'),
            (42,'Ralph Lauren','RL',1,'ralph lauren fashion','ralph-lauren'),
            (43,'Levi','LEVI',1,'levi fashion','levi'),
            (44,'Gap','GAP',1,'gap clothing','gap'),
            (45,'Uniqlo','UNI',1,'uniqlo clothing','uniqlo'),
            (46,'Ikea','IKEA',1,'ikea furniture','ikea'),
            (47,'Home Depot','HDEP',1,'home depot','home-depot'),
            (48,'Leroy Merlin','LM',1,'leroy merlin','leroy-merlin'),
            (49,'Bosch','BOSCH',1,'bosch appliances','bosch'),
            (50,'Siemens','SIEM',1,'siemens appliances','siemens')
        ]

        for m in manufacturers:
            Manufacturer.objects.update_or_create(
                id=m[0],
                defaults={
                    "name": m[1],
                    "code": m[2],
                    "status": m[3],
                    "search_keywords": m[4],
                    "slug": m[5]
                }
            )
        self.stdout.write(self.style.SUCCESS('Inserted 50 manufacturers'))

        # --------------------------
        # VENDOR Types
        # --------------------------
        # Real-world vendor types with descriptions (100 different types)
        vendor_types = [
            ("Manufacturer", "A company that manufactures goods from raw materials."),
            ("Distributor", "A business that buys products from manufacturers and sells them to retailers."),
            ("Retailer", "A business that sells goods directly to consumers."),
            ("Wholesaler", "A business that sells products in bulk to retailers."),
            ("Service Vendor", "A company providing specialized services to other businesses."),
            ("Logistics Provider", "A company handling the transportation and storage of goods."),
            ("Technology Provider", "A company that sells technology-related products or services."),
            ("Consultancy", "A company offering expert advice in a particular field."),
            ("Healthcare Supplier", "A business that provides medical supplies and equipment."),
            ("Food Supplier", "A company that supplies raw and processed food products."),
            ("Energy Supplier", "A company providing energy like electricity, gas, or renewable energy."),
            ("Telecommunications", "A company providing phone and internet services."),
            ("Finance Vendor", "A company offering financial products or services to businesses."),
            ("Legal Services", "A firm that provides legal services to individuals or organizations."),
            ("Insurance Provider", "A company providing various types of insurance products."),
            ("Construction Vendor", "A company supplying construction materials and services."),
            ("Automotive Supplier", "A company that provides parts and accessories for the automotive industry."),
            ("Textile Supplier", "A company that supplies fabrics and textile products."),
            ("Packaging Vendor", "A business that provides packaging solutions for products."),
            ("Raw Materials Supplier", "A vendor supplying raw materials for manufacturing."),
            ("Import/Export Vendor", "A business specializing in the import and export of goods."),
            ("Temporary Vendor", "A vendor contracted for a short-term or project-specific task."),
            ("Internal Vendor", "A company that provides services or goods internally within the same organization."),
            ("Environmental Services", "A company offering solutions related to waste management, recycling, and environmental sustainability."),
            ("Security Services", "A business offering physical and cybersecurity services."),
            ("Cleaning Services", "A company providing commercial and residential cleaning services."),
            ("Printing Vendor", "A company that offers printing services for businesses or consumers."),
            ("Transportation", "A business providing transportation services like freight and passenger transport."),
            ("Real Estate Services", "A vendor offering services related to the sale, purchase, and management of real estate."),
            ("IT Support Vendor", "A company that provides IT services, such as software support, hardware maintenance, etc."),
            ("Advertising Agency", "A firm that provides advertising and marketing services to businesses."),
            ("Publishing Vendor", "A company that publishes books, newspapers, magazines, and other media."),
            ("Agricultural Supplier", "A business that provides agricultural products, tools, and services."),
            ("Wholesale Distributor", "A vendor that distributes goods in large quantities to businesses."),
            ("Medical Equipment Supplier", "A business supplying medical devices and instruments."),
            ("Hospitality Services", "A company offering services like hotel accommodations, food services, etc."),
            ("Event Management", "A company specializing in organizing and managing events."),
            ("Software Vendor", "A company that provides software solutions, including SaaS and enterprise software."),
            ("Hardware Supplier", "A company that provides hardware products like computers, machines, etc."),
            ("Retail Management Systems", "A company offering software and systems for managing retail operations."),
            ("Laboratory Equipment Supplier", "A company providing scientific and laboratory equipment."),
            ("Packaging Material Supplier", "A company providing packaging materials like boxes, wraps, and containers."),
            ("Furniture Supplier", "A company supplying office and home furniture."),
            ("Cleaning Equipment Supplier", "A business that provides industrial-grade cleaning equipment."),
            ("Security Equipment Supplier", "A company providing security systems like cameras, alarms, etc."),
            ("Waste Management", "A company providing waste disposal and recycling services."),
            ("Advertising Materials Supplier", "A company providing advertising materials such as banners, flyers, and digital ads."),
            ("Entertainment Services", "A company providing entertainment services such as music, theater, etc."),
            ("Business Consulting", "A business that provides strategic advice to other businesses."),
            ("Freight Forwarding", "A business that manages the shipment of goods for customers."),
            ("Courier Services", "A company that provides quick, reliable shipping and delivery services."),
            ("Cleaning Supplies", "A vendor that provides cleaning chemicals, tools, and supplies."),
            ("Food Packaging", "A company that specializes in packaging food products."),
            ("Security Services Vendor", "A vendor that provides physical or cyber security services."),
            ("Distribution Management", "A company providing solutions for distribution logistics and management."),
            ("R&D Vendor", "A business that provides research and development services for companies."),
            ("Professional Training Services", "A company that offers corporate or professional training programs."),
            ("Utility Supplier", "A company that provides utilities like water, gas, and electricity."),
            ("Real Estate Developer", "A business that develops residential, commercial, or industrial properties."),
            ("Chemical Supplier", "A company that supplies chemicals for industrial, agricultural, or scientific use."),
            ("Plastic Supplier", "A business that supplies plastic materials for manufacturing."),
            ("Metal Supplier", "A company providing metal products such as steel, copper, aluminum."),
            ("Luxury Goods Supplier", "A company that supplies high-end, luxury goods like watches, jewelry, etc."),
            ("Building Materials Supplier", "A vendor that supplies materials like cement, bricks, tiles."),
            ("Printing and Packaging", "A business that handles both printing and packaging of products."),
            ("Fleet Services", "A company offering fleet management services for vehicles."),
            ("Pet Supplies", "A business that supplies pet products and services."),
            ("Apparel Supplier", "A company that provides clothing and textile products."),
            ("Bulk Supplier", "A vendor that supplies products in bulk for resellers."),
            ("Tool Supplier", "A business that provides tools and machinery for various industries."),
            ("Petroleum Supplier", "A company providing oil, gas, and other petroleum products."),
            ("Heavy Equipment Supplier", "A business providing machinery and equipment for construction and mining."),
            ("Mobile Vendor", "A business providing mobile products and services."),
            ("Office Equipment Supplier", "A company supplying office furniture and equipment."),
            ("Healthcare Consultant", "A vendor providing consultancy services to healthcare providers."),
            ("B2B Software Vendor", "A company offering software solutions designed for business-to-business transactions."),
            ("Furniture Manufacturer", "A vendor involved in the production and supply of furniture."),
            ("Construction Services", "A company providing construction and engineering services."),
            ("Property Maintenance", "A business offering property maintenance services like repairs and cleaning."),
            ("Audio-Visual Supplier", "A company providing audio and visual equipment for businesses and events."),
            ("Luxury Vehicle Supplier", "A vendor providing high-end and luxury vehicles."),
            ("Chemical Distributor", "A company that distributes chemical products to industries."),
            ("Wholesale Supplier", "A business providing wholesale products to retailers and other vendors."),
            ("Green Energy Supplier", "A company that provides renewable energy solutions like solar, wind."),
            ("Data Storage Services", "A vendor offering data storage and cloud services."),
            ("Metal Fabrication", "A company specializing in the process of metalworking and fabrication."),
            ("Furniture Retailer", "A vendor that sells furniture directly to consumers."),
            ("Packaging Design", "A company offering packaging design services for products."),
            ("Industrial Equipment Supplier", "A vendor providing industrial machinery and tools."),
            ("Construction Materials", "A company supplying raw materials used in construction projects."),
            ("Warehouse Services", "A company providing warehouse management and storage solutions."),
            ("Insurance Vendor", "A company providing a variety of insurance products to individuals and businesses."),
            ("Paper Supplier", "A business supplying paper products for commercial and industrial use."),
            ("Bulk Goods Supplier", "A company that provides bulk goods like grains, chemicals, etc."),
            ("Building Maintenance", "A company that provides maintenance services for buildings and facilities."),
            ("Printing Solutions", "A company providing printing solutions for businesses."),
            ("Petroleum Supplier", "A company providing oil and gas for industrial and consumer use."),
            ("Wholesale Electronics", "A company providing electronics and gadgets at wholesale prices."),
            ("Furniture Retailer", "A business selling furniture to consumers directly."),
            ("Building Automation", "A vendor offering systems for automating building processes."),
            ("Farm Equipment Supplier", "A company providing agricultural machinery and equipment."),
            ("Travel Services", "A company providing travel-related services for businesses or individuals."),
            ("Plastic Products Supplier", "A vendor supplying plastic products for manufacturing.")
        ]

        # Generate 100 records
        for i in range(1, 101):
            # Randomly choose from the vendor types
            vendor_type_name, description = random.choice(vendor_types)
            
            # Generate the code with the prefix 'VT-' followed by a unique identifier
            code = f"VT-{vendor_type_name[:3].upper()}-{i:03d}"  # Example: VT-MAN-001, VT-DIS-002, etc.
            
            # Determine status: Randomly set Active (1) or Inactive (0)
            status = random.choice([0, 1])  # 1 for Active, 0 for Inactive
            
            # Check if VendorType with this name already exists to avoid duplicates
            if VendorType.objects.filter(name=vendor_type_name).exists():
                print(f"VendorType with name {vendor_type_name} already exists.")
                continue  # Skip creating this vendor type if it already exists

            # Create the vendor type
            try:
                VendorType.objects.create(
                    name=vendor_type_name,
                    code=code,
                    status=status,
                    description=description
                )
                print(f"VendorType '{vendor_type_name}' with code '{code}' created successfully.")
            except IntegrityError as e:
                print(f"Failed to create VendorType '{vendor_type_name}' with code '{code}' due to integrity error: {e}")

        self.stdout.write(self.style.SUCCESS('Successfully generated 100 real-time VendorType data with name, code, status, and description.'))

        self.stdout.write(self.style.SUCCESS("All catalog data processed successfully."))
