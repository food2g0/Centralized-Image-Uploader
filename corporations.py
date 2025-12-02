group1_corporations = {
        "ATLANTIC STARGEM", "GALLIUM GRANITE", "GOLD BARS", "GREEN AMBER (J)",
        "KING-ASIA GROUP", "KRYPTON KNIGHT", "MAXI-WEALTH", "METROGOLD STAR",
        "NORTH-WESTERN PACIFIC", "PACIFIC METROSTAR", "PUREGOLD KARAT",
        "SAN SEBASTIAN SILVER", "WORLDCREST", "WORLDGEM"
    }

group2_corporations = {
   "ASIAPHIL STAR", "MAJOREVIM", "MEGAWORLD DOMESTIC", "NORTHERN SUNSTAR",
        "SAINT BARBARA PRIME", "SAN RAMON PLATINUM", "SILVERSTAR (J)"
    }
group3_corporations = {
        "ALEXITE (J)", "GOLDSTAR ATLANTIC", "GOOD QUALITY ASSURANCE", "HOMENEEDS",
        "INTER WORLD GEM", "KRISTAL CLEAR DIAMOND (J)", "MONEYMAX", "MULTIGAINED",
        "PRIMARY MAX", "PRINCESS CUT (J)", "SAFELOCK",
        "SUREPLEDGE", "UNIWORLD-ASIA", "YELLOW ENDURANCE"
    }


CORPORATIONS = [
    "NONE",
    "ALEXITE JEWELRY PAWNSHOP INC.",
    "GOLDSTAR ATLANTIC PAWNSHOP INC.",
    "GOOD QUALITY ASSURANCE PAWNSHOP INC.",
    "HOMENEEDS PAWNSHOP INC.",
    "INTER WORLD GEM PAWNSHOP INC.",
    "KRISTAL CLEAR DIAMOND & GOLD PAWNSHOP INC.",
    "MONEYMAX PAWNSHOP INC.",
    "MULTIGAINED PAWNSHOP INC.",
    "PRIMARY MAX PAWNSHOP INC.",
    "PRINCESS CUT JEWELRY AND PAWNSHOP INC.",
    "SAFELOCK PAWNSHOP INC.",
    "SUREPLEDGE PAWNSHOP INC.",
    "UNIWORLD-ASIA PAWNSHOP INC.",
    "YELLOW ENDURANCE PAWNSHOP INC.",
    "ATLANTIC STARGEM PAWNSHOP INC.",
    "GALLIUM GRANITE PAWNSHOP INC.",
    "GOLD BARS PAWNSHOP INC.",
    "GREEN AMBER JEWELRY AND PAWNSHOP INC.",
    "KING-ASIA GROUP PAWNSHOP INC.",
    "KRYPTON KNIGHT PAWNSHOP INC.",
    "MAXI-WEALTH PAWNSHOP INC.",
    "METROGOLD STAR PAWNSHOP INC.",
    "NORTH-WESTERN PACIFIC PAWNSHOP INC.",
    "PACIFIC METROSTAR PAWNSHOP INC.",
    "PUREGOLD KARAT PAWNSHOP INC.",
    "SAN SEBASTIAN SILVER PAWNSHOP INC.",
    "WORLDCREST PAWNSHOP INC.",
    "WORLDGEM PAWNSHOP INC.",
    "ASIAPHIL STAR PAWNSHOP INC.",
    "MAJOREVIM PAWNSHOP INC.",
    "MEGAWORLD DOMESTIC PAWNSHOP INC.",
    "NORTHERN SUNSTAR PAWNSHOP INC.",
    "SAINT BARBARA PRIME PAWNSHOP INC.",
    "SAN RAMON PLATINUM PAWNSHOP INC.",
    "SILVERSTAR JEWELRY PAWNSHOP INC.",
    "GLOBAL RELIANCE MANAGEMENT & HOLDINGS CORP.",
    "EUROPACIFIC MANAGEMENT & HOLDINGS CORP.",
]

DEPARTMENT_CONFIG = {
    "Accounting Department": {
        "icon": "🧮",
        "transactions": [
            "BIR 2000 (DST)",
            "BIR 1601C (Compensation)",
            "BIR 0619E (Expanded rent)",
            "Auction Sales Book",
            "ADS for auction",
            "BIR 2551Q (GRT) Rem/Auction/MC",
            "BIR 1601 EQ /Alphalist Data Entry (1601EQ)",
            "BIR 1702Q (Income Tax)",
            "QVVR",
            "Gross Income for Business Permit",
            "BIR 1604C",
            "BIR 1604E/Alphalist Data Entry (1604E)",
            "BIR 2316 (emp ITR)",
            "BIR 1702RT (ITR/FS)",
            "SEC",
            "BSP",
            "BIR",
            "2550Q (Global)",
            "Books of Account"
        ],
        "sub_categories": {
            "Books of Account": ["Journal", "Ledger", "Cash Receipt", "Cash Disbursement"]
        }
    },
    "HR Department": {
        "icon": "👥",
        "transactions": [
            "Memos",
            "DOLE Notifications / Resolutions",
            "Training Certificates",
            "Last Pay",
            "Training Materials",
            "Organizational Chart",
            "Company Policies",
            "Personal action Notice",
            "NDA",
            "201 FILE",
            "Resignation",
            "Termination",
            "Disciplinary Action / IR",

        ],
        "sub_categories": {

        }
    },
    "Cash Management A/P Department": {
        "icon": "💰",
        "transactions": [
            "RENTAL",
            "UTILITIES",
            "BIR PAYMENTS",
            "STATUTORY BENEFITS",
            "PALAWAN",
            "PALAWAN PAY",
            "GCASH",
            "INSURANCE",
            "ADS-SUBASTA",
            "SECURITY AGENCY",
            "PEST CONTROL",
            "CONSTRUCTIONS",
            "REPAIRS AND MAINTENANCE",
            "OFFICE SUPPLIES/EQUIPMENT",
            "PROFESSIONAL FEE",
            "PROPERTY TAX AND ASSO DUES",
            "BUSINESS PERMITS",
            "ADVANCES FROM OFFICERS",
            "LAST SALARIES",
            "CASH ADVANCES",
            "LIQUIDATIONS",
            "TRANSPORTATION AND TRAVE",
        ],
        "sub_categories": {
            "UTILITIES": [
                "ELECTRIC",
                "WATER",
                "INTERNET",
                "GLOBE POSTPAID"
            ],
            "BIR PAYMENTS": [
                "DST",
                "EXPANDED",
                "GRT",
                "MCIT",
                "VAT DECLARATION",
                "ITR",
            ],
            "STATUTORY BENEFITS": [
                "SSS",
                "PHILHEALTH",
                "PAG-IBIG"
            ],
            "INSURANCE": [
                "Sunlife",
                "Cocolife",
                "Philcare - HMO",
                "BDO - house insurance;",
                "Verdana",
                "BDO - insurance;",
                "Honda"
            ],
            "ADS-SUBASTA": [
                "MALAYA",
                "BALITA",
            ],
            "SECURITY AGENCY": [
                "Sforce(Guard)",
                "Itawes(Guard)",
                "El Tigre(Guard Banyan)"
            ],
            "PEST CONTROL": [
                "Homegurad",
                "Entom (pest control verdana)",
                "Pest away (pest control banyan)",
            ],
        },
    },
    "Liaison-Compliance Department": {
        "icon": "🤝",
        "transactions": [
            "GIS",
            "SEC",
            "COR",
            "BSP",
            "AMLC Certificate",
            "PERMITS",
            "STB",
            "MTPP",
            "Palawan Contract"
        ]
    },
    "Operation Department": {
        "icon": "🔧",
        "transactions": [
            "LEASE AGREEMENT",
            "GOLD RATE",
            "SECREATARY CERTIFICATE",
            "DIAMON RATE",
            "MC RATE",
            "BRANCH MEMO",
            "DAILY CASH COUNT",
            "INTER DEPARTMENT MEETING",
        ]
    },
    "MC Department": {
        "icon": "🏭",
        "transactions": [
            
            "MONTHLY REPORT",
            "MC Trading report with SI from Jayhana",
            "USD"
        ],
     
    },
    "IT Department": {
        "icon": "💻",
        "transactions": [
            "System Manual",
            "System Memo",
            "System Updates",
            "Accounts",
           
        ],
        "sub_categories": {}
    },
    "Audit Department": {
        "icon": "💻",
        "transactions": [
            "External Audit",
            "Internal Audit",
        ],
        "sub_categories": {
            "External Audit": [
                "IR",
                "Audit Findings",
                "Branch Cash Count",
                "Audit Appraisal-Jewelry",
                "Audit Appraisal-Silver",
                "Incedent Report",
                "Rematado Masterlist",
                "Checklist",
                "Inventory",
                "Audit Appraisal-Storage",
                "Sales Audit Findings",
            ],
            "Internal Audit": [
                "Action Plan",
                "Audit Report",
                "GAP Analysis",
                "Turnover of Records",
                "O.A./Fake for Salary Deduction",
                "Incident Report Penalty/Incentives",
                "Vault Combination Report/Incentives"
            
            ]
        }
    },
    "Purchasing Department": {
        "icon": "💻",
        "transactions": [
            "Purchase Order",
            "Inventory",
            
        ],
        "sub_categories": {

        }
    },
    "Executive": {
        "icon": "💻",
        "transactions": [
            "BOD Meetings",
            "Board Resolutions",
            "MOA",
            "SLA",
            "Agreements",
            "Stock Certificate",
            "Deed of sale with DST"
        ],
        "sub_categories": {}
    },

    "Cash Management A/R Department": {
        "icon": "💻",
        "transactions": [
            "Daily Bank Statement"
        ],
        "sub_categories": {

            "Daily Bank Statement": [
                "BDO",
                "BPI",
                "UNION BANK",

            ]
        }
    },
    "BDD Department": {
        "icon": "💻",
        "transactions": [
            "Gcash - Sales Invoice",
            "Sunlife Insurance - Monthly Billing",
            "Other Services Income - Monthly Income"

        ],
        "sub_categories": {}
    },
    "Payroll Department": {
        "icon": "💻",
        "transactions": [
            "SSS",
            "PAG-IBIG",
            "PHILHEALTH",
            "DTR DATABASE",
            "COR SSS",
            "PAG-IBIG SSF"

        ],
        "sub_categories": {}
    },


    
}