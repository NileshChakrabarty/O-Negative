"""
Real Indian Blood Donation Eligibility Rules

Sources:
- National Blood Transfusion Council (NBTC) guidelines
- NACO (National AIDS Control Organization) protocols
- WHO blood donation eligibility criteria

These rules are chunked for embedding and retrieval by the RAG engine.
Each rule entry includes the source for citation in agent responses.
"""

ELIGIBILITY_RULES = [
    {
        "id": "age_001",
        "text": "Blood donors must be between 18 and 65 years of age. Donors aged 18-19 require parental consent and must meet higher weight requirements (50 kg minimum). Donors over 60 may donate if they meet all other criteria and have donated before.",
        "source": "NBTC Guidelines, Section 2.1",
        "category": "Age and general eligibility"
    },
    {
        "id": "weight_001",
        "text": "Minimum body weight for blood donation in India is 50 kg. Weight is checked to ensure the donor can safely lose 350-450 ml of blood without causing adverse effects. Female donors with low body mass index should be screened more carefully.",
        "source": "NBTC Guidelines, Section 2.2",
        "category": "Physical requirements"
    },
    {
        "id": "donation_interval_001",
        "text": "A donor must wait at least 3 months (12 weeks) between whole blood donations. For apheresis procedures (platelet/plasma donation), a 2-week interval is allowed with specific frequency limits. No more than 5 donations per year per male donor; 3 donations per year for female donors.",
        "source": "NBTC Guidelines, Section 3.1",
        "category": "Donation frequency and intervals"
    },
    {
        "id": "medication_antibiotics_001",
        "text": "Donors taking antibiotics (including amoxicillin, ciprofloxacin, doxycycline) must wait 48 hours after completing the antibiotic course before donating. Donors on tetracyclines should wait 7 days after the last dose. Antibiotic duration in the body must be considered.",
        "source": "NACO Medication Guidelines, Section 4.1",
        "category": "Medication restrictions"
    },
    {
        "id": "medication_antihistamine_001",
        "text": "Donors taking antihistamines or antiallergy medications can donate, but should wait 48 hours after the last dose for medications like cetirizine or loratadine. These do not affect blood quality but ensure donor safety.",
        "source": "NACO Medication Guidelines, Section 4.2",
        "category": "Medication restrictions"
    },
    {
        "id": "medication_aspirin_001",
        "text": "Aspirin and aspirin-containing medications are permitted for whole blood donors. However, donors taking aspirin should wait 48 hours before donating platelets, as aspirin affects platelet function and can reduce transfusion efficacy.",
        "source": "NBTC Guidelines, Section 4.3",
        "category": "Medication restrictions"
    },
    {
        "id": "infection_hiv_001",
        "text": "Donors with HIV (Human Immunodeficiency Virus) are permanently ineligible to donate blood, plasma, organs, tissue, or bone. This is based on window period concerns and the progressive nature of HIV infection. HIV antibody testing is mandatory for all donations.",
        "source": "NACO HIV Policy",
        "category": "Infectious disease"
    },
    {
        "id": "infection_hepatitis_b_001",
        "text": "Donors with Hepatitis B (HBsAg positive) are permanently ineligible to donate. Even donors with a history of Hepatitis B infection who have recovered remain permanently ineligible due to the risk of transfusion-transmitted infection. All donations are screened with HBsAg and anti-HBc testing.",
        "source": "NACO Hepatitis B Policy",
        "category": "Infectious disease"
    },
    {
        "id": "infection_hepatitis_c_001",
        "text": "Donors with Hepatitis C (anti-HCV positive) are permanently ineligible to donate. Donors with a history of Hepatitis C remain ineligible even after recovery. All donations are screened with anti-HCV testing.",
        "source": "NACO Hepatitis C Policy",
        "category": "Infectious disease"
    },
    {
        "id": "infection_syphilis_001",
        "text": "Donors who test positive for syphilis (RPR/VDRL) are permanently ineligible to donate. All donations are screened with serological testing (RPR/VDRL and TPPA or FTA-ABS). Donors treated for syphilis remain ineligible.",
        "source": "NACO Syphilis Policy",
        "category": "Infectious disease"
    },
    {
        "id": "infection_malaria_001",
        "text": "Donors with a history of malaria can donate 3 years after complete cure and confirmation of parasitemia clearance. Donors in endemic areas or those with fever should be tested. Those with acute malaria are temporarily ineligible for 3 months after treatment completion.",
        "source": "NBTC Malaria Guidelines, Section 5.1",
        "category": "Infectious disease"
    },
    {
        "id": "fever_001",
        "text": "Donors with a current fever (body temperature above 98.6°F or 37°C) must defer donation. Fever may indicate an acute infection. Donors who have recovered from fever should wait at least 48 hours after the fever resolves before donating.",
        "source": "NBTC Guidelines, Section 5.2",
        "category": "Acute illness"
    },
    {
        "id": "surgery_001",
        "text": "Donors who have undergone major surgery should defer donation for at least 6 months. Minor surgical procedures (e.g., tooth extraction, skin biopsy) require a 48-hour deferral. Donors must be fully healed and not taking pain medications.",
        "source": "NBTC Guidelines, Section 6.1",
        "category": "Medical procedures"
    },
    {
        "id": "vaccination_001",
        "text": "Donors receiving live attenuated vaccines (e.g., varicella, MMR, yellow fever, BCG) must defer donation for 28 days after vaccination. Donors receiving inactivated vaccines (e.g., flu, hepatitis A/B, COVID-19) may donate immediately or after 48 hours depending on the vaccine.",
        "source": "NBTC Vaccination Guidelines, Section 6.2",
        "category": "Vaccinations and immunizations"
    },
    {
        "id": "dental_001",
        "text": "Donors who have undergone a dental procedure involving extraction or gum manipulation should defer donation for 48 hours. Minor dental cleaning without bleeding does not require deferral. Donors must ensure the dental wound is healed.",
        "source": "NBTC Guidelines, Section 6.3",
        "category": "Medical procedures"
    },
    {
        "id": "pregnancy_001",
        "text": "Pregnant women should not donate blood due to increased risks of iron deficiency and anemia, both for the mother and developing fetus. Breastfeeding women may donate, but should ensure adequate hydration and nutrition. Women who have recently given birth (within 6 months) should be evaluated individually.",
        "source": "NBTC Pregnancy Guidelines, Section 7.1",
        "category": "Reproductive health"
    },
    {
        "id": "menstruation_001",
        "text": "Menstruation is not an absolute contraindication to blood donation. However, women experiencing heavy menstrual bleeding may have lower hemoglobin levels and should be counseled about donation deferral. Iron supplementation should be considered if hemoglobin is borderline.",
        "source": "NBTC Guidelines, Section 7.2",
        "category": "Reproductive health"
    },
    {
        "id": "tattoo_001",
        "text": "Donors with a new tattoo or body piercing should defer donation for 6 months if performed with non-sterile equipment or in unregulated settings. Tattoos and piercings done by licensed professionals using sterile, single-use equipment do not require deferral.",
        "source": "NBTC Guidelines, Section 8.1",
        "category": "Behavioral risk"
    },
    {
        "id": "blood_type_compatibility_001",
        "text": "O- blood (Rh negative, type O) is the universal donor and can be given to any blood type. O+ can donate to O+, A+, B+, and AB+. A- can donate to A-, A+, AB-, and AB+. B- can donate to B-, B+, AB-, and AB+. AB- can donate to AB- and AB+. AB+ can only donate to AB+.",
        "source": "Blood Bank Compatibility Chart",
        "category": "Blood type and compatibility"
    },
    {
        "id": "blood_type_recipient_001",
        "text": "AB+ is the universal recipient and can receive from any blood type. AB- can receive from O-, A-, B-, and AB-. A+ can receive from O+, O-, A+, and A-. B+ can receive from O+, O-, B+, and B-. O- can only receive from O-.",
        "source": "Blood Bank Compatibility Chart",
        "category": "Blood type and compatibility"
    },
    {
        "id": "anemia_hemoglobin_male_001",
        "text": "For male blood donors, the minimum hemoglobin level is 13.0 g/dL (or hematocrit 40%). Donors below this threshold are at risk for iron deficiency anemia after donation and should be deferred. Iron supplementation for 6-8 weeks can increase hemoglobin to acceptable levels.",
        "source": "NBTC Guidelines, Section 9.1",
        "category": "Blood parameters"
    },
    {
        "id": "anemia_hemoglobin_female_001",
        "text": "For female blood donors, the minimum hemoglobin level is 12.0 g/dL (or hematocrit 36%). Female donors have higher risk of iron deficiency due to menstruation and pregnancy. Iron supplementation should be offered routinely.",
        "source": "NBTC Guidelines, Section 9.2",
        "category": "Blood parameters"
    },
    {
        "id": "hypertension_001",
        "text": "Donors with controlled hypertension (blood pressure < 180/100 mmHg) on stable medication can donate. Donors with uncontrolled hypertension (> 180/100 mmHg) should defer donation until controlled. Blood pressure should be checked at each donation visit.",
        "source": "NBTC Guidelines, Section 10.1",
        "category": "Chronic conditions"
    },
    {
        "id": "diabetes_001",
        "text": "Donors with well-controlled diabetes (fasting glucose < 200 mg/dL, HbA1c < 7.5%) on stable medication can donate. Donors with uncontrolled diabetes, diabetic complications, or requiring insulin adjustment for donation should be deferred. Blood sugar should be checked at each donation.",
        "source": "NBTC Guidelines, Section 10.2",
        "category": "Chronic conditions"
    },
    {
        "id": "heart_disease_001",
        "text": "Donors with a history of myocardial infarction (heart attack) or angina are permanently ineligible. Donors with arrhythmia or valve disease should be evaluated individually. Those with controlled heart failure who have been stable for 6 months may be considered for donation after medical clearance.",
        "source": "NBTC Cardiovascular Guidelines, Section 10.3",
        "category": "Chronic conditions"
    },
    {
        "id": "cancer_001",
        "text": "Donors with a history of cancer should be deferred. Those who have completed treatment for cancer and are in remission for at least 5 years may be considered for donation on a case-by-case basis. Active cancer diagnosis is a permanent contraindication.",
        "source": "NBTC Oncology Guidelines, Section 11.1",
        "category": "Medical history"
    },
    {
        "id": "transplant_kidney_001",
        "text": "Donors with a kidney transplant are generally not eligible to donate due to the need to protect the transplanted organ. However, donation eligibility may be reconsidered if kidney function is excellent and at least 2 years post-transplantation, subject to medical clearance.",
        "source": "NBTC Transplant Guidelines, Section 11.2",
        "category": "Medical history"
    },
    {
        "id": "lung_disease_001",
        "text": "Donors with active tuberculosis are ineligible. Those who have completed TB treatment and are cured for at least 2 years may donate. Donors with asthma or COPD can donate if their condition is well-controlled and they have normal oxygen saturation.",
        "source": "NBTC Pulmonary Guidelines, Section 11.3",
        "category": "Chronic conditions"
    },
    {
        "id": "alcohol_001",
        "text": "Donors who have consumed alcohol within 48 hours before donation should defer. Alcohol can cause dehydration and affect blood donation. Donors who have a history of alcohol abuse should be counseled and screened for liver disease (hepatitis).",
        "source": "NBTC Behavioral Guidelines, Section 12.1",
        "category": "Behavioral risk"
    },
    {
        "id": "drug_use_001",
        "text": "Donors with a history of intravenous drug use are permanently ineligible due to high risk of bloodborne infections (HIV, Hepatitis B/C). Those who experimented with IV drugs more than 12 months ago with no repeat use may be reconsidered with thorough testing.",
        "source": "NACO Drug Use Guidelines",
        "category": "Behavioral risk"
    },
    {
        "id": "sexual_exposure_001",
        "text": "Men who have had sex with another man within the past 12 months should defer donation. Men who have not engaged in sexual contact with other men for more than 12 months may donate. This policy is based on epidemiological data regarding sexual transmission of bloodborne infections.",
        "source": "NACO Sexual Health Guidelines",
        "category": "Behavioral risk"
    },
    {
        "id": "blood_transfusion_001",
        "text": "Donors who have received a blood transfusion should defer donation for 12 months from the date of transfusion. This deferral period allows for seroconversion of any potentially transmitted bloodborne pathogens to be detected.",
        "source": "NBTC Guidelines, Section 13.1",
        "category": "Transfusion history"
    },
    {
        "id": "dialysis_001",
        "text": "Donors who are on hemodialysis or peritoneal dialysis are ineligible to donate. The kidney disease and the need for dialysis pose risks to the donor's health after blood loss.",
        "source": "NBTC Renal Guidelines, Section 11.4",
        "category": "Chronic conditions"
    },
    {
        "id": "clotting_disorder_001",
        "text": "Donors with bleeding disorders (hemophilia, von Willebrand disease) or those on anticoagulation therapy (warfarin, DOACs) are ineligible. Donors taking aspirin for cardiovascular reasons can donate whole blood but should defer for platelet donation.",
        "source": "NBTC Coagulation Guidelines, Section 11.5",
        "category": "Medical history"
    }
]

def get_all_rules() -> list:
    """Return all eligibility rules."""
    return ELIGIBILITY_RULES

def get_rules_by_category(category: str) -> list:
    """Get rules by category."""
    return [r for r in ELIGIBILITY_RULES if r["category"].lower() == category.lower()]

def get_rule_by_id(rule_id: str) -> dict:
    """Get a specific rule by ID."""
    for rule in ELIGIBILITY_RULES:
        if rule["id"] == rule_id:
            return rule
    return None
