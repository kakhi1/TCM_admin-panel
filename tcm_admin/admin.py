from .models import Pattern
from django.utils.html import format_html
from django.forms.widgets import Widget
from django.utils.safestring import mark_safe
import json
from django.contrib import admin
from django import forms
from .models import (
    Analysis, Pattern, FunctionalCategory, SymptomCategory,
    MedicalCondition, WBCGlossary, WBCMatrix, MedicationList,
    MedicationMapping, MedicationScoreDef, SupplementList,
    SupplementMapping, SupplementScoreDef, LifestyleQuestionnaire,
    TCMBodyTypeMapping, TCMPathogenDefinition
)

# --- GLOBAL CONFIGURATION & ASSETS ---
# Common media config to ensure Select2 loads for all search-enabled forms
SHARED_MEDIA = {
    'css': {
        'all': (
            'https://cdnjs.cloudflare.com/ajax/libs/select2/4.0.13/css/select2.min.css',
            'admin/css/admin_enhanced.css',
        )
    },
    'js': (
        'https://code.jquery.com/jquery-3.6.0.min.js',
        'https://cdnjs.cloudflare.com/ajax/libs/select2/4.0.13/js/select2.full.min.js',
        'admin/js/admin_select2_setup.js',

    )
}


WIDGET_ATTRS = {
    'class': 'advanced-select',
    'style': 'width: 100%'
}

# --- HELPER FUNCTIONS FOR TEXT-BASED RELATIONS ---


def list_to_semicolon_string(cleaned_data_list):
    """Converts list back to 'Item A; Item B' string for DB storage."""
    if not cleaned_data_list:
        return ""
    return "; ".join([str(item) for item in cleaned_data_list])


def get_initial_list(db_string, master_list):
    """Converts DB string 'Item A; Item B' into list for widget."""
    if not db_string:
        return []
    items = [x.strip() for x in db_string.split(';')]
    # Safety: Add item to master list if it exists in DB but not in source
    for item in items:
        if item and item not in master_list:
            master_list.append(item)
    return items


class PairedSemicolonWidget(Widget):
    """
    A custom widget that renders a list of (Name + Magnitude) pairs.
    Now supports a custom header label (e.g., 'Medication Type' vs 'Supplement Type').
    """
    template_name = 'django/forms/widgets/textarea.html'

    # 1. Update __init__ to accept a label_text argument (Default is "Medication Type")
    def __init__(self, magnitude_field_name, label_text="Medication Type", *args, **kwargs):
        self.magnitude_field_name = magnitude_field_name
        self.label_text = label_text  # Store the label
        super().__init__(*args, **kwargs)

    def render(self, name, value, attrs=None, renderer=None):
        main_id = attrs.get('id', name)
        mag_id = main_id.replace(name, self.magnitude_field_name)
        current_types = value if value is not None else ''

        # 2. Use self.label_text in the HTML string instead of hardcoded text
        html = f"""
        <div id="wrapper_{main_id}" class="paired-widget-wrapper" 
             data-main-id="{main_id}" data-mag-id="{mag_id}"
             style="border: 1px solid #ccc; padding: 10px; border-radius: 4px; background: #f9f9f9;">
             
            <table class="paired-table" style="width: 100%; text-align: left;">
                <thead>
                    <tr>
                        <th style="width: 70%">{self.label_text}</th>  <th style="width: 20%">Magnitude (1-3)</th>
                        <th style="width: 10%">Action</th>
                    </tr>
                </thead>
                <tbody id="tbody_{main_id}">
                    </tbody>
            </table>
            
            <div style="margin-top: 10px;">
                <button type="button" id="btn_add_{main_id}" class="button" style="font-weight: bold;">+ Add Row</button>
            </div>
            
            <input type="hidden" name="{name}" id="{main_id}" value="{current_types}">
        </div>
        
        <script>
        // ... (Keep the rest of the script exactly the same as before) ...
        (function($) {{
            $(document).ready(function() {{
                var wrapper = $('#wrapper_{main_id}');
                var typesInput = $('#{main_id}');
                var magsInput = $('#{mag_id}');
                var tbody = $('#tbody_{main_id}');
                var addBtn = $('#btn_add_{main_id}');

                magsInput.closest('.form-row').hide();
                if(magsInput.closest('.form-row').length === 0) {{
                    magsInput.attr('type', 'hidden'); 
                    $('label[for="{mag_id}"]').hide();
                }}

                function addRow(typeVal, magVal) {{
                    typeVal = typeVal || '';
                    magVal = magVal || '1';
                    var rowId = 'row_' + Math.random().toString(36).substr(2, 9);
                    
                    var html = `
                        <tr id="${{rowId}}">
                            <td>
                                <input type="text" class="vTextField sync-input" 
                                       value="${{typeVal.replace(/"/g, '&quot;')}}" 
                                       style="width: 95%;" placeholder="e.g. Item Name">
                            </td>
                            <td>
                                <select class="sync-select" style="width: 100%;">
                                    <option value="1" ${{magVal == '1' ? 'selected' : ''}}>1</option>
                                    <option value="2" ${{magVal == '2' ? 'selected' : ''}}>2</option>
                                    <option value="3" ${{magVal == '3' ? 'selected' : ''}}>3</option>
                                </select>
                            </td>
                            <td>
                                <button type="button" class="remove-btn" 
                                        style="color: red; cursor: pointer; border: none; background: none; font-weight: bold;">
                                    ✖
                                </button>
                            </td>
                        </tr>
                    `;
                    tbody.append(html);
                }}

                function updateHiddenInputs() {{
                    var typeArr = [];
                    var magArr = [];
                    tbody.find('tr').each(function() {{
                        var t = $(this).find('.sync-input').val();
                        var m = $(this).find('.sync-select').val();
                        if (t && t.trim() !== '') {{
                            typeArr.push(t.replace(/;/g, ',').trim());
                            magArr.push(m);
                        }}
                    }});
                    typesInput.val(typeArr.join('; '));
                    magsInput.val(magArr.join('; '));
                }}

                function init() {{
                    var tRaw = typesInput.val() || '';
                    var mRaw = magsInput.val() || '';
                    var types = tRaw.split(';');
                    var mags = mRaw.split(';');
                    tbody.empty();
                    for (var i = 0; i < types.length; i++) {{
                        var t = types[i].trim();
                        if (t) {{
                            var m = (mags[i]) ? mags[i].trim() : '1';
                            addRow(t, m);
                        }}
                    }}
                }}

                addBtn.on('click', function() {{ addRow('', '1'); }});
                tbody.on('click', '.remove-btn', function() {{
                    $(this).closest('tr').remove();
                    updateHiddenInputs();
                }});
                tbody.on('change keyup', '.sync-input, .sync-select', function() {{
                    updateHiddenInputs();
                }});
                init();
            }});
        }})(django.jQuery);
        </script>
        """
        return mark_safe(html)
# ==============================================================================
# 1. ANALYSIS (Search: Name, Acronym)
# ==============================================================================


class AnalysisAdminForm(forms.ModelForm):
    # Searchable Multi-Select Widgets for text-based relationships
    tcm_diag_low = forms.MultipleChoiceField(
        required=False, label="TCM Diagnosis (Low)", widget=forms.SelectMultiple(attrs=WIDGET_ATTRS))
    tcm_diag_high = forms.MultipleChoiceField(
        required=False, label="TCM Diagnosis (High)", widget=forms.SelectMultiple(attrs=WIDGET_ATTRS))
    func_diag_low = forms.MultipleChoiceField(
        required=False, label="Functional Med Diagnosis (Low)", widget=forms.SelectMultiple(attrs=WIDGET_ATTRS))
    func_diag_high = forms.MultipleChoiceField(
        required=False, label="Functional Med Diagnosis (High)", widget=forms.SelectMultiple(attrs=WIDGET_ATTRS))

    class Meta:
        model = Analysis
        fields = '__all__'

    @property
    def media(self):
        return forms.Media(**SHARED_MEDIA)

    def __init__(self, *args, **kwargs):
        super(AnalysisAdminForm, self).__init__(*args, **kwargs)

        # 1. Fetch Source Data
        patterns = list(Pattern.objects.values_list(
            'tcm_patterns', flat=True).distinct().order_by('tcm_patterns'))
        func_cats = list(FunctionalCategory.objects.values_list(
            'functional_medicine', flat=True).distinct().order_by('functional_medicine'))

        # 2. Populate Widget Choices
        # Note: We filter out empty strings
        p_choices = [(p, p) for p in patterns if p]
        f_choices = [(f, f) for f in func_cats if f]

        self.fields['tcm_diag_low'].choices = p_choices
        self.fields['tcm_diag_high'].choices = p_choices
        self.fields['func_diag_low'].choices = f_choices
        self.fields['func_diag_high'].choices = f_choices

        # 3. Set Initial Values (Parse String -> List)
        instance = getattr(self, 'instance', None)
        if instance and instance.pk:
            # We pass a list of JUST the keys/values to helper
            p_flat = [p for p in patterns if p]
            f_flat = [f for f in func_cats if f]

            self.initial['tcm_diag_low'] = get_initial_list(
                instance.tcm_diag_low, p_flat)
            self.initial['tcm_diag_high'] = get_initial_list(
                instance.tcm_diag_high, p_flat)
            self.initial['func_diag_low'] = get_initial_list(
                instance.func_diag_low, f_flat)
            self.initial['func_diag_high'] = get_initial_list(
                instance.func_diag_high, f_flat)

    # Save Logic: Convert List -> String
    def clean_tcm_diag_low(self): return list_to_semicolon_string(
        self.cleaned_data['tcm_diag_low'])

    def clean_tcm_diag_high(self): return list_to_semicolon_string(
        self.cleaned_data['tcm_diag_high'])

    def clean_func_diag_low(self): return list_to_semicolon_string(
        self.cleaned_data['func_diag_low'])
    def clean_func_diag_high(self): return list_to_semicolon_string(
        self.cleaned_data['func_diag_high'])


# @admin.register(Analysis)
# class AnalysisAdmin(admin.ModelAdmin):
#     form = AnalysisAdminForm

#     # --- ADDED SEARCH FIELDS ---
#     search_fields = ('blood_test', 'blood_test_full',
#                      'blood_test_acronym', 'panel')

#     # --- LIST DISPLAY UPDATED WITH CLICK WRAPPERS ---
#     list_display = (
#         'panel', 'blood_test', 'blood_test_full', 'blood_test_acronym',
#         'units', 'units_interchangeable', 'ideal_low', 'ideal_high',
#         'absence_low', 'absence_high', 'severity', 'vital_marker',

#         # Updated fields using the _click wrappers
#         'tcm_diag_low', 'tcm_diag_high',
#         'func_diag_low_click', 'func_diag_high_click',
#         'conv_diag_low_click', 'conv_diag_high_click',
#         'organs_conv_func_click', 'organs_tcm_click',
#         'possible_assoc_pathogens_click',

#         'pathogens_low', 'pathogens_high',
#         'func_panel_1', 'func_panel_2', 'func_panel_3'
#     )
#     list_display_links = ('blood_test', 'panel',)

#     fieldsets = (
#         ('Blood Marker Identification', {
#             'fields': ('panel', 'blood_test', 'blood_test_full', 'blood_test_acronym', 'vital_marker')
#         }),
#         ('Ranges & Severity', {
#             'fields': (('ideal_low', 'ideal_high'), ('absence_low', 'absence_high'), 'severity')
#         }),
#         ('Medicine & TCM Diagnoses', {
#             'description': "Search and select multiple items.",
#             'fields': (
#                 'tcm_diag_low', 'tcm_diag_high',
#                 'func_diag_low', 'func_diag_high',
#             )
#         }),
#         ('Conventional Medicine Diagnoses', {
#             'fields': ('conv_diag_low', 'conv_diag_high')
#         }),
#         ('Organs & Pathogens', {
#             'fields': ('organs_conv_func', 'organs_tcm', 'possible_assoc_pathogens', 'pathogens_low', 'pathogens_high')
#         }),
#         ('Functional Panels', {
#             'fields': ('func_panel_1', 'func_panel_2', 'func_panel_3')
#         }),
#         ('Units', {
#             'fields': ('units', 'units_interchangeable')
#         }),
#     )
#     list_filter = ('panel', 'severity')
#     list_per_page = 50

#     # --- HELPER FOR TOGGLING TEXT ---
#     def _create_click_to_open(self, text):
#         """
#         Creates a toggleable text field using simple JavaScript.
#         """
#         if not text:
#             return "-"

#         # If text is short, just show it
#         if len(text) <= 50:
#             return text

#         short_text = text[:50] + "..."

#         # Two divs: one for short view, one for full view.
#         return format_html(
#             '<div class="text-toggle-container">'
#             # -- SHORT VERSION (Click to Expand) --
#             '<div style="cursor:pointer; display:block;" '
#             'onclick="this.style.display=\'none\'; this.nextElementSibling.style.display=\'block\';">'
#             '<span>{}</span> '
#             '<span style="color:#447e9b; font-weight:bold;"> &#9662;</span>'  # Down Arrow
#             '</div>'

#             # -- FULL VERSION (Click to Collapse) --
#             '<div style="cursor:pointer; display:none;" '
#             'onclick="this.style.display=\'none\'; this.previousElementSibling.style.display=\'block\';">'
#             '<span>{}</span> '
#             '<span style="color:#447e9b; font-weight:bold;"> &#9652;</span>'  # Up Arrow
#             '</div>'
#             '</div>',
#             short_text,
#             text
#         )

#     # --- WRAPPER METHODS ---

#     def func_diag_low_click(self, obj):
#         return self._create_click_to_open(obj.func_diag_low)
#     func_diag_low_click.short_description = "Functional Med Diagnosis (Low)"

#     def func_diag_high_click(self, obj):
#         return self._create_click_to_open(obj.func_diag_high)
#     func_diag_high_click.short_description = "Functional Med Diagnosis (High)"

#     def conv_diag_low_click(self, obj):
#         return self._create_click_to_open(obj.conv_diag_low)
#     conv_diag_low_click.short_description = "Conventional Med Diagnosis (Low)"

#     def conv_diag_high_click(self, obj):
#         return self._create_click_to_open(obj.conv_diag_high)
#     conv_diag_high_click.short_description = "Conventional Med Diagnosis (High)"

#     def organs_conv_func_click(self, obj):
#         return self._create_click_to_open(obj.organs_conv_func)
#     organs_conv_func_click.short_description = "Organs (Conv & Func)"

#     def organs_tcm_click(self, obj):
#         return self._create_click_to_open(obj.organs_tcm)
#     organs_tcm_click.short_description = "Organs (TCM)"

#     def possible_assoc_pathogens_click(self, obj):
#         return self._create_click_to_open(obj.possible_assoc_pathogens)
#     possible_assoc_pathogens_click.short_description = "Possible Assoc Pathogens"

@admin.register(Analysis)
class AnalysisAdmin(admin.ModelAdmin):
    form = AnalysisAdminForm

    # --- ADDED SEARCH FIELDS ---
    search_fields = ('blood_test', 'blood_test_full',
                     'blood_test_acronym', 'panel')

    # --- LIST DISPLAY UPDATED WITH CLICK WRAPPERS ---
    list_display = (
        'panel', 'blood_test', 'blood_test_full', 'blood_test_acronym',
        'units', 'units_interchangeable', 'ideal_low', 'ideal_high',
        'absence_low', 'absence_high', 'severity', 'vital_marker',

        # Updated fields using the _click wrappers
        'tcm_diag_low', 'tcm_diag_high',
        'func_diag_low_click', 'func_diag_high_click',
        'conv_diag_low_click', 'conv_diag_high_click',
        'organs_conv_func_click', 'organs_tcm_click',
        'possible_assoc_pathogens_click',

        'pathogens_low', 'pathogens_high',
        'func_panel_1', 'func_panel_2', 'func_panel_3'
    )
    list_display_links = ('blood_test', 'panel',)

    fieldsets = (
        ('Blood Marker Identification', {
            'fields': ('panel', 'blood_test', 'blood_test_full', 'blood_test_acronym', 'vital_marker')
        }),
        ('Ranges & Severity', {
            'fields': (('ideal_low', 'ideal_high'), ('absence_low', 'absence_high'), 'severity')
        }),
        ('Medicine & TCM Diagnoses', {
            'description': "Search and select multiple items.",
            'fields': (
                'tcm_diag_low', 'tcm_diag_high',
                'func_diag_low', 'func_diag_high',
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
    list_filter = ('panel', 'severity')
    list_per_page = 50

    # --- HELPER FOR TOGGLING TEXT ---
    def _create_click_to_open(self, text):
        """
        Creates a toggleable text field using simple JavaScript.
        """
        if not text:
            return "-"

        # If text is short, just show it
        if len(text) <= 50:
            return text

        short_text = text[:50] + "..."

        # Two divs: one for short view, one for full view.
        return format_html(
            '<div class="text-toggle-container">'
            # -- SHORT VERSION (Click to Expand) --
            '<div style="cursor:pointer; display:block;" '
            'onclick="this.style.display=\'none\'; this.nextElementSibling.style.display=\'block\';">'
            '<span>{}</span> '
            '<span style="color:#447e9b; font-weight:bold;"> &#9662;</span>'  # Down Arrow
            '</div>'

            # -- FULL VERSION (Click to Collapse) --
            '<div style="cursor:pointer; display:none;" '
            'onclick="this.style.display=\'none\'; this.previousElementSibling.style.display=\'block\';">'
            '<span>{}</span> '
            '<span style="color:#447e9b; font-weight:bold;"> &#9652;</span>'  # Up Arrow
            '</div>'
            '</div>',
            short_text,
            text
        )

    # --- WRAPPER METHODS ---

    def func_diag_low_click(self, obj):
        return self._create_click_to_open(obj.func_diag_low)
    func_diag_low_click.short_description = "Functional Med Diagnosis (Low)"

    def func_diag_high_click(self, obj):
        return self._create_click_to_open(obj.func_diag_high)
    func_diag_high_click.short_description = "Functional Med Diagnosis (High)"

    def conv_diag_low_click(self, obj):
        return self._create_click_to_open(obj.conv_diag_low)
    conv_diag_low_click.short_description = "Conventional Med Diagnosis (Low)"

    def conv_diag_high_click(self, obj):
        return self._create_click_to_open(obj.conv_diag_high)
    conv_diag_high_click.short_description = "Conventional Med Diagnosis (High)"

    def organs_conv_func_click(self, obj):
        return self._create_click_to_open(obj.organs_conv_func)
    organs_conv_func_click.short_description = "Organs (Conv & Func)"

    def organs_tcm_click(self, obj):
        return self._create_click_to_open(obj.organs_tcm)
    organs_tcm_click.short_description = "Organs (TCM)"

    def possible_assoc_pathogens_click(self, obj):
        return self._create_click_to_open(obj.possible_assoc_pathogens)
    possible_assoc_pathogens_click.short_description = "Possible Assoc Pathogens"

# ==============================================================================
# 2. PATTERNS (Search: Name | Select: Body Type, Pathogen)
# ==============================================================================


class SemicolonListWidget(Widget):
    """
    A custom widget that renders a list of text items.
    User adds rows, system saves as 'Item A; Item B; Item C'.
    """
    template_name = 'django/forms/widgets/textarea.html'

    def render(self, name, value, attrs=None, renderer=None):
        main_id = attrs.get('id', name)
        current_val = value if value is not None else ''

        html = f"""
        <div id="wrapper_{main_id}" style="border: 1px solid #ccc; padding: 10px; border-radius: 4px; background: #f9f9f9;">
            <table style="width: 100%; text-align: left;">
                <thead>
                    <tr>
                        <th style="width: 90%">Symptom / Item</th>
                        <th style="width: 10%">Action</th>
                    </tr>
                </thead>
                <tbody id="tbody_{main_id}">
                </tbody>
            </table>
            
            <div style="margin-top: 10px;">
                <button type="button" id="btn_add_{main_id}" class="button" style="font-weight: bold;">+ Add Item</button>
            </div>
            
            <input type="hidden" name="{name}" id="{main_id}" value="{current_val}">
        </div>

        <script>
        (function($) {{
            $(document).ready(function() {{
                var input = $('#{main_id}');
                var tbody = $('#tbody_{main_id}');
                var addBtn = $('#btn_add_{main_id}');

                function addRow(val) {{
                    val = val || '';
                    var rowId = 'row_' + Math.random().toString(36).substr(2, 9);
                    
                    var html = `
                        <tr id="${{rowId}}">
                            <td>
                                <input type="text" class="vTextField sync-input" 
                                       value="${{val.replace(/"/g, '&quot;')}}" 
                                       style="width: 98%;" placeholder="e.g. Headache">
                            </td>
                            <td>
                                <button type="button" class="remove-btn" 
                                        style="color: red; cursor: pointer; border: none; background: none; font-weight: bold;">
                                    ✖
                                </button>
                            </td>
                        </tr>
                    `;
                    tbody.append(html);
                }}

                function updateHiddenInput() {{
                    var arr = [];
                    tbody.find('.sync-input').each(function() {{
                        var t = $(this).val();
                        if (t && t.trim() !== '') {{
                            // Replace semicolons to prevent corruption, then trim
                            arr.push(t.replace(/;/g, ',').trim());
                        }}
                    }});
                    input.val(arr.join(';'));
                }}

                // Init
                var raw = input.val() || '';
                if(raw) {{
                    var items = raw.split(';');
                    items.forEach(function(item) {{
                        if(item.trim()) addRow(item.trim());
                    }});
                }}

                // Events
                addBtn.on('click', function() {{ addRow(''); }});
                
                tbody.on('click', '.remove-btn', function() {{
                    $(this).closest('tr').remove();
                    updateHiddenInput();
                }});

                tbody.on('change keyup', '.sync-input', function() {{
                    updateHiddenInput();
                }});
            }});
        }})(django.jQuery);
        </script>
        """
        return mark_safe(html)


class PatternAdminForm(forms.ModelForm):
    # 1. Body Types (Primary, Secondary, Tertiary)
    body_type_primary = forms.ChoiceField(
        required=False, label="TCM Body Type - Primary", widget=forms.Select(attrs=WIDGET_ATTRS))
    body_type_secondary = forms.ChoiceField(
        required=False, label="TCM Body Type - Secondary", widget=forms.Select(attrs=WIDGET_ATTRS))
    body_type_tertiary = forms.ChoiceField(
        required=False, label="TCM Body Type - Tertiary", widget=forms.Select(attrs=WIDGET_ATTRS))

    # 2. Pathogen
    pathogenic_factor = forms.ChoiceField(
        required=False, label="Pathogenic Factor", widget=forms.Select(attrs=WIDGET_ATTRS))

    # 3. Excess/Deficiency/General (Fixed Choices)
    excess_deficiency = forms.ChoiceField(
        choices=[
            ('', 'Select Type...'),
            ('Excess', 'Excess'),
            ('Deficiency', 'Deficiency'),
            ('General', 'General')
        ],
        required=False,
        label="Excess/Deficiency/General",
        widget=forms.Select(attrs=WIDGET_ATTRS)
    )

    class Meta:
        model = Pattern
        fields = '__all__'
        # 4. Apply the Semicolon Widget to Symptoms
        widgets = {
            'symptoms': SemicolonListWidget(),
        }

    @property
    def media(self): return forms.Media(**SHARED_MEDIA)

    def __init__(self, *args, **kwargs):
        super(PatternAdminForm, self).__init__(*args, **kwargs)

        # Load Body Types from DB
        body_types = list(TCMBodyTypeMapping.objects.values_list(
            'tcm_body_type', flat=True).distinct())

        # Load Pathogens
        pathogens = list(TCMPathogenDefinition.objects.values_list(
            'pathogen', flat=True).distinct())

        # Create Standard Choices List
        bt_choices = [('', 'Select Body Type...')] + [(b, b)
                                                      for b in body_types if b]
        p_choices = [('', 'Select Pathogen...')] + [(p, p)
                                                    for p in pathogens if p]

        # Apply Choices to Fields
        self.fields['body_type_primary'].choices = bt_choices
        self.fields['body_type_secondary'].choices = bt_choices
        self.fields['body_type_tertiary'].choices = bt_choices

        self.fields['pathogenic_factor'].choices = p_choices


@admin.register(Pattern)
class PatternAdmin(admin.ModelAdmin):
    # --- 2. CONNECT THE FORM ---
    form = PatternAdminForm

    search_fields = ('tcm_patterns', 'modern_description', 'middle_primary')

    list_display = (
        'tcm_patterns',
        'excess_deficiency',
        'modern_description_click',
        'middle_primary',
        'middle_secondary',
        'middle_tertiary',
        'middle_quantery',
        'bottom_primary',
        'bottom_secondary',
        'symptoms_click',
        'body_type_primary',
        'body_type_secondary',
        'body_type_tertiary',
        'positive_impacts_click',
        'negative_impacts_click',
        'rationale_click',
        'pathogenic_factor',
    )

    list_filter = ('tcm_patterns', 'excess_deficiency', 'middle_primary')

    # --- 3. CLEAN "SAME FRAME" TOGGLE (No extra icons) ---
    def _create_click_to_open(self, text):
        """
        Creates a toggleable text field using simple JavaScript.
        """
        if not text:
            return "-"

        # If text is short, just show it
        if len(text) <= 50:
            return text

        short_text = text[:50] + "..."

        # Two divs: one for short view, one for full view.
        # They swap display 'none' vs 'block' when clicked.
        return format_html(
            '<div class="text-toggle-container">'
            # -- SHORT VERSION (Click to Expand) --
            '<div style="cursor:pointer; display:block;" '
            'onclick="this.style.display=\'none\'; this.nextElementSibling.style.display=\'block\';">'
            '<span>{}</span> '
            '<span style="color:#447e9b; font-weight:bold;"> &#9662;</span>'  # Down Arrow
            '</div>'

            # -- FULL VERSION (Click to Collapse) --
            '<div style="cursor:pointer; display:none;" '
            'onclick="this.style.display=\'none\'; this.previousElementSibling.style.display=\'block\';">'
            '<span>{}</span> '
            '<span style="color:#447e9b; font-weight:bold;"> &#9652;</span>'  # Up Arrow
            '</div>'
            '</div>',
            short_text,
            text
        )

    # --- FIELD DEFINITIONS ---
    def modern_description_click(self, obj):
        return self._create_click_to_open(obj.modern_description)
    modern_description_click.short_description = "Modern Description"

    def symptoms_click(self, obj):
        return self._create_click_to_open(obj.symptoms)
    symptoms_click.short_description = "Symptoms"

    def positive_impacts_click(self, obj):
        return self._create_click_to_open(obj.positive_impacts)
    positive_impacts_click.short_description = "Positive Impacts"

    def negative_impacts_click(self, obj):
        return self._create_click_to_open(obj.negative_impacts)
    negative_impacts_click.short_description = "Negative Impacts"

    def rationale_click(self, obj):
        return self._create_click_to_open(obj.rationale)
    rationale_click.short_description = "Rationale"
# ==============================================================================
# 3. FUNCTIONAL & SYMPTOMS (Formatting Enforced)
# ==============================================================================

# --- Helper to format string "A, B, C" into "A, B and C" ---


def format_list_string(value):
    if not value:
        return value

    # 1. Split the input string by commas to get individual items
    #    (We also replace ' and ' with ',' just in case the user typed it manually)
    items = [item.strip() for item in value.replace(
        ' and ', ',').split(',') if item.strip()]

    count = len(items)

    if count == 0:
        return ""
    if count == 1:
        return items[0]
    if count == 2:
        return f"{items[0]} and {items[1]}"

    # For 3 or more: join all except last with commas, then add ' and ' before the last
    main_part = ", ".join(items[:-1])
    return f"{main_part} and {items[-1]}"


class FunctionalCategoryAdminForm(forms.ModelForm):
    class Meta:
        model = FunctionalCategory
        fields = '__all__'
        # Add help text so you know the format is being applied
        help_texts = {
            'primary_category': 'Enter items separated by commas (e.g., "Sleep, Stress"). System will auto-format to "Sleep and Stress".',
            'secondary_category': 'Enter items separated by commas. System will auto-format to "A, B and C".',
        }

    def clean_primary_category(self):
        # Auto-format the input before saving to DB
        return format_list_string(self.cleaned_data['primary_category'])

    def clean_secondary_category(self):
        # Auto-format the input before saving to DB
        return format_list_string(self.cleaned_data['secondary_category'])


@admin.register(FunctionalCategory)
class FunctionalCategoryAdmin(admin.ModelAdmin):
    form = FunctionalCategoryAdminForm  # <--- Connect the custom form here

    # --- ADDED SEARCH FIELDS ---
    search_fields = ('functional_medicine', 'primary_category')

    # --- EXISTING STRUCTURE PRESERVED ---
    list_display = ('functional_medicine',
                    'primary_category', 'secondary_category')


class SymptomCategoryAdminForm(forms.ModelForm):
    # Lookup for Functional Category
    primary_category = forms.ChoiceField(
        required=False, widget=forms.Select(attrs=WIDGET_ATTRS))

    class Meta:
        model = SymptomCategory
        fields = '__all__'

    @property
    def media(self): return forms.Media(**SHARED_MEDIA)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Load Categories from FunctionalCategory model
        cats = list(FunctionalCategory.objects.values_list(
            'functional_medicine', flat=True).distinct())
        self.fields['primary_category'].choices = [
            ('', 'Select Category...')] + [(c, c) for c in cats if c]


class SymptomCategoryAdminForm(forms.ModelForm):
    # Lookup for Functional Category
    primary_category = forms.ChoiceField(
        required=False, widget=forms.Select(attrs=WIDGET_ATTRS))

    class Meta:
        model = SymptomCategory
        fields = '__all__'

    @property
    def media(self): return forms.Media(**SHARED_MEDIA)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Load Categories from FunctionalCategory model
        cats = list(FunctionalCategory.objects.values_list(
            'functional_medicine', flat=True).distinct())
        self.fields['primary_category'].choices = [
            ('', 'Select Category...')] + [(c, c) for c in cats if c]


class SymptomCategoryAdminForm(forms.ModelForm):
    # 1. Selector for Symptoms (Source: Pattern model)
    symptoms = forms.ChoiceField(
        required=False,
        label="Symptom (from Patterns)",
        widget=forms.Select(attrs=WIDGET_ATTRS)
    )

    class Meta:
        model = SymptomCategory
        fields = '__all__'

    @property
    def media(self):
        return forms.Media(**SHARED_MEDIA)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # --- A. Populate SYMPTOMS from Pattern model ---
        # 1. Fetch all raw symptom strings (e.g., "Headache; Nausea")
        raw_pattern_data = Pattern.objects.values_list('symptoms', flat=True)

        # 2. Parse and Flatten: Split by ';', strip whitespace, and uniquify
        unique_symptoms = set()
        for entry in raw_pattern_data:
            if entry:
                # Split by semicolon and clean up whitespace
                parts = [x.strip() for x in entry.split(';') if x.strip()]
                unique_symptoms.update(parts)

        # 3. Sort and Create Choices
        sorted_symptoms = sorted(list(unique_symptoms))
        symptom_choices = [('', 'Select Symptom...')] + [(s, s)
                                                         for s in sorted_symptoms]

        # 4. Assign to field
        self.fields['symptoms'].choices = symptom_choices

        # --- B. Populate CATEGORIES from FunctionalCategory model ---
        cats = list(FunctionalCategory.objects.values_list(
            'functional_medicine', flat=True).distinct().order_by('functional_medicine'))

        cat_choices = [('', 'Select Category...')] + [(c, c)
                                                      for c in cats if c]
        self.fields['primary_category'].choices = cat_choices

        # --- C. Set Initial Values for Edit Mode ---
        instance = getattr(self, 'instance', None)
        if instance and instance.pk:
            # If the current value isn't in the list (e.g. custom text), add it to prevent data loss
            current_sym = instance.symptoms
            if current_sym and current_sym not in unique_symptoms:
                self.fields['symptoms'].choices.append(
                    (current_sym, current_sym))

            current_cat = instance.primary_category
            if current_cat and current_cat not in cats:
                self.fields['primary_category'].choices.append(
                    (current_cat, current_cat))


@admin.register(SymptomCategory)
class SymptomCategoryAdmin(admin.ModelAdmin):
    form = SymptomCategoryAdminForm

    # --- ADDED SEARCH FIELDS ---
    search_fields = ('symptoms', 'primary_category')

    # --- EXISTING STRUCTURE PRESERVED ---
    list_display = ('symptoms', 'primary_category', 'secondary_category')
    list_filter = ('primary_category',)

# ==============================================================================
# 4. MEDICAL CONDITIONS (Search: Name | Select: Pattern, Category)
# ==============================================================================


class MedicalConditionAdminForm(forms.ModelForm):
    # 1. Searchable Multi-Select for Patterns
    tcm_patterns = forms.MultipleChoiceField(
        required=False,
        label="TCM Patterns",
        widget=forms.SelectMultiple(attrs=WIDGET_ATTRS)
    )

    # # 2. Searchable Single-Selects for ALL Category Levels
    # primary_category = forms.ChoiceField(
    #     required=False,
    #     label="Primary Category",
    #     widget=forms.Select(attrs=WIDGET_ATTRS)
    # )
    # secondary_category = forms.ChoiceField(
    #     required=False,
    #     label="Secondary Category",
    #     widget=forms.Select(attrs=WIDGET_ATTRS)
    # )
    # tertiary_category = forms.ChoiceField(
    #     required=False,
    #     label="Tertiary Category",
    #     widget=forms.Select(attrs=WIDGET_ATTRS)
    # )

    class Meta:
        model = MedicalCondition
        fields = '__all__'

    @property
    def media(self): return forms.Media(**SHARED_MEDIA)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # --- LOGIC TO FIX "MISSING CATEGORIES" & PREVENT CRASH ---

        # A. Fetch the Master List
        master_cats = set(FunctionalCategory.objects.values_list(
            'functional_medicine', flat=True))

        # B. Fetch currently used categories (including those NOT in master list)
        used_p = set(MedicalCondition.objects.values_list(
            'primary_category', flat=True))
        used_s = set(MedicalCondition.objects.values_list(
            'secondary_category', flat=True))
        used_t = set(MedicalCondition.objects.values_list(
            'tertiary_category', flat=True))

        # C. Combine all sets
        combined_set = master_cats | used_p | used_s | used_t

        # D. Filter out None/Empty values BEFORE sorting
        # This fixes the "TypeError: '<' not supported between instances of 'NoneType' and 'str'"
        all_possible_cats = sorted([cat for cat in combined_set if cat])

        # E. Create Choices
        cat_choices = [('', 'Select Category...')] + [(c, c)
                                                      for c in all_possible_cats]

        # F. Assign to fields
        self.fields['primary_category'].choices = cat_choices
        self.fields['secondary_category'].choices = cat_choices
        self.fields['tertiary_category'].choices = cat_choices

        # --- PATTERN LOGIC ---
        patterns = list(Pattern.objects.values_list(
            'tcm_patterns', flat=True).distinct().order_by('tcm_patterns'))
        # Filter out empty patterns to be safe
        self.fields['tcm_patterns'].choices = [(p, p) for p in patterns if p]

        # Initial Value for Patterns
        instance = getattr(self, 'instance', None)
        if instance and instance.pk:
            p_flat = [p for p in patterns if p]
            self.initial['tcm_patterns'] = get_initial_list(
                instance.tcm_patterns, p_flat)

    def clean_tcm_patterns(self):
        return list_to_semicolon_string(self.cleaned_data['tcm_patterns'])


@admin.register(MedicalCondition)
class MedicalConditionAdmin(admin.ModelAdmin):
    form = MedicalConditionAdminForm

    # --- ADDED SEARCH FIELDS ---
    search_fields = ('condition', 'tcm_patterns', 'rationale')

    # --- LIST DISPLAY ---
    list_display = (
        'condition', 'tcm_patterns', 'rationale',
        'primary_category', 'secondary_category', 'tertiary_category'
    )

    # --- FORM LAYOUT ---
    fields = (
        'condition', 'tcm_patterns', 'rationale',
        'primary_category', 'secondary_category', 'tertiary_category'
    )

    list_display_links = ('condition',)
    list_filter = ('primary_category', 'secondary_category')
    list_per_page = 50


# ==============================================================================
# 5. WBC GLOSSARY & MATRIX (Search Enabled)
# ==============================================================================
@admin.register(WBCGlossary)
class WBCGlossaryAdmin(admin.ModelAdmin):
    # --- ADDED SEARCH FIELDS ---
    search_fields = ('term', 'definition', 'next_steps')

    # --- EXISTING STRUCTURE PRESERVED ---
    list_display = ('term', 'definition', 'next_steps')
    fields = ('term', 'definition', 'next_steps')
    list_display_links = ('term',)
    list_per_page = 50


# --- 1. DEFINE THE CUSTOM FORM ---
class WBCMatrixAdminForm(forms.ModelForm):
    # Override risk_score to be a dropdown (1-5)
    risk_score = forms.ChoiceField(
        choices=[(None, 'Select Score')] + [(i, str(i)) for i in range(1, 6)],
        required=False,
        label="Risk Score",
        # Matches your other widgets
        widget=forms.Select(attrs={'style': 'width: 100%'})
    )

    class Meta:
        model = WBCMatrix
        fields = '__all__'


@admin.register(WBCMatrix)
class WBCMatrixAdmin(admin.ModelAdmin):
    form = WBCMatrixAdminForm
    # --- SEARCH FIELDS ---
    search_fields = ('wbc', 'primary_int', 'rationale', 'clinical_guidance')

    # --- LIST DISPLAY ---
    list_display = (
        'wbc', 'neutrophils', 'lymphocytes', 'monocytes', 'eosinophils', 'basophils',
        'primary_int', 'secondary', 'tertiary', 'quaternary', 'quinary',
        'risk_score', 'risk_level', 'confidence',
        'risk_definition_click',    # Will be 700px
        'other_considerations',
        'rationale_click',          # Will be 350px
        'clinical_guidance_click'   # Will be 350px
    )

    list_display_links = ('wbc', 'neutrophils', 'lymphocytes',
                          'monocytes', 'eosinophils', 'basophils')

    # --- FIELDSETS ---
    fieldsets = (
        ('Marker Patterns', {
            'description': "Select the deviation level for each marker.",
            'fields': (
                ('wbc', 'neutrophils'),
                ('lymphocytes', 'monocytes'),
                ('eosinophils', 'basophils')
            )
        }),
        ('Interpretation Hierarchy', {
            'fields': (
                'primary_int',
                ('secondary', 'tertiary'),
                ('quaternary', 'quinary')
            ),
            'classes': ('wide',)
        }),
        ('Risk & Analysis', {
            'fields': (
                ('risk_score', 'risk_level'),
                'confidence',
                'risk_definition',
                'other_considerations',
                'rationale',
                'clinical_guidance'
            )
        }),
    )

    list_filter = ('risk_level', 'confidence', 'wbc')
    list_per_page = 50

    # --- UPDATED LOGIC: INLINE STYLES FOR WIDTH ---
    def _create_click_to_open(self, text, width="300px"):
        """
        Creates a toggleable text field.
        Accepts a 'width' argument to force the table cell to expand.
        """
        if not text:
            return "-"

        # NOTE: We apply the min-width to the container DIV.
        # This forces the table cell to be at least this wide.
        style_str = f"min-width: {width}; white-space: normal;"

        if len(text) <= 50:
            # Even if text is short, we enforce width to keep columns aligned
            return format_html(
                f'<div style="{style_str}">{text}</div>'
            )

        short_text = text[:50] + "..."

        return format_html(
            f'<div class="text-toggle-container" style="{style_str}">'
            # -- SHORT VERSION --
            '<div style="cursor:pointer; display:block;" '
            'onclick="this.style.display=\'none\'; this.nextElementSibling.style.display=\'block\';">'
            '<span>{}</span> <span style="color:#447e9b; font-weight:bold;"> &#9662;</span></div>'

            # -- FULL VERSION --
            '<div style="cursor:pointer; display:none;" '
            'onclick="this.style.display=\'none\'; this.previousElementSibling.style.display=\'block\';">'
            '<span>{}</span> <span style="color:#447e9b; font-weight:bold;"> &#9652;</span></div>'
            '</div>',
            short_text, text
        )

    # --- WRAPPERS WITH SPECIFIC WIDTHS ---
    def rationale_click(self, obj):
        return self._create_click_to_open(obj.rationale, width="200px")
    rationale_click.short_description = "Rationale"

    def clinical_guidance_click(self, obj):
        return self._create_click_to_open(obj.clinical_guidance, width="200px")
    clinical_guidance_click.short_description = "Clinical Guidance"

    def risk_definition_click(self, obj):
        # FORCE 700PX HERE
        return self._create_click_to_open(obj.risk_definition, width="200px")
    risk_definition_click.short_description = "Risk Definition"

    # --- CLEANER CSS (Removed the broken column selectors) ---
    class Media:
        css = {
            'all': ('admin/css/admin_enhanced.css',)
        }
        extra = '''
            <style>
                /* Layout Fixes for Edit Form (Keep these!) */
                .form-row .field-box {
                    vertical-align: top; 
                    float: none !important; 
                    display: inline-block;
                    margin-right: 20px;
                }
                .form-row .field-box label {
                    display: block !important;
                    margin-bottom: 5px;
                    width: auto !important;
                }
                .form-row .field-box textarea {
                    width: 90%;
                }
            </style>
        '''

# ==============================================================================
# 6. MEDICATIONS & SUPPLEMENTS (Search: Type | Select: Marker)
# ==============================================================================


class MappingAdminFormBase(forms.ModelForm):
    # Common logic to select Blood Marker from Analysis
    marker = forms.ChoiceField(
        required=False, label="Target Blood Marker", widget=forms.Select(attrs=WIDGET_ATTRS))

    @property
    def media(self): return forms.Media(**SHARED_MEDIA)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        markers = list(Analysis.objects.values_list(
            'blood_test', flat=True).distinct().order_by('blood_test'))

        # Protect existing value if not in list
        instance = getattr(self, 'instance', None)
        if instance and instance.marker and instance.marker not in markers:
            markers.append(instance.marker)

        choices = [('', 'Select Blood Marker...')] + [(m, m)
                                                      for m in markers if m]
        self.fields['marker'].choices = choices


class MedicationMappingAdminForm(MappingAdminFormBase):
    class Meta:
        model = MedicationMapping
        fields = '__all__'


class MedicationMappingAdminForm(MappingAdminFormBase):
    class Meta:
        model = MedicationMapping
        fields = '__all__'
        widgets = {
            # Attach the custom widget to the "Types" fields.
            # We tell it which field name holds the magnitude numbers.
            'med_types_low': PairedSemicolonWidget(magnitude_field_name='magnitude_low'),
            'med_types_high': PairedSemicolonWidget(magnitude_field_name='magnitude_high'),

            # We hide the actual magnitude inputs because the widget above controls them
            'magnitude_low': forms.HiddenInput(),
            'magnitude_high': forms.HiddenInput(),
        }


@admin.register(MedicationList)
class MedicationListAdmin(admin.ModelAdmin):
    # --- ADDED SEARCH FIELDS ---
    search_fields = ('category', 'example_medications',
                     'tcm_narrative_no_effect')

    # --- EXISTING STRUCTURE PRESERVED ---
    list_display = ('category', 'sub_category', 'example_medications',
                    'do_not_effect', 'tcm_narrative_no_effect')
    fields = ('category', 'sub_category', 'example_medications',
              'do_not_effect', 'tcm_narrative_no_effect')
    list_display_links = ('category', 'sub_category')
    list_filter = ('category',)
    list_per_page = 50


# @admin.register(MedicationMapping)
# class MedicationMappingAdmin(admin.ModelAdmin):
#     form = MedicationMappingAdminForm

#     # --- ADDED SEARCH FIELDS ---
#     search_fields = ('marker', 'panel', 'med_types_low', 'med_types_high')

#     # --- EXISTING STRUCTURE PRESERVED ---
#     list_display = (
#         'panel', 'marker', 'med_types_low', 'magnitude_low', 'med_types_high',
#         'magnitude_high', 'narrative_low', 'narrative_high', 'tcm_narrative_low', 'tcm_narrative_high'
#     )
#     fields = (
#         'panel', 'marker', 'med_types_low', 'magnitude_low', 'med_types_high',
#         'magnitude_high', 'narrative_low', 'narrative_high', 'tcm_narrative_low', 'tcm_narrative_high'
#     )
#     list_display_links = ('marker', 'panel')
#     list_filter = ('panel', 'magnitude_low', 'magnitude_high')
#     list_per_page = 50

@admin.register(MedicationMapping)
class MedicationMappingAdmin(admin.ModelAdmin):
    form = MedicationMappingAdminForm

    # --- ADDED SEARCH FIELDS ---
    search_fields = ('marker', 'panel', 'med_types_low', 'med_types_high')

    # --- LIST DISPLAY UPDATED ---
    list_display = (
        'panel',
        'marker',
        'med_types_low',
        'magnitude_low',
        'med_types_high',
        'magnitude_high',
        'narrative_low_click',       # Updated with width
        'narrative_high_click',      # Updated with width
        'tcm_narrative_low_click',   # Updated with width
        'tcm_narrative_high_click'   # Updated with width
    )

    fields = (
        'panel', 'marker', 'med_types_low', 'magnitude_low', 'med_types_high',
        'magnitude_high', 'narrative_low', 'narrative_high', 'tcm_narrative_low', 'tcm_narrative_high'
    )
    list_display_links = ('marker', 'panel')
    list_filter = ('panel', 'magnitude_low', 'magnitude_high')
    list_per_page = 50

    # --- HELPER FOR TOGGLING TEXT WITH WIDTH CONTROL ---
    def _create_click_to_open(self, text, width="200px"):
        """
        Creates a toggleable text field with a specific minimum width.
        """
        if not text:
            return "-"

        # Apply min-width and ensure text wraps normally
        style_str = f"min-width: {width}; white-space: normal;"

        # If text is short, we still apply the width to keep the column stable
        if len(text) <= 50:
            return format_html(f'<div style="{style_str}">{text}</div>')

        short_text = text[:50] + "..."

        # Two divs: one for short view, one for full view.
        return format_html(
            f'<div class="text-toggle-container" style="{style_str}">'
            # -- SHORT VERSION (Click to Expand) --
            '<div style="cursor:pointer; display:block;" '
            'onclick="this.style.display=\'none\'; this.nextElementSibling.style.display=\'block\';">'
            '<span>{}</span> '
            '<span style="color:#447e9b; font-weight:bold;"> &#9662;</span>'  # Down Arrow
            '</div>'

            # -- FULL VERSION (Click to Collapse) --
            '<div style="cursor:pointer; display:none;" '
            'onclick="this.style.display=\'none\'; this.previousElementSibling.style.display=\'block\';">'
            '<span>{}</span> '
            '<span style="color:#447e9b; font-weight:bold;"> &#9652;</span>'  # Up Arrow
            '</div>'
            '</div>',
            short_text,
            text
        )

    # --- WRAPPER METHODS (PASSING 200px WIDTH) ---

    def narrative_low_click(self, obj):
        return self._create_click_to_open(obj.narrative_low, width="200px")
    narrative_low_click.short_description = "Narrative – how ↓ meds lower/mask (E)"

    def narrative_high_click(self, obj):
        return self._create_click_to_open(obj.narrative_high, width="200px")
    narrative_high_click.short_description = "Narrative – how ↑ meds raise/mask (F)"

    def tcm_narrative_low_click(self, obj):
        return self._create_click_to_open(obj.tcm_narrative_low, width="200px")
    tcm_narrative_low_click.short_description = "TCM narrative – for ↓ meds"

    def tcm_narrative_high_click(self, obj):
        return self._create_click_to_open(obj.tcm_narrative_high, width="200px")
    tcm_narrative_high_click.short_description = "TCM narrative – for ↑ meds"


@admin.register(MedicationScoreDef)
class MedicationScoreDefAdmin(admin.ModelAdmin):
    list_display = ('score', 'definition')


@admin.register(SupplementList)
class SupplementsListAdmin(admin.ModelAdmin):
    # --- ADDED SEARCH FIELDS ---
    search_fields = ('category', 'example_supplements', 'normal_narrative')

    # --- EXISTING STRUCTURE PRESERVED ---
    list_display = ('category', 'sub_category',
                    'example_supplements', 'normal_narrative', 'tcm_narrative')
    fields = ('category', 'sub_category', 'example_supplements',
              'normal_narrative', 'tcm_narrative')
    list_display_links = ('category', 'sub_category')
    list_filter = ('category',)
    list_per_page = 50


class SupplementMappingAdminForm(MappingAdminFormBase):
    class Meta:
        model = SupplementMapping
        fields = '__all__'
        widgets = {
            # Pass label_text="Supplement Type" here
            'supp_types_low': PairedSemicolonWidget(
                magnitude_field_name='magnitude_low',
                label_text="Supplement Type"
            ),

            # Pass label_text="Supplement Type" here
            'supp_types_high': PairedSemicolonWidget(
                magnitude_field_name='magnitude_high',
                label_text="Supplement Type"
            ),

            'magnitude_low': forms.HiddenInput(),
            'magnitude_high': forms.HiddenInput(),
        }


# @admin.register(SupplementMapping)
# class SupplementsMappingAdmin(admin.ModelAdmin):
#     form = SupplementMappingAdminForm

#     # --- ADDED SEARCH FIELDS ---
#     search_fields = ('marker', 'panel', 'supp_types_low', 'supp_types_high')

#     # --- EXISTING STRUCTURE PRESERVED ---
#     list_display = (
#         'panel', 'marker', 'supp_types_low', 'magnitude_low', 'supp_types_high',
#         'magnitude_high', 'narrative_low', 'narrative_high', 'tcm_narrative_low',
#         'tcm_narrative_high', 'mechanism_low', 'mechanism_high', 'interp_note_low', 'interp_note_high'
#     )
#     fields = (
#         'panel', 'marker', 'supp_types_low', 'magnitude_low', 'supp_types_high',
#         'magnitude_high', 'narrative_low', 'narrative_high', 'tcm_narrative_low',
#         'tcm_narrative_high', 'mechanism_low', 'mechanism_high', 'interp_note_low', 'interp_note_high'
#     )
#     list_display_links = ('marker', 'panel')
#     list_filter = ('panel', 'magnitude_low', 'magnitude_high')
#     list_per_page = 50


@admin.register(SupplementMapping)
class SupplementsMappingAdmin(admin.ModelAdmin):
    form = SupplementMappingAdminForm

    # --- ADDED SEARCH FIELDS ---
    search_fields = ('marker', 'panel', 'supp_types_low', 'supp_types_high')

    # --- LIST DISPLAY UPDATED WITH CLICK WRAPPERS ---
    list_display = (
        'panel', 'marker',
        'supp_types_low', 'magnitude_low',
        'supp_types_high', 'magnitude_high',
        'narrative_low_click',       # Updated
        'narrative_high_click',      # Updated
        'tcm_narrative_low_click',   # Updated
        'tcm_narrative_high_click',  # Updated
        'mechanism_low', 'mechanism_high',
        'interp_note_low_click',     # Updated
        'interp_note_high_click'     # Updated
    )

    fields = (
        'panel', 'marker', 'supp_types_low', 'magnitude_low', 'supp_types_high',
        'magnitude_high', 'narrative_low', 'narrative_high', 'tcm_narrative_low',
        'tcm_narrative_high', 'mechanism_low', 'mechanism_high', 'interp_note_low', 'interp_note_high'
    )
    list_display_links = ('marker', 'panel')
    list_filter = ('panel', 'magnitude_low', 'magnitude_high')
    list_per_page = 50

    # --- HELPER FOR TOGGLING TEXT WITH WIDTH CONTROL ---
    def _create_click_to_open(self, text, width="200px"):
        """
        Creates a toggleable text field with a specific minimum width.
        """
        if not text:
            return "-"

        # Apply min-width and ensure text wraps normally
        style_str = f"min-width: {width}; white-space: normal;"

        # If text is short, we still apply the width to keep the column stable
        if len(text) <= 50:
            return format_html(f'<div style="{style_str}">{text}</div>')

        short_text = text[:50] + "..."

        # Two divs: one for short view, one for full view.
        return format_html(
            f'<div class="text-toggle-container" style="{style_str}">'
            # -- SHORT VERSION (Click to Expand) --
            '<div style="cursor:pointer; display:block;" '
            'onclick="this.style.display=\'none\'; this.nextElementSibling.style.display=\'block\';">'
            '<span>{}</span> '
            '<span style="color:#447e9b; font-weight:bold;"> &#9662;</span>'  # Down Arrow
            '</div>'

            # -- FULL VERSION (Click to Collapse) --
            '<div style="cursor:pointer; display:none;" '
            'onclick="this.style.display=\'none\'; this.previousElementSibling.style.display=\'block\';">'
            '<span>{}</span> '
            '<span style="color:#447e9b; font-weight:bold;"> &#9652;</span>'  # Up Arrow
            '</div>'
            '</div>',
            short_text,
            text
        )

    # --- WRAPPER METHODS (PASSING WIDTH) ---

    def narrative_low_click(self, obj):
        return self._create_click_to_open(obj.narrative_low, width="250px")
    narrative_low_click.short_description = "Narrative – how ↓ supplements lower/mask"

    def narrative_high_click(self, obj):
        return self._create_click_to_open(obj.narrative_high, width="250px")
    narrative_high_click.short_description = "Narrative – how ↑ supplements raise/mask"

    def tcm_narrative_low_click(self, obj):
        return self._create_click_to_open(obj.tcm_narrative_low, width="250px")
    tcm_narrative_low_click.short_description = "TCM narrative – for ↓ supplements"

    def tcm_narrative_high_click(self, obj):
        return self._create_click_to_open(obj.tcm_narrative_high, width="250px")
    tcm_narrative_high_click.short_description = "TCM narrative – for ↑ supplements"

    def interp_note_low_click(self, obj):
        return self._create_click_to_open(obj.interp_note_low, width="200px")
    interp_note_low_click.short_description = "Interpretation Note ↓"

    def interp_note_high_click(self, obj):
        return self._create_click_to_open(obj.interp_note_high, width="200px")
    interp_note_high_click.short_description = "Interpretation Note ↑"


@admin.register(SupplementScoreDef)
class SupplementScoreDefAdmin(admin.ModelAdmin):
    list_display = ('score', 'definition')


# ==============================================================================
# 7. LIFESTYLE & TCM DEFINITIONS (Search Enabled)
# ==============================================================================
@admin.register(LifestyleQuestionnaire)
class LifestyleQuestionnaireAdmin(admin.ModelAdmin):
    # --- ADDED SEARCH FIELDS ---
    search_fields = ('question', 'func_perspective', 'tcm_perspective')

    # --- EXISTING STRUCTURE PRESERVED ---
    list_display = (
        'question_number', 'question', 'answer_option',
        'sub_answer', 'func_perspective', 'tcm_perspective'
    )
    fields = (
        'question_number', 'question', 'answer_option',
        'sub_answer', 'func_perspective', 'tcm_perspective'
    )
    list_display_links = ('question_number', 'question')
    list_filter = ('question_number',)


@admin.register(TCMBodyTypeMapping)
class TCMBodyTypeMappingAdmin(admin.ModelAdmin):
    # --- ADDED SEARCH FIELDS ---
    search_fields = ('tcm_body_type', 'func_equivalent', 'tcm_explanation')

    # --- EXISTING STRUCTURE PRESERVED ---
    list_display = (
        'tcm_body_type', 'tcm_explanation',
        'func_equivalent', 'func_explanation'
    )
    fields = (
        'tcm_body_type', 'tcm_explanation',
        'func_equivalent', 'func_explanation'
    )
    list_display_links = ('tcm_body_type',)
    list_per_page = 50


@admin.register(TCMPathogenDefinition)
class TCMPathogenDefinitionAdmin(admin.ModelAdmin):
    # --- ADDED SEARCH FIELDS ---
    search_fields = ('pathogen', 'definition')

    # --- EXISTING STRUCTURE PRESERVED ---
    list_display = ('pathogen', 'definition')
