from enum import Enum
from sqlalchemy import Enum as PGEnum


#ToDo(evseev.dmsr): Make correct list of interests
class EInterests(Enum):
    interest1 = 'interest1'
    interest2 = 'interest2'


class EExpertiseArea(Enum):
    development = 'development'
    devops = 'devops'
    cyber_security = 'cyber_security'
    data_science = 'data_science'
    databases = 'databases'
    cloud_technologies = 'cloud_technologies'
    technical_support = 'technical_support'
    product_management = 'product_management'
    design = 'design'
    marketing = 'marketing'
    legal_services = 'legal_services'
    finances = 'finances'
    compliance = 'compliance'
    hr = 'hr'
    pr = 'pr'
    sales = 'sales'
    business_development = 'business_development'


class ESpecialisation(Enum):
    # development
    frontend = 'frontend'
    backend = 'backend'
    mobile = 'mobile'
    web = 'web'
    gamedev = 'gamedev'
    embedded = 'embedded'
    nocode = 'nocode'

    # devops
    net_administration = 'net_administration'
    server_administration = 'server_administration'
    virtualization = 'virtualization'
    containerization = 'containerization'
    automatization = 'automatization'
    cloud_devops = 'cloud_devops'
    serverless = 'serverless'

    # cyber_security
    vulnerability_assessment = 'vulnerability_assessment'
    pentesting = 'pentesting'
    data_protection = 'data_protection'
    incident_management = 'incident_management'
    cryptography = 'cryptography'
    app_security = 'app_security'
    net_security = 'net_security'
    cloud_security = 'cloud_security'
    devsecops = 'devsecops'

    # data_science
    data_analysis = 'data_analysis'
    machine_learning = 'machine_learning'
    big_data = 'big_data'
    business_analytics = 'business_analytics'
    ai = 'ai'
    social_media_analysis = 'social_media_analysis'
    bioinformatics = 'bioinformatics'
    biometrics = 'biometrics'
    clearml = 'clearml'

    # databases
    db_administration = 'db_administration'
    db_design = 'db_design'
    request_optimisation = 'request_optimisation'
    dwh = 'dwh'
    nosql = 'nosql'

    # cloud_technologies
    cloud_platforms = 'cloud_platforms'
    cloud_infrastructure = 'cloud_infrastructure'
    cloud_resources_management = 'cloud_resources_management'
    microservices = 'microservices'
    private_cloud = 'private_cloud'
    multi_cloud_strategies = 'multi_cloud_strategies'

    # technical_support
    help_desk = 'help_desk'
    tech_support = 'tech_support'
    equipment_incident_management = 'equipment_incident_management'
    user_service = 'user_service'
    itsm = 'itsm'
    devops_support = 'devops_support'

    # product_management
    product_lifetime_management = 'product_lifetime_management'
    release_plans = 'release_plans'
    requirements_management = 'requirements_management'
    ux_ui_design = 'ux_ui_design'
    product_analysis_optimisation = 'product_analysis_optimisation'
    team_management = 'team_management'
    strategic_planning = 'strategic_planning'
    data_driven_product_development = 'data_driven_product_development'
    mvp_development = 'mvp_development'

    # design
    graphic_design = 'graphic_design'
    web_design = 'web_design'
    mobile_design = 'mobile_design'
    ux_design = 'ux_design'
    interaction_design = 'interaction_design'
    visual_design = 'visual_design'
    user_experience_design = 'user_experience_design'
    design_systems = 'design_systems'
    data_visualization = 'data_visualization'
    theed_design = 'theed_design'
    ui_motion_design = 'ui_motion_design'
    wearables_design = 'wearables_design'

    # marketing
    digital_marketing = 'digital_marketing'
    content_marketing = 'content_marketing'
    seo = 'seo'
    smm = 'smm'
    marketing_research = 'marketing_research'
    data_driven_marketing = 'data_driven_marketing'
    go_to_market_strategy = 'go_to_market_strategy'
    developing_market_entry_plan = 'developing_market_entry_plan'
    competitive_landscape_analysis = 'competitive_landscape_analysis'
    target_segments_defining = 'target_segments_defining'

    # legal_services
    intellectual_property = 'intellectual_property'
    software_licensing = 'software_licensing'
    privacy_and_data_protection = 'privacy_and_data_protection'
    compliance_and_regulation = 'compliance_and_regulation'
    contract_law = 'contract_law'
    tech_law = 'tech_law'

    # finances
    accounting = 'accounting'
    financial_planning_and_analysis = 'financial_planning_and_analysis'
    risk_management = 'risk_management'
    taxation = 'taxation'
    financial_statements = 'financial_statements'
    financial_analytics_using_ai = 'financial_analytics_using_ai'

    # compliance
    compliance_with_regulatory_requirements = 'compliance_with_regulatory_requirements'
    compliance_risk_management = 'compliance_risk_management'
    internal_audits = 'internal_audits'
    anti_fraud = 'anti_fraud'
    data_privacy_management = 'data_privacy_management'
    cyber_compliance = 'cyber_compliance'

    # hr
    recruitment_of_staff = 'recruitment_of_staff'
    labor_relations_management = 'labor_relations_management'
    staff_training_and_development = 'staff_training_and_development'
    talent_management_and_succession_planning = 'talent_management_and_succession_planning'
    compensation_and_benefits = 'compensation_and_benefits'
    employee_performance_management = 'employee_performance_management'
    organizational_development_and_change = 'organizational_development_and_change'
    corporate_culture_and_employee_engagement = 'corporate_culture_and_employee_engagement'
    labor_legislation_and_regulatory_regulation = 'labor_legislation_and_regulatory_regulation'
    conflictology_and_resolution_of_labor_disputes = 'conflictology_and_resolution_of_labor_disputes'
    managing_remote_commands = 'managing_remote_commands'

    # pr
    strategic_communication_planning = 'strategic_communication_planning'
    media_relations = 'media_relations'
    internal_communications = 'internal_communications'
    crisis_pr = 'crisis_pr'
    reputation_management = 'reputation_management'
    working_with_social_media = 'working_with_social_media'
    organization_of_events = 'organization_of_events'
    corporate_communications = 'corporate_communications'
    work_with_public = 'work_with_public'
    content_development_and_copywriting = 'content_development_and_copywriting'
    csr = 'csr'

    # sales
    b2b = 'b2b'
    b2c = 'b2c'
    sales_management = 'sales_management'
    partner_network_development = 'partner_network_development'
    sales_techniques_and_methodologies = 'sales_techniques_and_methodologies'
    training_and_development_of_sales_team = 'training_and_development_of_sales_team'
    sales_support = 'sales_support'
    competitor_and_market_analysis = 'competitor_and_market_analysis'

    # business_development
    business_strategic_planning = 'business_strategic_planning'
    market_research_and_analysis = 'market_research_and_analysis'
    development_of_new_products_and_services = 'development_of_new_products_and_services'
    negotiating_and_concluding_deals = 'negotiating_and_concluding_deals'
    project_management = 'project_management'
    international_development = 'international_development'
    development_of_corporate_culture = 'development_of_corporate_culture'
    financial_analysis_and_planning = 'financial_analysis_and_planning'


#ToDo(evseev.dmsr): Make correct list of grades
class EGrade(Enum):
    senior = 'senior'
    middle = 'middle'
    junior = 'junior'


#ToDo(evseev.dmsr): Make correct list of industries
class EIndustry(Enum):
    industry1 = 'industry1'
    industry2 = 'industry2'


#ToDo(evseev.dmsr): Make correct list of skills
class ESkills(Enum):
    skill1 = 'skill1'
    skill2 = 'skill2'


#ToDo(evseev.dmsr): Make correct list of services
class ECompanyServices(Enum):
    vkservice1 = 'vkservice1'
    yandexservice1 = 'yandexservice1'


#ToDo(evseev.dmsr): Make correct list of locations
class ELocation(Enum):
    moscow_russia = 'moscow_russia'
    london_uk = 'london_uk'


#ToDo(evseev.dmsr): Make correct list of requests
class ERequestsToCommunity(Enum):
    friendship = 'friendship'


#ToDo(evseev.dmsr): Make correct list of possible values
class EWithWhom(Enum):
    friends = 'friends'
    anyone = 'anyone'


#ToDo(evseev.dmsr): Make correct list of privacy settings
class EVisibilitySettings(Enum):
    anyone = 'anyone'
    nobody = 'nobody'


class EProfileType(Enum):
    New = 'new'
    MigratedWOIssues = 'migrated_wo_issues'
    MigratedHasIssues = 'migrated_has_issues'
    MigratedIssuesFixed = 'migrated_issues_fixed'


InterestsPGEnum = PGEnum(EInterests, name='user_interests_enum', inherit_schema=True)
ExpertiseAreaPGEnum = PGEnum(EExpertiseArea, name='user_expertise_enum', inherit_schema=True)
SpecialisationPGEnum = PGEnum(ESpecialisation, name='user_specialisation_enum', inherit_schema=True)
GradePGEnum = PGEnum(EGrade, name='user_grade_enum', inherit_schema=True)
IndustryPGEnum = PGEnum(EIndustry, name='user_industry_enum', inherit_schema=True)
SkillsPGEnum = PGEnum(ESkills, name='user_skills_enum', inherit_schema=True)
CompanyServicesPGEnum = PGEnum(ECompanyServices, name='user_company_services_enum', inherit_schema=True)
LocationPGEnum = PGEnum(ELocation, name='user_location_enum', inherit_schema=True)
RequestsToCommunityPGEnum = PGEnum(ERequestsToCommunity, name='user_requests_to_community_enum', inherit_schema=True)
WithWhomEnumPGEnum = PGEnum(EWithWhom, name='user_with_whom_enum', inherit_schema=True)
VisibilitySettingsPGEnum = PGEnum(EVisibilitySettings, name='user_visibility_settings_enum', inherit_schema=True)
ProfileTypePGEnum = PGEnum(EProfileType, name='user_profile_type_enum', inherit_schema=True)
