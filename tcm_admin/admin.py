from django.contrib import admin
from .models import (
    Analysis, Pattern, FunctionalCategory, SymptomCategory,
    MedicalCondition, WBCGlossary, WBCMatrix, MedicationList,
    MedicationMapping, MedicationScoreDef, SupplementList,
    SupplementMapping, SupplementScoreDef, LifestyleQuestionnaire,
    TCMBodyTypeMapping, TCMPathogenDefinition
)


@admin.register(Analysis)
class AnalysisAdmin(admin.ModelAdmin):
    # 1. TABLE VIEW (The List) - Shows all 24 columns
    list_display = (
        'blood_test', 'panel', 'blood_test_full', 'blood_test_acronym',
        'units', 'units_interchangeable', 'ideal_low', 'ideal_high',
        'absence_low', 'absence_high', 'conv_diag_low', 'conv_diag_high',
        'func_diag_low', 'func_diag_high', 'tcm_diag_low', 'tcm_diag_high',
        'organs_conv_func', 'organs_tcm', 'possible_assoc_pathogens',
        'severity', 'pathogens_low', 'pathogens_high', 'vital_marker',
        'func_panel_1', 'func_panel_2', 'func_panel_3'
    )

    # 2. ADD / EDIT VIEW (The Form) - Organized into logical groups
    # This ensures EVERY field is visible when adding new data
    fieldsets = (
        ('Blood Marker Identification', {
            'fields': (
                'panel',
                'blood_test',
                'blood_test_full',
                'blood_test_acronym',
                'vital_marker'
            )
        }),
        ('Units & Measurement', {
            'fields': (
                'units',
                'units_interchangeable'
            )
        }),
        ('Reference Ranges & Severity', {
            'fields': (
                ('ideal_low', 'ideal_high'),
                ('absence_low', 'absence_high'),
                'severity'
            )
        }),
        ('Medicine & TCM Diagnoses', {
            'description': "Detailed diagnostic narratives for low and high results",
            'fields': (
                'conv_diag_low', 'conv_diag_high',
                'func_diag_low', 'func_diag_high',
                'tcm_diag_low', 'tcm_diag_high'
            )
        }),
        ('Organs & Pathogens', {
            'fields': (
                'organs_conv_func',
                'organs_tcm',
                'possible_assoc_pathogens',
                'pathogens_low',
                'pathogens_high'
            )
        }),
        ('Functional Panels Mapping', {
            'fields': (
                'func_panel_1',
                'func_panel_2',
                'func_panel_3'
            )
        }),
    )

    # Helper features
    search_fields = ('blood_test', 'blood_test_full', 'panel')
    list_filter = ('panel', 'vital_marker', 'severity')
    list_per_page = 50


@admin.register(Pattern)
class PatternsAdmin(admin.ModelAdmin):
    # --- TABLE VIEW (List of all entries) ---
    list_display = (
        'tcm_patterns',
        'excess_deficiency',
        'modern_description',
        'middle_primary',
        'middle_secondary',
        'middle_tertiary',
        'middle_quantery',
        'bottom_primary',
        'bottom_secondary',
        'symptoms',
        'body_type_primary',
        'body_type_secondary',
        'body_type_tertiary',
        'positive_impacts',
        'negative_impacts',
        'rationale',
        'pathogenic_factor'
    )

    # --- ADD/EDIT VIEW (Form for adding new data) ---
    fields = (
        'tcm_patterns',
        'excess_deficiency',
        'modern_description',
        'middle_primary',
        'middle_secondary',
        'middle_tertiary',
        'middle_quantery',
        'bottom_primary',
        'bottom_secondary',
        'symptoms',
        'body_type_primary',
        'body_type_secondary',
        'body_type_tertiary',
        'positive_impacts',
        'negative_impacts',
        'rationale',
        'pathogenic_factor'
    )

    # Search and Filter options
    search_fields = ('tcm_patterns', 'symptoms',
                     'rationale', 'modern_description')
    list_filter = ('excess_deficiency',
                   'body_type_primary', 'pathogenic_factor')
    list_per_page = 50
    list_display_links = ('tcm_patterns',)


@admin.register(FunctionalCategory)
class FunctionalCategoryAdmin(admin.ModelAdmin):
    list_display = ('functional_medicine',
                    'primary_category', 'secondary_category')
    search_fields = ('functional_medicine', 'primary_category')


@admin.register(SymptomCategory)
class SymptomCategoryAdmin(admin.ModelAdmin):
    list_display = ('symptoms', 'primary_category', 'secondary_category')
    search_fields = ('symptoms', 'primary_category')


@admin.register(MedicalCondition)
class MedicalConditionAdmin(admin.ModelAdmin):
    # --- TABLE VIEW (Shows all rows and columns) ---
    list_display = (
        'condition',
        'tcm_patterns',
        'rationale',
        'primary_category',
        'secondary_category',
        'tertiary_category'
    )

    # --- ADD/EDIT FORM VIEW (Every field visible) ---
    fields = (
        'condition',
        'tcm_patterns',
        'rationale',
        'primary_category',
        'secondary_category',
        'tertiary_category'
    )

    # Clickable link to edit
    list_display_links = ('condition',)

    # Search bar for conditions and patterns
    search_fields = ('condition', 'tcm_patterns', 'rationale')

    # Filters for categories
    list_filter = ('primary_category', 'secondary_category')

    list_per_page = 50


@admin.register(WBCGlossary)
class WBCGlossaryAdmin(admin.ModelAdmin):
    # --- TABLE VIEW (All 3 Columns) ---
    list_display = (
        'term',
        'definition',
        'next_steps'
    )

    # --- ADD/EDIT FORM VIEW (All 3 Columns) ---
    fields = (
        'term',
        'definition',
        'next_steps'
    )

    # Clickable link to edit
    list_display_links = ('term',)

    # Search bar
    search_fields = ('term', 'definition', 'next_steps')

    list_per_page = 50


@admin.register(WBCMatrix)
class WBCMatrixAdmin(admin.ModelAdmin):
    # --- TABLE VIEW (All 18 Columns) ---
    list_display = (
        'wbc', 'neutrophils', 'lymphocytes', 'monocytes', 'eosinophils', 'basophils',
        'primary_int', 'risk_score', 'risk_level', 'confidence'
    )
    # (Note: I kept list_display slightly shorter to fit the screen,
    # but the form below has EVERYTHING editable)

    # --- ADD/EDIT FORM VIEW (All 18 Columns) ---
    fieldsets = (
        ('Marker Patterns', {
            'description': "Enter 'High', 'Low', or 'Normal' for each marker",
            'fields': (
                ('wbc', 'neutrophils', 'lymphocytes'),
                ('monocytes', 'eosinophils', 'basophils')
            )
        }),
        ('Interpretation Hierarchy', {
            'fields': (
                'primary_int',
                'secondary',
                'tertiary',
                'quaternary',
                'quinary'
            )
        }),
        ('Risk & Analysis', {
            'fields': (
                ('risk_score', 'risk_level', 'confidence'),
                'risk_definition',
                'other_considerations',
                'rationale',
                'clinical_guidance'
            )
        }),
    )

    # Clickable links
    list_display_links = ('wbc', 'primary_int')

    # Search and Filters
    search_fields = ('primary_int', 'rationale', 'clinical_guidance')
    list_filter = ('risk_level', 'confidence', 'wbc')

    list_per_page = 50


@admin.register(MedicationList)
class MedicationListAdmin(admin.ModelAdmin):
    # --- TABLE VIEW (All Columns) ---
    list_display = (
        'category',
        'sub_category',
        'example_medications',
        'do_not_effect',
        'tcm_narrative_no_effect'
    )

    # --- ADD/EDIT FORM VIEW (All Columns) ---
    fields = (
        'category',
        'sub_category',
        'example_medications',
        'do_not_effect',
        'tcm_narrative_no_effect'
    )

    # Allow clicking on category or sub-category to open the edit page
    list_display_links = ('category', 'sub_category')

    # Add a search bar for medications and narratives
    search_fields = ('category', 'example_medications',
                     'tcm_narrative_no_effect')

    # Add filters for easier navigation
    list_filter = ('category',)

    list_per_page = 50


@admin.register(MedicationMapping)
class MedicationMappingAdmin(admin.ModelAdmin):
    # --- TABLE VIEW (All 10 Columns) ---
    list_display = (
        'panel',
        'marker',
        'med_types_low',
        'magnitude_low',
        'med_types_high',
        'magnitude_high',
        'narrative_low',
        'narrative_high',
        'tcm_narrative_low',
        'tcm_narrative_high'
    )

    # --- ADD/EDIT FORM VIEW (All 10 Columns) ---
    # This ensures every value can be entered when adding new
    fields = (
        'panel',
        'marker',
        'med_types_low',
        'magnitude_low',
        'med_types_high',
        'magnitude_high',
        'narrative_low',
        'narrative_high',
        'tcm_narrative_low',
        'tcm_narrative_high'
    )

    # Clickable links
    list_display_links = ('marker', 'panel')

    # Search and Filters
    search_fields = ('marker', 'panel', 'med_types_low', 'med_types_high')
    list_filter = ('panel', 'magnitude_low', 'magnitude_high')

    list_per_page = 50


@admin.register(MedicationScoreDef)
class MedicationScoreDefAdmin(admin.ModelAdmin):
    list_display = ('score', 'definition')


@admin.register(SupplementList)
class SupplementsListAdmin(admin.ModelAdmin):
    # --- TABLE VIEW (All 5 Columns) ---
    list_display = (
        'category',
        'sub_category',
        'example_supplements',
        'normal_narrative',
        'tcm_narrative'
    )

    # --- ADD/EDIT FORM VIEW (All 5 Columns) ---
    fields = (
        'category',
        'sub_category',
        'example_supplements',
        'normal_narrative',
        'tcm_narrative'
    )

    # Clickable links for easy editing
    list_display_links = ('category', 'sub_category')

    # Search bar for finding specific supplements
    search_fields = ('category', 'example_supplements', 'normal_narrative')

    # Filter by Category on the right side
    list_filter = ('category',)

    list_per_page = 50


@admin.register(SupplementMapping)
class SupplementsMappingAdmin(admin.ModelAdmin):
    # --- TABLE VIEW (All 14 Columns) ---
    list_display = (
        'panel',
        'marker',
        'supp_types_low',
        'magnitude_low',
        'supp_types_high',
        'magnitude_high',
        'narrative_low',
        'narrative_high',
        'tcm_narrative_low',
        'tcm_narrative_high',
        'mechanism_low',
        'mechanism_high',
        'interp_note_low',
        'interp_note_high'
    )

    # --- ADD/EDIT FORM VIEW (All 14 Columns) ---
    fields = (
        'panel',
        'marker',
        'supp_types_low',
        'magnitude_low',
        'supp_types_high',
        'magnitude_high',
        'narrative_low',
        'narrative_high',
        'tcm_narrative_low',
        'tcm_narrative_high',
        'mechanism_low',
        'mechanism_high',
        'interp_note_low',
        'interp_note_high'
    )

    # Clickable links
    list_display_links = ('marker', 'panel')

    # Search and Filters
    search_fields = ('marker', 'panel', 'supp_types_low', 'supp_types_high')
    list_filter = ('panel', 'magnitude_low', 'magnitude_high')

    list_per_page = 50


@admin.register(SupplementScoreDef)
class SupplementScoreDefAdmin(admin.ModelAdmin):
    list_display = ('score', 'definition')


@admin.register(LifestyleQuestionnaire)
class LifestyleQuestionnaireAdmin(admin.ModelAdmin):
    # --- TABLE VIEW (All Columns) ---
    list_display = (
        'question_number',
        'question',
        'answer_option',
        'sub_answer',
        'func_perspective',
        'tcm_perspective'
    )

    # --- ADD/EDIT FORM VIEW (All Columns) ---
    fields = (
        'question_number',
        'question',
        'answer_option',
        'sub_answer',
        'func_perspective',
        'tcm_perspective'
    )

    # Allow clicking on the question or number to edit
    list_display_links = ('question_number', 'question')

    # Add a search bar for keywords in questions or perspectives
    search_fields = ('question', 'func_perspective', 'tcm_perspective')

    # Add a filter for question numbers
    list_filter = ('question_number',)


@admin.register(TCMBodyTypeMapping)
class TCMBodyTypeMappingAdmin(admin.ModelAdmin):
    # --- TABLE VIEW (All 4 Columns) ---
    list_display = (
        'tcm_body_type',
        'tcm_explanation',
        'func_equivalent',
        'func_explanation'
    )

    # --- ADD/EDIT FORM VIEW (All 4 Columns) ---
    fields = (
        'tcm_body_type',
        'tcm_explanation',
        'func_equivalent',
        'func_explanation'
    )

    # Clickable link to edit
    list_display_links = ('tcm_body_type',)

    # Search bar
    search_fields = ('tcm_body_type', 'func_equivalent', 'tcm_explanation')

    list_per_page = 50


@admin.register(TCMPathogenDefinition)
class TCMPathogenDefinitionAdmin(admin.ModelAdmin):
    list_display = ('pathogen', 'definition')
    search_fields = ('pathogen',)
