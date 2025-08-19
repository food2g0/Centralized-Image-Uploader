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
    "ALEXITE (J)", "GOLDSTAR ATLANTIC", "GOOD QUALITY ASSURANCE", "HOMENEEDS",
    "INTER WORLD GEM", "KRISTAL CLEAR DIAMOND (J)", "MONEYMAX", "MULTIGAINED",
    "PRIMARY MAX", "PRINCESS CUT (J)", "SAFELOCK",
    "SUREPLEDGE", "UNIWORLD-ASIA", "YELLOW ENDURANCE", "ATLANTIC STARGEM",
    "GALLIUM GRANITE", "GOLD BARS", "GREEN AMBER (J)",
    "KING-ASIA GROUP", "KRYPTON KNIGHT", "MAXI-WEALTH", "METROGOLD STAR",
    "NORTH-WESTERN PACIFIC", "PACIFIC METROSTAR", "PUREGOLD KARAT",
    "SAN SEBASTIAN SILVER", "WORLDCREST", "WORLDGEM",
    "ASIAPHIL STAR", "MAJOREVIM", "MEGAWORLD DOMESTIC", "NORTHERN SUNSTAR",
    "SAINT BARBARA PRIME", "SAN RAMON PLATINUM", "SILVERSTAR (J)"
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
            "BIR 1601 EQ (expanded rent)",
            "Alphalist Data Entry (1601EQ) rental",
            "BIR 1702Q (Income Tax)",
            "QVVR",
            "Gross Income for Business Permit",
            "BIR 1604C",
            "Alphalist Data Entry (1604E)",
            "BIR 2316 (emp ITR)",
            "BIR 1702RT (ITR/FS)",
            "SEC",
            "BSP",
            "BIR",
            "Books of Account"
        ],
        "sub_categories": {
            "Books of Account": ["Journal", "Ledger", "Cash Receipt", "Cash Disbursement"]
        }
    },
    "HR Department": {
        "icon": "👥",
        "transactions": [
            "Pre - Employment Requirements",
            "Disciplinary Actions",
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
        ],
        "sub_categories": {
            "201 FILE": [
                "Employment Contract",
                "Resignation",
                "Termination",
                "Job Description",
            ]
        }
    },
    "Cash Management Department": {
        "icon": "💰",
        "transactions": [
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
            "ADVANCES FROM OFFICERS"
        ],
        "sub_categories": {
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
                " Entom (pest control verdana)",
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
            "PERMITS",
            "STB",
            "MTPP"
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
            "MC Trading report with SI from Jayhana"
        ],
     
    },
    "IT Department": {
        "icon": "💻",
        "transactions": [
            "System Maintenance",
            "Software Installation",
            "Hardware Setup",
            "Network Configuration",
            "Database Backup",
            "Security Updates",
            "Technical Support",
            "Equipment Procurement"
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
                "Audit Findings"
            ],
            "Internal Audit": [
                "Action Plan",
                "Audit Report",
                "GAP Analysis",
                "Turnover of Records"
            ]
        }
    },
    "Purchasing Department": {
        "icon": "💻",
        "transactions": [
            "Requisition Purchase",
            "Monthly Inventory Report",
            
        ],
        "sub_categories": {}
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
    
}