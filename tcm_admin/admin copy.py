from django.contrib import admin
from django import forms
from .models import Analysis, Pattern, FunctionalCategory
from .models import (

    Analysis, Pattern, FunctionalCategory, SymptomCategory,

    MedicalCondition, WBCGlossary, WBCMatrix, MedicationList,

    MedicationMapping, MedicationScoreDef, SupplementList,

    SupplementMapping, SupplementScoreDef, LifestyleQuestionnaire,

    TCMBodyTypeMapping, TCMPathogenDefinition

)


class AnalysisAdminForm(forms.ModelForm):
    # UX Config: We add the 'advanced-select' class and the Placeholder text here
    WIDGET_ATTRS = {
        'class': 'advanced-select',
        'style': 'width: 100%'  # Fallback style
    }

    tcm_diag_low = forms.MultipleChoiceField(
        required=False,
        label="TCM Diagnosis (Low)",
        widget=forms.SelectMultiple(
            attrs={**WIDGET_ATTRS, 'data-placeholder': 'Type to search TCM Diagnosis (Low)...'})
    )
    tcm_diag_high = forms.MultipleChoiceField(
        required=False,
        label="TCM Diagnosis (High)",
        widget=forms.SelectMultiple(
            attrs={**WIDGET_ATTRS, 'data-placeholder': 'Type to search TCM Diagnosis (High)...'})
    )
    func_diag_low = forms.MultipleChoiceField(
        required=False,
        label="Functional Med Diagnosis (Low)",
        widget=forms.SelectMultiple(
            attrs={**WIDGET_ATTRS, 'data-placeholder': 'Type to search Func Diagnosis (Low)...'})
    )
    func_diag_high = forms.MultipleChoiceField(
        required=False,
        label="Functional Med Diagnosis (High)",
        widget=forms.SelectMultiple(
            attrs={**WIDGET_ATTRS, 'data-placeholder': 'Type to search Func Diagnosis (High)...'})
    )

    class Meta:
        model = Analysis
        fields = '__all__'

    class Media:
        css = {
            'all': (
                # 1. Standard Select2 CSS
                'https://cdnjs.cloudflare.com/ajax/libs/select2/4.0.13/css/select2.min.css',
                # 2. Your Custom CSS (Make sure this file exists!)
                'admin/css/admin_enhanced.css',
            )
        }
        js = (
            # 1. LOAD JQUERY FIRST (Critical Fix)
            'https://code.jquery.com/jquery-3.6.0.min.js',
            # 2. Load Select2
            'https://cdnjs.cloudflare.com/ajax/libs/select2/4.0.13/js/select2.full.min.js',
            # 3. Load your custom setup
            'admin/js/admin_select2_setup.js',
        )

    def __init__(self, *args, **kwargs):
        super(AnalysisAdminForm, self).__init__(*args, **kwargs)

        # 1. Get Data
        patterns = list(Pattern.objects.values_list(
            'tcm_patterns', flat=True).distinct().order_by('tcm_patterns'))
        func_cats = list(FunctionalCategory.objects.values_list(
            'functional_medicine', flat=True).distinct().order_by('functional_medicine'))

        # 2. Add Missing Data logic (if editing existing row)
        instance = getattr(self, 'instance', None)

        def get_initial_list(db_string, master_list):
            if not db_string:
                return []
            items = [x.strip() for x in db_string.split(';')]
            # Add any item found in DB but not in master list (safety)
            for item in items:
                if item and item not in master_list:
                    master_list.append(item)
            return items

        if instance and instance.pk:
            self.initial['tcm_diag_low'] = get_initial_list(
                instance.tcm_diag_low, patterns)
            self.initial['tcm_diag_high'] = get_initial_list(
                instance.tcm_diag_high, patterns)
            self.initial['func_diag_low'] = get_initial_list(
                instance.func_diag_low, func_cats)
            self.initial['func_diag_high'] = get_initial_list(
                instance.func_diag_high, func_cats)

        # 3. Set Choices (Note: We do NOT need the empty '👇 Select' option anymore because Select2 handles the placeholder)
        self.fields['tcm_diag_low'].choices = [(p, p) for p in patterns if p]
        self.fields['tcm_diag_high'].choices = [(p, p) for p in patterns if p]
        self.fields['func_diag_low'].choices = [(f, f) for f in func_cats if f]
        self.fields['func_diag_high'].choices = [
            (f, f) for f in func_cats if f]

    # --- SAVE LOGIC (Convert List -> String) ---
    def clean_tcm_diag_low(self): return "; ".join(
        self.cleaned_data['tcm_diag_low'])

    def clean_tcm_diag_high(self): return "; ".join(
        self.cleaned_data['tcm_diag_high'])

    def clean_func_diag_low(self): return "; ".join(
        self.cleaned_data['func_diag_low'])
    def clean_func_diag_high(self): return "; ".join(
        self.cleaned_data['func_diag_high'])


@admin.register(Analysis)
class AnalysisAdmin(admin.ModelAdmin):
    form = AnalysisAdminForm
# --- 1. SHOW ALL FIELDS IN LIST ---
    list_display = (
        'id', 'panel', 'blood_test', 'blood_test_full', 'blood_test_acronym',
        'units', 'units_interchangeable', 'ideal_low', 'ideal_high',
        'absence_low', 'absence_high', 'severity', 'vital_marker',
        'tcm_diag_low', 'tcm_diag_high', 'func_diag_low', 'func_diag_high',
        'conv_diag_low', 'conv_diag_high', 'organs_conv_func', 'organs_tcm',
        'possible_assoc_pathogens', 'pathogens_low', 'pathogens_high',
        'func_panel_1', 'func_panel_2', 'func_panel_3'
    )

    # We add this to ensure the columns don't look cramped in the main list
    list_display_links = ('blood_test',)

    # --- EDIT FORM LAYOUT ---
    fieldsets = (
        ('Blood Marker Identification', {
            'fields': ('panel', 'blood_test', 'blood_test_full', 'blood_test_acronym', 'vital_marker')
        }),
        ('Ranges & Severity', {
            'fields': (('ideal_low', 'ideal_high'), ('absence_low', 'absence_high'), 'severity')
        }),
        # --- HERE IS THE KEY CHANGE ---
        # We give the dropdowns plenty of space
        ('Medicine & TCM Diagnoses', {
            'description': "Hold CTRL (Windows) or CMD (Mac) to select multiple items.",
            'fields': (
                'tcm_diag_low',
                'tcm_diag_high',
                'func_diag_low',
                'func_diag_high',
            )
        }),
        ('Conventional Medicine Diagnoses', {
            'fields': ('conv_diag_low', 'conv_diag_high')
        }),
        ('Organs & Pathogens', {
            'fields': ('organs_conv_func', 'organs_tcm', 'possible_assoc_pathogens', 'pathogens_low', 'pathogens_high')
        }),
        ('Functional Panels', {
            'fields': ('func_panel_1', 'func_panel_2', 'func_panel_3')
        }),
        ('Units', {
            'fields': ('units', 'units_interchangeable')
        }),
    )

    search_fields = ('blood_test', 'panel', 'blood_test_full')
    list_filter = ('panel', 'severity')
    list_per_page = 50


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


class MedicationMappingAdminForm(forms.ModelForm):
    # Turn 'marker' into a Dropdown populated by Analysis table
    marker = forms.ChoiceField(required=False, label="Target Blood Marker")

    class Meta:
        model = MedicationMapping
        fields = '__all__'

    def __init__(self, *args, **kwargs):
        super(MedicationMappingAdminForm, self).__init__(*args, **kwargs)
        # Fetch all Blood Markers from Analysis table
        markers = list(Analysis.objects.values_list(
            'blood_test', flat=True).distinct().order_by('blood_test'))

        # Protect existing value
        instance = getattr(self, 'instance', None)
        if instance and instance.marker and instance.marker not in markers:
            markers.append(instance.marker)

        markers.sort(key=lambda x: (x is None, x))
        choices = [('', '👇 Select Blood Marker...')] + [(m, m)
                                                        for m in markers if m]
        self.fields['marker'].choices = choices


@admin.register(MedicationMapping)
class MedicationMappingAdmin(admin.ModelAdmin):
    form = MedicationMappingAdminForm
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


class SupplementMappingAdminForm(forms.ModelForm):
    # Turn 'marker' into a Dropdown populated by Analysis table
    marker = forms.ChoiceField(required=False, label="Target Blood Marker")

    class Meta:
        model = SupplementMapping
        fields = '__all__'

    def __init__(self, *args, **kwargs):
        super(SupplementMappingAdminForm, self).__init__(*args, **kwargs)
        # Fetch all Blood Markers
        markers = list(Analysis.objects.values_list(
            'blood_test', flat=True).distinct().order_by('blood_test'))

        # Protect existing value
        instance = getattr(self, 'instance', None)
        if instance and instance.marker and instance.marker not in markers:
            markers.append(instance.marker)

        markers.sort(key=lambda x: (x is None, x))
        choices = [('', '👇 Select Blood Marker...')] + [(m, m)
                                                        for m in markers if m]
        self.fields['marker'].choices = choices


@admin.register(SupplementMapping)
class SupplementsMappingAdmin(admin.ModelAdmin):
    marker = forms.ChoiceField(required=False, label="Target Blood Marker")
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
