"""
Advice logic for SkyWell: maps risk scores and health profiles to actionable recommendations.
"""

def get_tier(risk_score: int) -> int:
    """
    Map a 1–10 risk score to a tier (0–3).
    """
    if risk_score >= 9:
        return 3
    elif risk_score >= 7:
        return 2
    elif risk_score >= 4:
        return 1
    else:
        return 0  # No alert

# Tiered action plans for each health profile
ACTION_PLANS = {
    'allergic_rhinitis': {
        1: [
            'Wrap-around sunglasses + barrier balm around nostrils',
            'Shower, wash hair, and change clothes immediately after outdoor exposure'
        ],
        2: [
            'Stay indoors with windows shut during high pollen; time outings (post-rain or evening)',
            'Wear surgical/N95 mask outdoors',
            'Start intranasal steroid or antihistamine 1–2 days before peak',
            'Use saline nasal irrigation (nasal lavage)'
        ],
        3: [],
    },
    'allergic_asthma': {
        1: [
            'Follow written asthma plan; increase controller/reliever early'
        ],
        2: [
            'Skip vigorous outdoor exercise during O₃ or PM peaks; close windows',
            'Wear FFP2/N95 mask if exposure unavoidable',
            'Run HEPA air-cleaner in bedroom',
            'Pre-treat with SABA 10–15 min before outdoor tasks'
        ],
        3: [],
    },
    'copd': {
        1: [
            'Keep rescue inhaler handy; use before exertion on bad-air days'
        ],
        2: [
            'Stay indoors with recirc‑AC during pollution alerts',
            'Run portable HEPA purifier',
            'Wear N95 respirator outdoors in high pollution'
        ],
        3: [],
    },
    'heart_disease': {
        1: [
            'Check blood pressure and heart rate more frequently; maintain medication schedule',
            'Hydrate and avoid smoking / second‑hand smoke on poor-air days'
        ],
        2: [
            'Reschedule strenuous exercise indoors on poor air days',
            'Create clean-air room with sealed windows and HEPA purifier',
            'Wear N95 mask for essential outdoor travel'
        ],
        3: [],
    },
    'diabetes': {
        1: [
            'Monitor glucose more closely; hydrate well on poor-air days',
            'Maintain Mediterranean-style antioxidant-rich diet'
        ],
        2: [
            'Move workouts indoors during air pollution peaks',
            'Run HEPA purifier at home',
            'Wear N95 mask in traffic or smoky environments'
        ],
        3: [],
    },
    'pregnancy': {
        1: [
            'Flag any unusually high exposure to obstetric care team',
            'Hydrate well and avoid smoking/second‑hand smoke'
        ],
        2: [
            'Stay indoors with filtered (HEPA) air',
            'Choose low-traffic routes or exercise indoors on high-pollution days',
            'Use bedroom HEPA purifier overnight',
            'Wear FFP2 mask for unavoidable travel during alerts'
        ],
        3: [],
    },
    'skin_cancer_survivor': {
        1: [
            'Apply broad-spectrum SPF 30–50 sunscreen',
            'Wear sun-protective clothing, broad-brim hat, UV400 sunglasses',
            'Seek shade or use a parasol outdoors'
        ],
        2: [
            'Avoid sun exposure between 10 AM and 4 PM'
        ],
        3: [],
    },
    'vitiligo_albinism': {
        1: [
            'Apply SPF 50+ sunscreen daily to depigmented skin',
            'Wear UPF clothing, gloves, and wide-brim hat',
        ],
        2: [
            'Install UV-filter window film in car/home',
            'Plan outdoor errands for early morning or late afternoon'
        ],
        3: [],
    },
    'sle_photosensitive': {
        1: [
            'Apply broad-spectrum mineral SPF 50+ sunscreen every 2 hours',
            'Wear protective clothing and UV sunglasses'
        ],
        2: [
            'Strictly avoid sun when UV Index ≥ 3',
            'Use UV-blocking window film at home/car'
        ],
        3: [],
    },
    'allergic_conjunctivitis': {
        1: [
            'Wear wrap-around sunglasses or goggles',
            'Use artificial tears after outdoor exposure',
            'Apply antihistamine/mast-cell stabilizer eye drops before exposure',
            'Apply cool compresses to relieve itching or swelling'
        ],
        2: [
            'Keep windows closed and run AC/HEPA filter at home'
        ],
        3: [],
    },
    'atopic_dermatitis': {
        1: [
            'Soak-and-seal emollient bath after lukewarm wash',
            'Use emollient soap substitutes (no harsh soaps)',
            'Wear loose cotton clothing; optional mask in dusty conditions'
        ],
        2: [
            'Limit outdoor time during PM or O₃ alerts',
            'Run HEPA purifier and keep indoor humidity at 40–50%'
        ],
        3: [],
    }
}

# Generic, variable-specific tiered advice for custom profiles
GENERIC_ACTION_PLANS = {
    'birch_pollen': {
        1: ['Check birch pollen count, consider sunglasses'],
        2: ['Wear mask outdoors, close windows'],
        3: ['Stay indoors, shower/change clothes']
    },
    'grass_pollen': {
        1: ['Check grass pollen count, consider sunglasses'],
        2: ['Wear mask outdoors, close windows'],
        3: ['Stay indoors, shower/change clothes']
    },
    'olive_pollen': {
        1: ['Check olive pollen count, consider sunglasses'],
        2: ['Wear mask outdoors, close windows'],
        3: ['Stay indoors, shower/change clothes']
    },
    'mugwort_pollen': {
        1: ['Check mugwort pollen count, consider sunglasses'],
        2: ['Wear mask outdoors, close windows'],
        3: ['Stay indoors, shower/change clothes']
    },
    'ragweed_pollen': {
        1: ['Check ragweed pollen count, consider sunglasses'],
        2: ['Wear mask outdoors, close windows'],
        3: ['Stay indoors, shower/change clothes']
    },
    'alder_pollen': {
        1: ['Check alder pollen count, consider sunglasses'],
        2: ['Wear mask outdoors, close windows'],
        3: ['Stay indoors, shower/change clothes']
    },
    'pm2p5_conc': {
        1: ['Monitor air quality, reduce heavy exertion'],
        2: ['Use N95 mask if outside, limit outdoor activity'],
        3: ['Stay indoors, run HEPA air purifier']
    },
    'pm10_conc': {
        1: ['Monitor air quality, reduce heavy exertion'],
        2: ['Use N95 mask if outside, limit outdoor activity'],
        3: ['Stay indoors, run HEPA air purifier']
    },
    'o3_conc': {
        1: ['Avoid peak hours, ventilate indoor air'],
        2: ['Avoid outdoor exercise, close windows'],
        3: ['Stay indoors, use AC or air purifier']
    },
    'no2_conc': {
        1: ['Minimize time near traffic'],
        2: ['Avoid traffic corridors, wear mask'],
        3: ['Stay indoors, run air purifier']
    },
    'uv_biologically_effective_dose': {
        1: ['Use sunglasses, plan outdoor time early/late'],
        2: ['Apply sunscreen SPF50+, wear protective clothing'],
        3: ['Avoid sun 10am-4pm, stay in shade']
    },
    'so2_conc': {
        1: ['Limit outdoor exposure'],
        2: ['Use mask, avoid high-traffic areas'],
        3: ['Stay indoors, use air purifier']
    },
}

def get_advice(profile: str, risk_score: int) -> list:
    """
    Get all recommended actions for a given profile and risk score.
    Returns a list of actions up to the current tier.
    """
    tier = get_tier(risk_score)
    actions = []
    if profile not in ACTION_PLANS:
        return actions
    for i in range(1, tier + 1):
        actions.extend(ACTION_PLANS[profile].get(i, []))
    return actions

def get_generic_advice(variables: list, risk_score: int) -> list:
    """
    Get tiered generic advice for a list of variables and a given risk score.
    Returns a list of actions up to the current tier for each variable.
    """
    tier = get_tier(risk_score)
    actions = []
    for var in variables:
        if var in GENERIC_ACTION_PLANS:
            for i in range(1, tier + 1):
                actions.extend(GENERIC_ACTION_PLANS[var].get(i, []))
    return actions 