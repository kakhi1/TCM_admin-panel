from django.utils.html import escape
from django.utils.html import escape  # Import this
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
# --- NEW HELPER FUNCTIONS & CUSTOM FIELD ---


def list_to_oxford_string(cleaned_data_list):
    """
    Converts list ['Sleep', 'Stress'] -> 'Sleep and Stress'
    """
    if not cleaned_data_list:
        return ""
    items = [str(x).strip() for x in cleaned_data_list if x.strip()]
    count = len(items)
    if count == 0:
        return ""
    if count == 1:
        return items[0]
    main_part = ", ".join(items[:-1])
    return f"{main_part} and {items[-1]}"


def get_initial_oxford_list(db_string, master_list=None):
    """
    Converts string 'Sleep, Stress and Diet' -> List ['Sleep', 'Stress', 'Diet']
    """
    if not db_string:
        return []
    # Normalize ' and ' to comma, then split
    normalized = db_string.replace(' and ', ',').replace(', and ', ',')
    items = [x.strip() for x in normalized.split(',') if x.strip()]

    # Add to master list if strictly needed to ensure it appears selected
    if master_list is not None:
        for item in items:
            if item and (item, item) not in master_list:
                master_list.append((item, item))
    return items


class DynamicMultipleChoiceField(forms.MultipleChoiceField):
    """
    Allows adding NEW values (Tags) that aren't in the initial list.
    """

    def validate(self, value):
        if self.required and not value:
            raise forms.ValidationError(
                self.error_messages['required'], code='required')
        return True
# --- CUSTOM FORM FOR SCORE DEFINITIONS ---


class ScoreDefAdminForm(forms.ModelForm):
    # 1. Use CharField so you can type text (e.g., "1 = Minor")
    score = forms.CharField(
        required=True,
        label="Score (e.g. '1 = Minor')",
        # 2. Use TextInput widget (standard text box)
        widget=forms.TextInput(attrs={'style': 'width: 300px;'})
    )

    definition = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={'rows': 5, 'style': 'width: 100%'})
    )

    class Meta:
        fields = '__all__'


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


# class PairedSemicolonWidget(Widget):
#     """
#     A custom widget that renders a list of (Name + Magnitude) pairs.
#     Now supports a custom header label (e.g., 'Medication Type' vs 'Supplement Type').
#     """
#     template_name = 'django/forms/widgets/textarea.html'

#     # 1. Update __init__ to accept a label_text argument (Default is "Medication Type")
#     def __init__(self, magnitude_field_name, label_text="Medication Type", *args, **kwargs):
#         self.magnitude_field_name = magnitude_field_name
#         self.label_text = label_text  # Store the label
#         super().__init__(*args, **kwargs)

#     def render(self, name, value, attrs=None, renderer=None):
#         main_id = attrs.get('id', name)
#         mag_id = main_id.replace(name, self.magnitude_field_name)
#         current_types = value if value is not None else ''

#         # 2. Use self.label_text in the HTML string instead of hardcoded text
#         html = f"""
#         <div id="wrapper_{main_id}" class="paired-widget-wrapper"
#              data-main-id="{main_id}" data-mag-id="{mag_id}"
#              style="border: 1px solid #ccc; padding: 10px; border-radius: 4px; background: #f9f9f9;">

#             <table class="paired-table" style="width: 100%; text-align: left;">
#                 <thead>
#                     <tr>
#                         <th style="width: 70%">{self.label_text}</th>  <th style="width: 20%">Magnitude (1-3)</th>
#                         <th style="width: 10%">Action</th>
#                     </tr>
#                 </thead>
#                 <tbody id="tbody_{main_id}">
#                     </tbody>
#             </table>

#             <div style="margin-top: 10px;">
#                 <button type="button" id="btn_add_{main_id}" class="button" style="font-weight: bold;">+ Add Row</button>
#             </div>

#             <input type="hidden" name="{name}" id="{main_id}" value="{current_types}">
#         </div>

#         <script>
#         // ... (Keep the rest of the script exactly the same as before) ...
#         (function($) {{
#             $(document).ready(function() {{
#                 var wrapper = $('#wrapper_{main_id}');
#                 var typesInput = $('#{main_id}');
#                 var magsInput = $('#{mag_id}');
#                 var tbody = $('#tbody_{main_id}');
#                 var addBtn = $('#btn_add_{main_id}');

#                 magsInput.closest('.form-row').hide();
#                 if(magsInput.closest('.form-row').length === 0) {{
#                     magsInput.attr('type', 'hidden');
#                     $('label[for="{mag_id}"]').hide();
#                 }}

#                 function addRow(typeVal, magVal) {{
#                     typeVal = typeVal || '';
#                     magVal = magVal || '1';
#                     var rowId = 'row_' + Math.random().toString(36).substr(2, 9);

#                     var html = `
#                         <tr id="${{rowId}}">
#                             <td>
#                                 <input type="text" class="vTextField sync-input"
#                                        value="${{typeVal.replace(/"/g, '&quot;')}}"
#                                        style="width: 95%;" placeholder="e.g. Item Name">
#                             </td>
#                             <td>
#                                 <select class="sync-select" style="width: 100%;">
#                                     <option value="1" ${{magVal == '1' ? 'selected' : ''}}>1</option>
#                                     <option value="2" ${{magVal == '2' ? 'selected' : ''}}>2</option>
#                                     <option value="3" ${{magVal == '3' ? 'selected' : ''}}>3</option>
#                                 </select>
#                             </td>
#                             <td>
#                                 <button type="button" class="remove-btn"
#                                         style="color: red; cursor: pointer; border: none; background: none; font-weight: bold;">
#                                     ✖
#                                 </button>
#                             </td>
#                         </tr>
#                     `;
#                     tbody.append(html);
#                 }}

#                 function updateHiddenInputs() {{
#                     var typeArr = [];
#                     var magArr = [];
#                     tbody.find('tr').each(function() {{
#                         var t = $(this).find('.sync-input').val();
#                         var m = $(this).find('.sync-select').val();
#                         if (t && t.trim() !== '') {{
#                             typeArr.push(t.replace(/;/g, ',').trim());
#                             magArr.push(m);
#                         }}
#                     }});
#                     typesInput.val(typeArr.join('; '));
#                     magsInput.val(magArr.join('; '));
#                 }}

#                 function init() {{
#                     var tRaw = typesInput.val() || '';
#                     var mRaw = magsInput.val() || '';
#                     var types = tRaw.split(';');
#                     var mags = mRaw.split(';');
#                     tbody.empty();
#                     for (var i = 0; i < types.length; i++) {{
#                         var t = types[i].trim();
#                         if (t) {{
#                             var m = (mags[i]) ? mags[i].trim() : '1';
#                             addRow(t, m);
#                         }}
#                     }}
#                 }}

#                 addBtn.on('click', function() {{ addRow('', '1'); }});
#                 tbody.on('click', '.remove-btn', function() {{
#                     $(this).closest('tr').remove();
#                     updateHiddenInputs();
#                 }});
#                 tbody.on('change keyup', '.sync-input, .sync-select', function() {{
#                     updateHiddenInputs();
#                 }});
#                 init();
#             }});
#         }})(django.jQuery);
#         </script>
#         """
#         return mark_safe(html)


# class PairedSemicolonWidget(Widget):
#     """
#     A custom widget that renders a list of (Name + Magnitude) pairs.
#     Now supports a 'data_choices' list to create a dropdown (datalist) for the Name field.
#     """
#     template_name = 'django/forms/widgets/textarea.html'

#     def __init__(self, magnitude_field_name, label_text="Medication Type", data_choices=None, *args, **kwargs):
#         self.magnitude_field_name = magnitude_field_name
#         self.label_text = label_text
#         # Store choices here. Defaults to empty, populated via Form __init__
#         self.data_choices = data_choices if data_choices is not None else []
#         super().__init__(*args, **kwargs)

#     def render(self, name, value, attrs=None, renderer=None):
#         main_id = attrs.get('id', name)
#         mag_id = main_id.replace(name, self.magnitude_field_name)
#         current_types = value if value is not None else ''

#         # Generate a unique ID for the datalist based on the input ID
#         datalist_id = f"list_{main_id}"

#         # Build the <datalist> HTML options from self.data_choices
#         options_html = ""
#         for item in self.data_choices:
#             # Escape quotes to prevent HTML breaking
#             clean_item = str(item).replace('"', '&quot;')
#             options_html += f'<option value="{clean_item}">'

#         html = f"""
#         <div id="wrapper_{main_id}" class="paired-widget-wrapper"
#              data-main-id="{main_id}" data-mag-id="{mag_id}"
#              style="border: 1px solid #ccc; padding: 10px; border-radius: 4px; background: #f9f9f9;">

#             <datalist id="{datalist_id}">
#                 {options_html}
#             </datalist>

#             <table class="paired-table" style="width: 100%; text-align: left;">
#                 <thead>
#                     <tr>
#                         <th style="width: 70%">{self.label_text}</th>  <th style="width: 20%">Magnitude (1-3)</th>
#                         <th style="width: 10%">Action</th>
#                     </tr>
#                 </thead>
#                 <tbody id="tbody_{main_id}">
#                     </tbody>
#             </table>

#             <div style="margin-top: 10px;">
#                 <button type="button" id="btn_add_{main_id}" class="button" style="font-weight: bold;">+ Add Row</button>
#             </div>

#             <input type="hidden" name="{name}" id="{main_id}" value="{current_types}">
#         </div>

#         <script>
#         (function($) {{
#             $(document).ready(function() {{
#                 var wrapper = $('#wrapper_{main_id}');
#                 var typesInput = $('#{main_id}');
#                 var magsInput = $('#{mag_id}');
#                 var tbody = $('#tbody_{main_id}');
#                 var addBtn = $('#btn_add_{main_id}');

#                 magsInput.closest('.form-row').hide();
#                 if(magsInput.closest('.form-row').length === 0) {{
#                     magsInput.attr('type', 'hidden');
#                     $('label[for="{mag_id}"]').hide();
#                 }}

#                 function addRow(typeVal, magVal) {{
#                     typeVal = typeVal || '';
#                     magVal = magVal || '1';
#                     var rowId = 'row_' + Math.random().toString(36).substr(2, 9);

#                     // UPDATED: Input now includes list="{datalist_id}" attribute
#                     var html = `
#                         <tr id="${{rowId}}">
#                             <td>
#                                 <input type="text" list="{datalist_id}" class="vTextField sync-input"
#                                        value="${{typeVal.replace(/"/g, '&quot;')}}"
#                                        style="width: 95%;" placeholder="Select or Type...">
#                             </td>
#                             <td>
#                                 <select class="sync-select" style="width: 100%;">
#                                     <option value="1" ${{magVal == '1' ? 'selected' : ''}}>1</option>
#                                     <option value="2" ${{magVal == '2' ? 'selected' : ''}}>2</option>
#                                     <option value="3" ${{magVal == '3' ? 'selected' : ''}}>3</option>
#                                 </select>
#                             </td>
#                             <td>
#                                 <button type="button" class="remove-btn"
#                                         style="color: red; cursor: pointer; border: none; background: none; font-weight: bold;">
#                                     ✖
#                                 </button>
#                             </td>
#                         </tr>
#                     `;
#                     tbody.append(html);
#                 }}

#                 function updateHiddenInputs() {{
#                     var typeArr = [];
#                     var magArr = [];
#                     tbody.find('tr').each(function() {{
#                         var t = $(this).find('.sync-input').val();
#                         var m = $(this).find('.sync-select').val();
#                         if (t && t.trim() !== '') {{
#                             typeArr.push(t.replace(/;/g, ',').trim());
#                             magArr.push(m);
#                         }}
#                     }});
#                     typesInput.val(typeArr.join('; '));
#                     magsInput.val(magArr.join('; '));
#                 }}

#                 function init() {{
#                     var tRaw = typesInput.val() || '';
#                     var mRaw = magsInput.val() || '';
#                     var types = tRaw.split(';');
#                     var mags = mRaw.split(';');
#                     tbody.empty();
#                     for (var i = 0; i < types.length; i++) {{
#                         var t = types[i].trim();
#                         if (t) {{
#                             var m = (mags[i]) ? mags[i].trim() : '1';
#                             addRow(t, m);
#                         }}
#                     }}
#                 }}

#                 addBtn.on('click', function() {{ addRow('', '1'); }});
#                 tbody.on('click', '.remove-btn', function() {{
#                     $(this).closest('tr').remove();
#                     updateHiddenInputs();
#                 }});
#                 tbody.on('change keyup', '.sync-input, .sync-select', function() {{
#                     updateHiddenInputs();
#                 }});
#                 init();
#             }});
#         }})(django.jQuery);
#         </script>
#         """
#         return mark_safe(html)


class PairedSemicolonWidget(Widget):
    """
    A custom widget that renders a list of (Name + Magnitude) pairs.
    Now supports dynamic 'data_choices' (for the Name) AND 'magnitude_choices' (for the Score).
    """
    template_name = 'django/forms/widgets/textarea.html'

    def __init__(self, magnitude_field_name, label_text="Medication Type", data_choices=None, magnitude_choices=None, *args, **kwargs):
        self.magnitude_field_name = magnitude_field_name
        self.label_text = label_text
        self.data_choices = data_choices if data_choices is not None else []
        # Default to 1-3 if nothing is passed, but we will pass DB values later
        self.magnitude_choices = magnitude_choices if magnitude_choices is not None else [
            '1', '2', '3']
        super().__init__(*args, **kwargs)

    def render(self, name, value, attrs=None, renderer=None):
        main_id = attrs.get('id', name)
        mag_id = main_id.replace(name, self.magnitude_field_name)
        current_types = value if value is not None else ''

        datalist_id = f"list_{main_id}"

        # 1. Build DataList options (for the Name input)
        data_options_html = ""
        for item in self.data_choices:
            clean_item = str(item).replace('"', '&quot;')
            data_options_html += f'<option value="{clean_item}">'

        # 2. Build Magnitude Select Options (from DB values)
        mag_options_html = ""
        for score in self.magnitude_choices:
            s_clean = str(score).strip()
            mag_options_html += f'<option value="{s_clean}">{s_clean}</option>'

        html = f"""
        <div id="wrapper_{main_id}" class="paired-widget-wrapper"
             data-main-id="{main_id}" data-mag-id="{mag_id}"
             style="border: 1px solid #ccc; padding: 10px; border-radius: 4px; background: #f9f9f9;">

            <datalist id="{datalist_id}">
                {data_options_html}
            </datalist>

            <table class="paired-table" style="width: 100%; text-align: left;">
                <thead>
                    <tr>
                        <th style="width: 70%">{self.label_text}</th>  <th style="width: 20%">Magnitude</th>
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
        (function($) {{
            $(document).ready(function() {{
                var wrapper = $('#wrapper_{main_id}');
                var typesInput = $('#{main_id}');
                var magsInput = $('#{mag_id}');
                var tbody = $('#tbody_{main_id}');
                var addBtn = $('#btn_add_{main_id}');

                // Store our dynamic options in a JS variable
                var magOptionsHTML = `{mag_options_html}`;

                magsInput.closest('.form-row').hide();
                if(magsInput.closest('.form-row').length === 0) {{
                    magsInput.attr('type', 'hidden');
                    $('label[for="{mag_id}"]').hide();
                }}

                function addRow(typeVal, magVal) {{
                    typeVal = typeVal || '';
                    magVal = magVal ? magVal.trim() : ''; // Don't default to '1' yet, let logic handle it later

                    var rowId = 'row_' + Math.random().toString(36).substr(2, 9);

                    var html = `
                        <tr id="${{rowId}}">
                            <td>
                                <input type="text" list="{datalist_id}" class="vTextField sync-input"
                                       value="${{typeVal.replace(/"/g, '&quot;')}}"
                                       style="width: 95%;" placeholder="Select or Type...">
                            </td>
                            <td>
                                <select class="sync-select" style="width: 100%;">
                                    ${{magOptionsHTML}}
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

                    var $row = $(html);
                    tbody.append($row);

                    // If we have a value (from DB), select it.
                    // If it's a new row (empty magVal), select the first option by default.
                    if (magVal) {{
                        $row.find('.sync-select').val(magVal);
                    }} else {{
                         $row.find('.sync-select option:first').prop('selected', true);
                    }}
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
                            var m = (mags[i]) ? mags[i].trim() : '';
                            addRow(t, m);
                        }}
                    }}
                }}

                addBtn.on('click', function() {{ addRow('', ''); }});
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


@admin.register(Analysis)
class AnalysisAdmin(admin.ModelAdmin):
    form = AnalysisAdminForm

    # --- ADDED SEARCH FIELDS ---
    search_fields = ('blood_test', 'blood_test_full',
                     'blood_test_acronym', 'panel', 'units', 'units_interchangeable', 'severity', 'vital_marker')
    # --- LIST DISPLAY UPDATED WITH CLICK WRAPPERS ---
    list_display = (
        'panel', 'blood_test', 'blood_test_full', 'blood_test_acronym',
        'units', 'units_interchangeable', 'ideal_low', 'ideal_high',
        'absence_low', 'absence_high', 'severity', 'vital_marker',

        # Updated fields using the _click wrappers
        'tcm_diag_low', 'tcm_diag_high',
        'func_diag_low_click', 'func_diag_high_click',
        'conv_diag_low_click', 'conv_diag_high_click',


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
        ('Functional Panels', {
            'fields': ('func_panel_1', 'func_panel_2', 'func_panel_3')
        }),
        ('Units', {
            'fields': ('units', 'units_interchangeable')
        }),
    )
    list_filter = ('panel', 'blood_test', 'severity', 'units',
                   'units_interchangeable', 'severity', 'vital_marker')
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


# class SemicolonListWidget(Widget):
#     """
#     A custom widget that renders a list of text items.
#     User adds rows, system saves as 'Item A; Item B; Item C'.
#     """
#     template_name = 'django/forms/widgets/textarea.html'

#     def render(self, name, value, attrs=None, renderer=None):
#         main_id = attrs.get('id', name)
#         current_val = value if value is not None else ''

#         html = f"""
#         <div id="wrapper_{main_id}" style="border: 1px solid #ccc; padding: 10px; border-radius: 4px; background: #f9f9f9;">
#             <table style="width: 100%; text-align: left;">
#                 <thead>
#                     <tr>
#                         <th style="width: 90%">Symptom / Item</th>
#                         <th style="width: 10%">Action</th>
#                     </tr>
#                 </thead>
#                 <tbody id="tbody_{main_id}">
#                 </tbody>
#             </table>

#             <div style="margin-top: 10px;">
#                 <button type="button" id="btn_add_{main_id}" class="button" style="font-weight: bold;">+ Add Item</button>
#             </div>

#             <input type="hidden" name="{name}" id="{main_id}" value="{current_val}">
#         </div>

#         <script>
#         (function($) {{
#             $(document).ready(function() {{
#                 var input = $('#{main_id}');
#                 var tbody = $('#tbody_{main_id}');
#                 var addBtn = $('#btn_add_{main_id}');

#                 function addRow(val) {{
#                     val = val || '';
#                     var rowId = 'row_' + Math.random().toString(36).substr(2, 9);

#                     var html = `
#                         <tr id="${{rowId}}">
#                             <td>
#                                 <input type="text" class="vTextField sync-input"
#                                        value="${{val.replace(/"/g, '&quot;')}}"
#                                        style="width: 98%;" placeholder="e.g. Headache">
#                             </td>
#                             <td>
#                                 <button type="button" class="remove-btn"
#                                         style="color: red; cursor: pointer; border: none; background: none; font-weight: bold;">
#                                     ✖
#                                 </button>
#                             </td>
#                         </tr>
#                     `;
#                     tbody.append(html);
#                 }}

#                 function updateHiddenInput() {{
#                     var arr = [];
#                     tbody.find('.sync-input').each(function() {{
#                         var t = $(this).val();
#                         if (t && t.trim() !== '') {{
#                             // Replace semicolons to prevent corruption, then trim
#                             arr.push(t.replace(/;/g, ',').trim());
#                         }}
#                     }});
#                     input.val(arr.join(';'));
#                 }}

#                 // Init
#                 var raw = input.val() || '';
#                 if(raw) {{
#                     var items = raw.split(';');
#                     items.forEach(function(item) {{
#                         if(item.trim()) addRow(item.trim());
#                     }});
#                 }}

#                 // Events
#                 addBtn.on('click', function() {{ addRow(''); }});

#                 tbody.on('click', '.remove-btn', function() {{
#                     $(this).closest('tr').remove();
#                     updateHiddenInput();
#                 }});

#                 tbody.on('change keyup', '.sync-input', function() {{
#                     updateHiddenInput();
#                 }});
#             }});
#         }})(django.jQuery);
#         </script>
#         """
#         return mark_safe(html)

class StrictSemicolonListWidget(Widget):
    """
    A custom widget that renders a list of Dropdowns (Select only).
    User CANNOT type new text; they must choose from the provided 'data_choices'.
    """
    template_name = 'django/forms/widgets/textarea.html'

    def __init__(self, data_choices=None, *args, **kwargs):
        # Store the list of valid symptoms
        self.data_choices = data_choices if data_choices is not None else []
        super().__init__(*args, **kwargs)

    def render(self, name, value, attrs=None, renderer=None):
        main_id = attrs.get('id', name)
        current_val = value if value is not None else ''

        # 1. Build the <option> HTML string just once
        options_html = '<option value="">-- Select Symptom --</option>'
        for item in self.data_choices:
            # Escape quotes just in case
            safe_item = str(item).replace('"', '&quot;')
            options_html += f'<option value="{safe_item}">{safe_item}</option>'

        # We hide the options_html inside a script tag or variable to inject it into JS easily
        # Note: We use replacing of {val} in JS logic below.

        html = f"""
        <div id="wrapper_{main_id}" style="border: 1px solid #ccc; padding: 10px; border-radius: 4px; background: #f9f9f9;">
            
            <table style="width: 100%; text-align: left;">
                <thead>
                    <tr>
                        <th style="width: 90%">Symptom (Select Only)</th>
                        <th style="width: 10%">Action</th>
                    </tr>
                </thead>
                <tbody id="tbody_{main_id}">
                </tbody>
            </table>
            
            <div style="margin-top: 10px;">
                <button type="button" id="btn_add_{main_id}" class="button" style="font-weight: bold;">+ Add Symptom</button>
            </div>
            
            <input type="hidden" name="{name}" id="{main_id}" value="{current_val}">
        </div>

        <script>
        (function($) {{
            $(document).ready(function() {{
                var input = $('#{main_id}');
                var tbody = $('#tbody_{main_id}');
                var addBtn = $('#btn_add_{main_id}');
                
                // Store options in a JS variable to reuse in every row
                var allOptions = `{options_html}`;

                function addRow(selectedValue) {{
                    selectedValue = selectedValue || '';
                    var rowId = 'row_' + Math.random().toString(36).substr(2, 9);
                    
                    // Create the Select element
                    // We must manually set the 'selected' attribute after creating the HTML
                    var html = `
                        <tr id="${{rowId}}">
                            <td>
                                <select class="sync-select" style="width: 98%; padding: 5px;">
                                    ${{allOptions}}
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
                    
                    var newRow = $(html);
                    tbody.append(newRow);

                    // Set the selected value if one was passed (e.g., loading from DB)
                    if (selectedValue) {{
                        newRow.find('select').val(selectedValue);
                    }}
                }}

                function updateHiddenInput() {{
                    var arr = [];
                    tbody.find('.sync-select').each(function() {{
                        var t = $(this).val();
                        if (t && t.trim() !== '') {{
                            arr.push(t);
                        }}
                    }});
                    // Save as "Symptom A; Symptom B"
                    input.val(arr.join('; '));
                }}

                // 1. Initial Load: Parse the existing DB string
                var raw = input.val() || '';
                if(raw) {{
                    // Split by semicolon (handling both "; " and ";")
                    var items = raw.split(';');
                    items.forEach(function(item) {{
                        if(item.trim()) addRow(item.trim());
                    }});
                }}

                // 2. Button Events
                addBtn.on('click', function() {{ addRow(''); }});
                
                tbody.on('click', '.remove-btn', function() {{
                    $(this).closest('tr').remove();
                    updateHiddenInput();
                }});

                // 3. Update hidden input whenever a dropdown changes
                tbody.on('change', '.sync-select', function() {{
                    updateHiddenInput();
                }});
            }});
        }})(django.jQuery);
        </script>
        """
        return mark_safe(html)


# class PatternAdminForm(forms.ModelForm):
#     # 1. Body Types (Primary, Secondary, Tertiary)
#     body_type_primary = forms.ChoiceField(
#         required=False, label="TCM Body Type - Primary", widget=forms.Select(attrs=WIDGET_ATTRS))
#     body_type_secondary = forms.ChoiceField(
#         required=False, label="TCM Body Type - Secondary", widget=forms.Select(attrs=WIDGET_ATTRS))
#     body_type_tertiary = forms.ChoiceField(
#         required=False, label="TCM Body Type - Tertiary", widget=forms.Select(attrs=WIDGET_ATTRS))

#     # 2. Pathogen
#     pathogenic_factor = forms.ChoiceField(
#         required=False, label="Pathogenic Factor", widget=forms.Select(attrs=WIDGET_ATTRS))

#     # 3. Excess/Deficiency/General (Fixed Choices)
#     excess_deficiency = forms.ChoiceField(
#         choices=[
#             ('', 'Select Type...'),
#             ('Excess', 'Excess'),
#             ('Deficiency', 'Deficiency'),
#             ('General', 'General')
#         ],
#         required=False,
#         label="Excess/Deficiency/General",
#         widget=forms.Select(attrs=WIDGET_ATTRS)
#     )

#     class Meta:
#         model = Pattern
#         fields = '__all__'
#         # 4. Apply the Semicolon Widget to Symptoms
#         widgets = {
#             'symptoms': SemicolonListWidget(),
#         }

#     @property
#     def media(self): return forms.Media(**SHARED_MEDIA)

#     def __init__(self, *args, **kwargs):
#         super(PatternAdminForm, self).__init__(*args, **kwargs)

#         # Load Body Types from DB
#         body_types = list(TCMBodyTypeMapping.objects.values_list(
#             'tcm_body_type', flat=True).distinct())

#         # Load Pathogens
#         pathogens = list(TCMPathogenDefinition.objects.values_list(
#             'pathogen', flat=True).distinct())

#         # Create Standard Choices List
#         bt_choices = [('', 'Select Body Type...')] + [(b, b)
#                                                       for b in body_types if b]
#         p_choices = [('', 'Select Pathogen...')] + [(p, p)
#                                                     for p in pathogens if p]

#         # Apply Choices to Fields
#         self.fields['body_type_primary'].choices = bt_choices
#         self.fields['body_type_secondary'].choices = bt_choices
#         self.fields['body_type_tertiary'].choices = bt_choices

#         self.fields['pathogenic_factor'].choices = p_choices


class PatternAdminForm(forms.ModelForm):
    # (Keep your existing ChoiceFields for body types/pathogens here...)
    # 1. Body Types
    body_type_primary = forms.ChoiceField(
        required=False, label="TCM Body Type - Primary", widget=forms.Select(attrs=WIDGET_ATTRS))
    body_type_secondary = forms.ChoiceField(
        required=False, label="TCM Body Type - Secondary", widget=forms.Select(attrs=WIDGET_ATTRS))
    body_type_tertiary = forms.ChoiceField(
        required=False, label="TCM Body Type - Tertiary", widget=forms.Select(attrs=WIDGET_ATTRS))

    # 2. Pathogen
    pathogenic_factor = forms.ChoiceField(
        required=False, label="Pathogenic Factor", widget=forms.Select(attrs=WIDGET_ATTRS))

    # 3. Excess/Deficiency
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
        widgets = {
            # Attach the new Strict Widget
            'symptoms': StrictSemicolonListWidget(),
        }

    @property
    def media(self): return forms.Media(**SHARED_MEDIA)

    def __init__(self, *args, **kwargs):
        super(PatternAdminForm, self).__init__(*args, **kwargs)

        # --- A. POPULATE SYMPTOMS (Strict List) ---
        # 1. Fetch symptoms from SymptomCategory (only valid source)
        symptom_pool = list(SymptomCategory.objects.exclude(symptoms__isnull=True)
                            .exclude(symptoms__exact='')
                            .values_list('symptoms', flat=True)
                            .distinct()
                            .order_by('symptoms'))

        # 2. Pass choices to the widget
        if 'symptoms' in self.fields:
            self.fields['symptoms'].widget.data_choices = symptom_pool

        # --- B. EXISTING LOGIC (Body Types, Pathogens, Middle/Bottom Groups) ---
        # (Keep the rest of your logic exactly as it was)

        body_types = list(TCMBodyTypeMapping.objects.values_list(
            'tcm_body_type', flat=True).distinct())
        pathogens = list(TCMPathogenDefinition.objects.values_list(
            'pathogen', flat=True).distinct())

        bt_choices = [('', 'Select Body Type...')] + [(b, b)
                                                      for b in body_types if b]
        p_choices = [('', 'Select Pathogen...')] + [(p, p)
                                                    for p in pathogens if p]

        self.fields['body_type_primary'].choices = bt_choices
        self.fields['body_type_secondary'].choices = bt_choices
        self.fields['body_type_tertiary'].choices = bt_choices
        self.fields['pathogenic_factor'].choices = p_choices

        # --- Middle vs Bottom Groups Logic ---
        middle_group = ['middle_primary', 'middle_secondary',
                        'middle_tertiary', 'middle_quantery']
        bottom_group = ['bottom_primary', 'bottom_secondary']

        def get_pooled_choices(column_names):
            pool = set()
            for col in column_names:
                values = Pattern.objects.values_list(col, flat=True).distinct()
                for val in values:
                    if val:
                        pool.add(val)
            return [('', '')] + [(v, v) for v in sorted(list(pool))]

        middle_choices = get_pooled_choices(middle_group)
        bottom_choices = get_pooled_choices(bottom_group)

        for f_name in middle_group:
            if f_name in self.fields:
                self.fields[f_name].widget = forms.Select(
                    choices=middle_choices,
                    attrs={'class': 'advanced-select', 'style': 'width: 100%',
                           'data-tags': 'true', 'data-placeholder': 'Select Middle Category...'}
                )

        for f_name in bottom_group:
            if f_name in self.fields:
                self.fields[f_name].widget = forms.Select(
                    choices=bottom_choices,
                    attrs={'class': 'advanced-select', 'style': 'width: 100%',
                           'data-tags': 'true', 'data-placeholder': 'Select Bottom Category...'}
                )

        # Safety Check for existing values
        instance = getattr(self, 'instance', None)
        if instance and instance.pk:
            all_target_fields = middle_group + bottom_group
            for f_name in all_target_fields:
                val = getattr(instance, f_name, None)
                if val:
                    existing_keys = [
                        k for k, v in self.fields[f_name].widget.choices]
                    if val not in existing_keys:
                        self.fields[f_name].widget.choices.append((val, val))


@admin.register(Pattern)
class PatternAdmin(admin.ModelAdmin):
    # --- 2. CONNECT THE FORM ---
    form = PatternAdminForm

    search_fields = ('tcm_patterns', 'modern_description',
                     'middle_primary', 'pathogenic_factor', 'symptoms')

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

        'pathogenic_factor',
    )

    list_filter = ('tcm_patterns', 'modern_description', 'excess_deficiency',
                   'middle_primary', 'pathogenic_factor')

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

    # def positive_impacts_click(self, obj):
    #     return self._create_click_to_open(obj.positive_impacts)
    # positive_impacts_click.short_description = "Positive Impacts"

    # def negative_impacts_click(self, obj):
    #     return self._create_click_to_open(obj.negative_impacts)
    # negative_impacts_click.short_description = "Negative Impacts"

    # def rationale_click(self, obj):
    #     return self._create_click_to_open(obj.rationale)
    # rationale_click.short_description = "Rationale"
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
    primary_category = DynamicMultipleChoiceField(
        required=False,
        widget=forms.SelectMultiple(
            attrs={'class': 'advanced-select', 'style': 'width: 100%', 'data-tags': 'true'})
    )
    secondary_category = DynamicMultipleChoiceField(
        required=False,
        widget=forms.SelectMultiple(
            attrs={'class': 'advanced-select', 'style': 'width: 100%', 'data-tags': 'true'})
    )

    class Meta:
        model = FunctionalCategory
        fields = '__all__'

    @property
    def media(self):
        return forms.Media(**SHARED_MEDIA)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # --- SEPARATE LOGIC: Fetch ONLY from FunctionalCategory Table ---
        unique_items = set()

        # 1. Get raw strings
        raw_p = FunctionalCategory.objects.values_list(
            'primary_category', flat=True)
        raw_s = FunctionalCategory.objects.values_list(
            'secondary_category', flat=True)

        # 2. Parse strings into tags
        for val in list(raw_p) + list(raw_s):
            if val:
                unique_items.update(get_initial_oxford_list(val))

        # 3. Create Choices
        choices = sorted([(i, i) for i in unique_items if i])

        self.fields['primary_category'].choices = choices
        self.fields['secondary_category'].choices = choices

        # 4. Set Initial Values
        instance = getattr(self, 'instance', None)
        if instance and instance.pk:
            self.initial['primary_category'] = get_initial_oxford_list(
                instance.primary_category, self.fields['primary_category'].choices
            )
            self.initial['secondary_category'] = get_initial_oxford_list(
                instance.secondary_category, self.fields['secondary_category'].choices
            )

    def clean_primary_category(self):
        return list_to_oxford_string(self.cleaned_data['primary_category'])

    def clean_secondary_category(self):
        return list_to_oxford_string(self.cleaned_data['secondary_category'])


# class FunctionalCategoryAdminForm(forms.ModelForm):
#     class Meta:
#         model = FunctionalCategory
#         fields = '__all__'
#         # Add help text so you know the format is being applied
#         help_texts = {
#             'primary_category': 'Enter items separated by commas (e.g., "Sleep, Stress"). System will auto-format to "Sleep and Stress".',
#             'secondary_category': 'Enter items separated by commas. System will auto-format to "A, B and C".',
#         }

#     def clean_primary_category(self):
#         # Auto-format the input before saving to DB
#         return format_list_string(self.cleaned_data['primary_category'])

#     def clean_secondary_category(self):
#         # Auto-format the input before saving to DB
#         return format_list_string(self.cleaned_data['secondary_category'])


@admin.register(FunctionalCategory)
class FunctionalCategoryAdmin(admin.ModelAdmin):
    form = FunctionalCategoryAdminForm  # <--- Connect the custom form here

    # --- ADDED SEARCH FIELDS ---
    search_fields = ('functional_medicine',
                     'primary_category', 'secondary_category')
    list_filter = ('functional_medicine',
                   'primary_category', 'secondary_category')
    list_filter

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
    search_fields = ('symptoms', 'primary_category', 'secondary_category')

    # --- EXISTING STRUCTURE PRESERVED ---
    list_display = ('symptoms', 'primary_category', 'secondary_category')
    list_filter = ('symptoms', 'primary_category', 'secondary_category')

# ==============================================================================
# 4. MEDICAL CONDITIONS (Search: Name | Select: Pattern, Category)
# ==============================================================================


# class MedicalConditionAdminForm(forms.ModelForm):
#     # 1. Searchable Multi-Select for Patterns
#     tcm_patterns = forms.MultipleChoiceField(
#         required=False,
#         label="TCM Patterns",
#         widget=forms.SelectMultiple(attrs=WIDGET_ATTRS)
#     )

#     # # 2. Searchable Single-Selects for ALL Category Levels
#     # primary_category = forms.ChoiceField(
#     #     required=False,
#     #     label="Primary Category",
#     #     widget=forms.Select(attrs=WIDGET_ATTRS)
#     # )
#     # secondary_category = forms.ChoiceField(
#     #     required=False,
#     #     label="Secondary Category",
#     #     widget=forms.Select(attrs=WIDGET_ATTRS)
#     # )
#     # tertiary_category = forms.ChoiceField(
#     #     required=False,
#     #     label="Tertiary Category",
#     #     widget=forms.Select(attrs=WIDGET_ATTRS)
#     # )

#     class Meta:
#         model = MedicalCondition
#         fields = '__all__'

#     @property
#     def media(self): return forms.Media(**SHARED_MEDIA)

#     def __init__(self, *args, **kwargs):
#         super().__init__(*args, **kwargs)

#         # --- LOGIC TO FIX "MISSING CATEGORIES" & PREVENT CRASH ---

#         # A. Fetch the Master List
#         master_cats = set(FunctionalCategory.objects.values_list(
#             'functional_medicine', flat=True))

#         # B. Fetch currently used categories (including those NOT in master list)
#         used_p = set(MedicalCondition.objects.values_list(
#             'primary_category', flat=True))
#         used_s = set(MedicalCondition.objects.values_list(
#             'secondary_category', flat=True))
#         used_t = set(MedicalCondition.objects.values_list(
#             'tertiary_category', flat=True))

#         # C. Combine all sets
#         combined_set = master_cats | used_p | used_s | used_t

#         # D. Filter out None/Empty values BEFORE sorting
#         # This fixes the "TypeError: '<' not supported between instances of 'NoneType' and 'str'"
#         all_possible_cats = sorted([cat for cat in combined_set if cat])

#         # E. Create Choices
#         cat_choices = [('', 'Select Category...')] + [(c, c)
#                                                       for c in all_possible_cats]

#         # F. Assign to fields
#         self.fields['primary_category'].choices = cat_choices
#         self.fields['secondary_category'].choices = cat_choices
#         self.fields['tertiary_category'].choices = cat_choices

#         # --- PATTERN LOGIC ---
#         patterns = list(Pattern.objects.values_list(
#             'tcm_patterns', flat=True).distinct().order_by('tcm_patterns'))
#         # Filter out empty patterns to be safe
#         self.fields['tcm_patterns'].choices = [(p, p) for p in patterns if p]

#         # Initial Value for Patterns
#         instance = getattr(self, 'instance', None)
#         if instance and instance.pk:
#             p_flat = [p for p in patterns if p]
#             self.initial['tcm_patterns'] = get_initial_list(
#                 instance.tcm_patterns, p_flat)

#     def clean_tcm_patterns(self):
#         return list_to_semicolon_string(self.cleaned_data['tcm_patterns'])


class MedicalConditionAdminForm(forms.ModelForm):
    # Standard Pattern Field (Existing)
    tcm_patterns = forms.MultipleChoiceField(
        required=False,
        label="TCM Patterns",
        widget=forms.SelectMultiple(attrs=WIDGET_ATTRS)
    )

    # Categories (New Logic)
    primary_category = DynamicMultipleChoiceField(
        required=False,
        label="Primary Category",
        widget=forms.SelectMultiple(
            attrs={'class': 'advanced-select', 'style': 'width: 100%', 'data-tags': 'true'})
    )
    secondary_category = DynamicMultipleChoiceField(
        required=False,
        label="Secondary Category",
        widget=forms.SelectMultiple(
            attrs={'class': 'advanced-select', 'style': 'width: 100%', 'data-tags': 'true'})
    )
    tertiary_category = DynamicMultipleChoiceField(
        required=False,
        label="Tertiary Category",
        widget=forms.SelectMultiple(
            attrs={'class': 'advanced-select', 'style': 'width: 100%', 'data-tags': 'true'})
    )

    class Meta:
        model = MedicalCondition
        fields = '__all__'

    @property
    def media(self):
        return forms.Media(**SHARED_MEDIA)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # --- SEPARATE LOGIC: Fetch ONLY from MedicalCondition Table ---
        unique_items = set()

        # 1. Get raw strings
        raw_p = MedicalCondition.objects.values_list(
            'primary_category', flat=True)
        raw_s = MedicalCondition.objects.values_list(
            'secondary_category', flat=True)
        raw_t = MedicalCondition.objects.values_list(
            'tertiary_category', flat=True)

        # 2. Parse strings into tags
        #    Combining all 3 columns into one list so any tag used anywhere is available
        all_raw = list(raw_p) + list(raw_s) + list(raw_t)
        for val in all_raw:
            if val:
                unique_items.update(get_initial_oxford_list(val))

        # 3. Create Choices
        choices = sorted([(i, i) for i in unique_items if i])

        self.fields['primary_category'].choices = choices
        self.fields['secondary_category'].choices = choices
        self.fields['tertiary_category'].choices = choices

        # --- PATTERN CHOICES (Existing) ---
        patterns = list(Pattern.objects.values_list(
            'tcm_patterns', flat=True).distinct().order_by('tcm_patterns'))
        self.fields['tcm_patterns'].choices = [(p, p) for p in patterns if p]

        # --- INITIAL VALUES ---
        instance = getattr(self, 'instance', None)
        if instance and instance.pk:
            # Patterns
            p_flat = [p for p in patterns if p]
            self.initial['tcm_patterns'] = get_initial_list(
                instance.tcm_patterns, p_flat)

            # Categories
            self.initial['primary_category'] = get_initial_oxford_list(
                instance.primary_category, self.fields['primary_category'].choices)

            self.initial['secondary_category'] = get_initial_oxford_list(
                instance.secondary_category, self.fields['secondary_category'].choices)

            self.initial['tertiary_category'] = get_initial_oxford_list(
                instance.tertiary_category, self.fields['tertiary_category'].choices)

    # --- SAVE LOGIC ---
    def clean_tcm_patterns(self):
        return list_to_semicolon_string(self.cleaned_data['tcm_patterns'])

    def clean_primary_category(self):
        return list_to_oxford_string(self.cleaned_data['primary_category'])

    def clean_secondary_category(self):
        return list_to_oxford_string(self.cleaned_data['secondary_category'])

    def clean_tertiary_category(self):
        return list_to_oxford_string(self.cleaned_data['tertiary_category'])


@admin.register(MedicalCondition)
class MedicalConditionAdmin(admin.ModelAdmin):
    form = MedicalConditionAdminForm

    # --- ADDED SEARCH FIELDS ---
    search_fields = (
        'condition', 'tcm_patterns', 'rationale',
        'primary_category', 'secondary_category', 'tertiary_category'
    )

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
    list_filter = ('condition', 'primary_category', )
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
    list_filter = ('term',)
    list_display_links = ('term',)
    list_per_page = 50


class WBCMatrixAdminForm(forms.ModelForm):
    # Use ChoiceFields for the Interpretation Hierarchy so they select from WBCGlossary
    primary_int = forms.ChoiceField(
        required=False, label="Primary Interpretation", widget=forms.Select(attrs=WIDGET_ATTRS))
    secondary = forms.ChoiceField(
        required=False, label="Secondary", widget=forms.Select(attrs=WIDGET_ATTRS))
    tertiary = forms.ChoiceField(
        required=False, label="Tertiary", widget=forms.Select(attrs=WIDGET_ATTRS))
    quaternary = forms.ChoiceField(
        required=False, label="Quaternary", widget=forms.Select(attrs=WIDGET_ATTRS))
    quinary = forms.ChoiceField(
        required=False, label="Quinary", widget=forms.Select(attrs=WIDGET_ATTRS))

    class Meta:
        model = WBCMatrix
        fields = '__all__'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # 1. Fetch Terms from WBCGlossary
        terms = list(WBCGlossary.objects.values_list(
            'term', flat=True).distinct().order_by('term'))

        # 2. Create Choices List
        term_choices = [('', 'Select Term...')] + [(t, t) for t in terms if t]

        # 3. Assign choices to the fields
        self.fields['primary_int'].choices = term_choices
        self.fields['secondary'].choices = term_choices
        self.fields['tertiary'].choices = term_choices
        self.fields['quaternary'].choices = term_choices
        self.fields['quinary'].choices = term_choices

        # 4. Set Initial Values (if editing an existing record)
        instance = getattr(self, 'instance', None)
        if instance and instance.pk:
            current_values = [
                instance.primary_int, instance.secondary, instance.tertiary,
                instance.quaternary, instance.quinary
            ]
            for val in current_values:
                if val and val not in terms:
                    term_choices.append((val, val))

            self.fields['primary_int'].choices = term_choices
            self.fields['secondary'].choices = term_choices
            self.fields['tertiary'].choices = term_choices
            self.fields['quaternary'].choices = term_choices
            self.fields['quinary'].choices = term_choices


# # --- 1. DEFINE THE CUSTOM FORM ---
# class WBCMatrixAdminForm(forms.ModelForm):
#     # Override risk_score to be a dropdown (1-5)
#     risk_score = forms.ChoiceField(
#         choices=[(None, 'Select Score')] + [(i, str(i)) for i in range(1, 6)],
#         required=False,
#         label="Risk Score",
#         # Matches your other widgets
#         widget=forms.Select(attrs={'style': 'width: 100%'})
#     )

#     class Meta:
#         model = WBCMatrix
#         fields = '__all__'


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
        'risk_definition_click',
        'other_considerations',
        'rationale_click',
        'clinical_guidance_click'
    )

    list_display_links = ('wbc', 'neutrophils', 'lymphocytes',
                          'monocytes', 'eosinophils', 'basophils')

    # --- 1. DISABLE ADD PERMISSION ---
    def has_add_permission(self, request):
        return False

    # --- 2. MAKE FIELDS READ-ONLY ---
    readonly_fields = (
        'wbc', 'neutrophils', 'lymphocytes', 'monocytes', 'eosinophils', 'basophils',
        'risk_score', 'risk_level', 'confidence'
    )

    # --- FIELDSETS ---
    fieldsets = (
        ('Marker Patterns (Read Only)', {
            'description': "These patterns identify the row and cannot be changed.",
            'fields': (
                ('wbc', 'neutrophils'),
                ('lymphocytes', 'monocytes'),
                ('eosinophils', 'basophils')
            )
        }),
        ('Interpretation Hierarchy', {
            'description': "Select terms from the WBC Glossary.",
            'fields': (
                'primary_int',
                ('secondary', 'tertiary'),
                ('quaternary', 'quinary')
            ),
            'classes': ('wide',)
        }),
        ('Risk & Analysis', {
            'fields': (
                ('risk_score', 'risk_level'),  # Now Read-only
                'confidence',                 # Now Read-only
                'risk_definition',
                'other_considerations',
                'rationale',
                'clinical_guidance'
            )
        }),
    )

    list_filter = ('risk_level', 'confidence', 'wbc')
    list_per_page = 50

    # --- CLICK TO OPEN HELPERS ---
    def _create_click_to_open(self, text, width="300px"):
        if not text:
            return "-"

        style_str = f"min-width: {width}; white-space: normal;"

        if len(text) <= 50:
            return format_html(f'<div style="{style_str}">{text}</div>')

        short_text = text[:50] + "..."

        return format_html(
            f'<div class="text-toggle-container" style="{style_str}">'
            '<div style="cursor:pointer; display:block;" '
            'onclick="this.style.display=\'none\'; this.nextElementSibling.style.display=\'block\';">'
            '<span>{}</span> <span style="color:#447e9b; font-weight:bold;"> &#9662;</span></div>'
            '<div style="cursor:pointer; display:none;" '
            'onclick="this.style.display=\'none\'; this.previousElementSibling.style.display=\'block\';">'
            '<span>{}</span> <span style="color:#447e9b; font-weight:bold;"> &#9652;</span></div>'
            '</div>',
            short_text, text
        )

    def rationale_click(self, obj):
        return self._create_click_to_open(obj.rationale, width="200px")
    rationale_click.short_description = "Rationale"

    def clinical_guidance_click(self, obj):
        return self._create_click_to_open(obj.clinical_guidance, width="200px")
    clinical_guidance_click.short_description = "Clinical Guidance"

    def risk_definition_click(self, obj):
        return self._create_click_to_open(obj.risk_definition, width="200px")
    risk_definition_click.short_description = "Risk Definition"

    # --- UPDATED CSS FOR COMPACT UI ---
    class Media:
        css = {
            'all': ('admin/css/admin_enhanced.css',)
        }
        # Generalized CSS to fix ALL rows (WBC, Risk Score, Confidence, etc.)
        extra = '''
            <style>
                /* 1. Reset the Row Layout */
                /* Force items to align to the left */
                .form-group .row {
                    display: flex !important;
                    justify-content: flex-start !important;
                }

                /* 2. Shrink Labels (e.g. "WBC", "Risk Score") */
                /* Override the theme's 'col-sm-3' which forces 25% width */
                .form-group .row label.col-sm-3 {
                    flex: 0 0 auto !important;
                    width: auto !important;
                    max-width: none !important;
                    margin-right: 10px !important;  /* Tiny gap between Label and Value */
                    padding-right: 0 !important;
                }

                /* 3. Shrink Value Wrappers (e.g. "High", "5") */
                .form-group .row .fieldBox {
                    flex: 0 0 auto !important;
                    width: auto !important;
                    padding-left: 0 !important;
                    margin-right: 50px !important; /* Gap before the NEXT label starts */
                }

                /* 4. Fix alignment for the second label in the row (e.g. "Neutrophils") */
                .form-group .row label.col-auto {
                    padding-left: 0 !important;
                    margin-right: 10px !important;
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


# class MedicationMappingAdminForm(MappingAdminFormBase):
#     class Meta:
#         model = MedicationMapping
#         fields = '__all__'
#         widgets = {
#             'magnitude_low': forms.HiddenInput(),
#             'magnitude_high': forms.HiddenInput(),
#         }

#     def __init__(self, *args, **kwargs):
#         super().__init__(*args, **kwargs)

#         # 1. Fetch sub-categories from MedicationList
#         med_choices = list(MedicationList.objects.exclude(sub_category__isnull=True)
#                            .values_list('sub_category', flat=True)
#                            .distinct().order_by('sub_category'))

#         # 2. Dynamically assign widgets with choices
#         self.fields['med_types_low'].widget = PairedSemicolonWidget(
#             magnitude_field_name='magnitude_low',
#             label_text="Medication Type",
#             choices=med_choices
#         )
#         self.fields['med_types_high'].widget = PairedSemicolonWidget(
#             magnitude_field_name='magnitude_high',
#             label_text="Medication Type",
#             choices=med_choices
#         )


# class MedicationMappingAdminForm(MappingAdminFormBase):
#     class Meta:
#         model = MedicationMapping
#         fields = '__all__'
#         widgets = {
#             # Attach the custom widget to the "Types" fields.
#             # We tell it which field name holds the magnitude numbers.
#             'med_types_low': PairedSemicolonWidget(magnitude_field_name='magnitude_low'),
#             'med_types_high': PairedSemicolonWidget(magnitude_field_name='magnitude_high'),

#             # We hide the actual magnitude inputs because the widget above controls them
#             'magnitude_low': forms.HiddenInput(),
#             'magnitude_high': forms.HiddenInput(),
#         }

#     def __init__(self, *args, **kwargs):
#         super().__init__(*args, **kwargs)

#         # --- NEW: Fetch Medication Sub-Categories for the Dropdown ---
#         # Get unique sub_categories, excluding blanks
#         med_choices = list(MedicationList.objects
#                            .exclude(sub_category__isnull=True)
#                            .exclude(sub_category__exact='')
#                            .values_list('sub_category', flat=True)
#                            .distinct()
#                            .order_by('sub_category'))

#         # --- Pass choices to the widget instance ---
#         if 'med_types_low' in self.fields:
#             self.fields['med_types_low'].widget.choices = med_choices

#         if 'med_types_high' in self.fields:
#             self.fields['med_types_high'].widget.choices = med_choices


class MedicationMappingAdminForm(MappingAdminFormBase):
    class Meta:
        model = MedicationMapping
        fields = '__all__'
        widgets = {
            # Attach the custom widget. Note: data_choices isn't passed here, but in __init__
            'med_types_low': PairedSemicolonWidget(magnitude_field_name='magnitude_low'),
            'med_types_high': PairedSemicolonWidget(magnitude_field_name='magnitude_high'),

            'magnitude_low': forms.HiddenInput(),
            'magnitude_high': forms.HiddenInput(),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # --- 1. DYNAMIC SCORES (The new logic) ---
        # Fetch raw strings from DB (e.g., "1 = Minor", "2 = Moderate")
        raw_scores = list(
            MedicationScoreDef.objects.values_list('score', flat=True))

        # Parse and Extract "Only the First Number"
        cleaned_scores = set()
        for s in raw_scores:
            if s:
                # Split by '=' and take the first part ("1 = Minor" -> "1")
                clean_val = str(s).split('=')[0].strip()

                # Verify it is a digit
                if clean_val.isdigit():
                    cleaned_scores.add(int(clean_val))

        # Sort numerically (1, 2, 3...) and convert back to string
        sorted_scores = [str(i) for i in sorted(list(cleaned_scores))]

        # Fallback if DB is empty
        if not sorted_scores:
            sorted_scores = ['1', '2', '3']

        # Pass the cleaned numbers to the widgets
        if 'med_types_low' in self.fields:
            self.fields['med_types_low'].widget.magnitude_choices = sorted_scores
        if 'med_types_high' in self.fields:
            self.fields['med_types_high'].widget.magnitude_choices = sorted_scores

        # --- 2. MEDICATION NAMES (Existing logic) ---
        # Fetch distinct Sub-Categories from MedicationList for the text dropdown
        sub_categories = list(MedicationList.objects
                              .exclude(sub_category__isnull=True)
                              .exclude(sub_category__exact='')
                              .values_list('sub_category', flat=True)
                              .distinct()
                              .order_by('sub_category'))

        if 'med_types_low' in self.fields:
            self.fields['med_types_low'].widget.data_choices = sub_categories

        if 'med_types_high' in self.fields:
            self.fields['med_types_high'].widget.data_choices = sub_categories


@admin.register(MedicationList)
class MedicationListAdmin(admin.ModelAdmin):
    # --- ADDED SEARCH FIELDS ---
    search_fields = ('category', 'sub_category', 'example_medications',
                     'tcm_narrative_no_effect')

    # --- EXISTING STRUCTURE PRESERVED ---
    list_display = ('category', 'sub_category', 'example_medications',
                    'do_not_effect', 'tcm_narrative_no_effect')
    fields = ('category', 'sub_category', 'example_medications',
              'do_not_effect', 'tcm_narrative_no_effect')
    list_display_links = ('category', 'sub_category')
    list_filter = ('category', 'sub_category',)
    list_per_page = 50


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
    list_filter = ('panel', 'marker',)
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


# @admin.register(MedicationScoreDef)
# class MedicationScoreDefAdmin(admin.ModelAdmin):
#     list_display = ('score', 'definition')

@admin.register(MedicationScoreDef)
class MedicationScoreDefAdmin(admin.ModelAdmin):
    form = ScoreDefAdminForm
    # Display the score text and definition in the list
    list_display = ('score', 'definition')
    # Allow clicking the score text to edit
    list_display_links = ('score',)
    # Search by the text inside the score (e.g. search "Minor")
    search_fields = ('score', 'definition')
    ordering = ('score',)


@admin.register(SupplementScoreDef)
class SupplementScoreDefAdmin(admin.ModelAdmin):
    form = ScoreDefAdminForm
    list_display = ('score', 'definition')
    list_display_links = ('score',)
    search_fields = ('score', 'definition')
    ordering = ('score',)


@admin.register(SupplementList)
class SupplementsListAdmin(admin.ModelAdmin):
    # --- ADDED SEARCH FIELDS ---
    search_fields = ('category', 'sub_category',
                     'example_supplements', 'normal_narrative', 'tcm_narrative')

    # --- EXISTING STRUCTURE PRESERVED ---
    list_display = ('category', 'sub_category',
                    'example_supplements', 'normal_narrative', 'tcm_narrative')
    fields = ('category', 'sub_category', 'example_supplements',
              'normal_narrative', 'tcm_narrative')
    list_display_links = ('category', 'sub_category')
    list_filter = ('category', 'sub_category',)
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

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # ========================================================
        # 1. FETCH SUPPLEMENT TYPES (Sub-Categories)
        # ========================================================
        # Query SupplementList for unique 'sub_category' values
        supp_choices = list(SupplementList.objects
                            .exclude(sub_category__isnull=True)
                            .exclude(sub_category__exact='')
                            .values_list('sub_category', flat=True)
                            .distinct()
                            .order_by('sub_category'))

        # Pass these choices to the custom widgets
        if 'supp_types_low' in self.fields:
            self.fields['supp_types_low'].widget.data_choices = supp_choices

        if 'supp_types_high' in self.fields:
            self.fields['supp_types_high'].widget.data_choices = supp_choices

        # ========================================================
        # 2. DYNAMIC SCORES (Existing Logic)
        # ========================================================
        # Fetch raw strings from DB (e.g., "1 = Minor / Minor", "2 = Moderate")
        raw_scores = list(
            SupplementScoreDef.objects.values_list('score', flat=True))

        # Parse and Extract "Only the First Number"
        cleaned_scores = set()
        for s in raw_scores:
            if s:
                # Logic: Split by '=' and take the first part, then strip spaces
                clean_val = str(s).split('=')[0].strip()

                # Verify it is a digit before adding (safety check)
                if clean_val.isdigit():
                    cleaned_scores.add(int(clean_val))

        # Sort numerically (1, 2, 3...)
        sorted_scores = [str(i) for i in sorted(list(cleaned_scores))]

        # Fallback if DB is empty
        if not sorted_scores:
            sorted_scores = ['1', '2', '3']

        # Pass the cleaned numbers to the widget
        if 'supp_types_low' in self.fields:
            self.fields['supp_types_low'].widget.magnitude_choices = sorted_scores
        if 'supp_types_high' in self.fields:
            self.fields['supp_types_high'].widget.magnitude_choices = sorted_scores

# class SupplementMappingAdminForm(MappingAdminFormBase):
#     class Meta:
#         model = SupplementMapping
#         fields = '__all__'
#         widgets = {
#             # Pass label_text="Supplement Type" here
#             'supp_types_low': PairedSemicolonWidget(
#                 magnitude_field_name='magnitude_low',
#                 label_text="Supplement Type"
#             ),

#             # Pass label_text="Supplement Type" here
#             'supp_types_high': PairedSemicolonWidget(
#                 magnitude_field_name='magnitude_high',
#                 label_text="Supplement Type"
#             ),

#             'magnitude_low': forms.HiddenInput(),
#             'magnitude_high': forms.HiddenInput(),
#         }

#     def __init__(self, *args, **kwargs):
#         super().__init__(*args, **kwargs)

#         # 1. Fetch raw strings from DB (e.g., "1 = Minor / Minor", "2 = Moderate")
#         raw_scores = list(
#             SupplementScoreDef.objects.values_list('score', flat=True))

#         # 2. Parse and Extract "Only the First Number"
#         cleaned_scores = set()
#         for s in raw_scores:
#             if s:
#                 # Logic: Split by '=' and take the first part, then strip spaces
#                 # Example: "1 = Minor" -> "1 " -> "1"
#                 # Example: "4" -> "4"
#                 clean_val = str(s).split('=')[0].strip()

#                 # Verify it is a digit before adding (safety check)
#                 if clean_val.isdigit():
#                     cleaned_scores.add(int(clean_val))

#         # 3. Sort numerically (1, 2, 3, 4, 10...)
#         sorted_scores = [str(i) for i in sorted(list(cleaned_scores))]

#         # Fallback if DB is empty
#         if not sorted_scores:
#             sorted_scores = ['1', '2', '3']

#         # 4. Pass the cleaned numbers to the widget
#         if 'supp_types_low' in self.fields:
#             self.fields['supp_types_low'].widget.magnitude_choices = sorted_scores
#         if 'supp_types_high' in self.fields:
#             self.fields['supp_types_high'].widget.magnitude_choices = sorted_scores


@admin.register(SupplementMapping)
class SupplementsMappingAdmin(admin.ModelAdmin):
    form = SupplementMappingAdminForm

    # --- ADDED SEARCH FIELDS ---
    search_fields = ('panel', 'marker', 'supp_types_low', 'magnitude_low', 'supp_types_high',
                     'magnitude_high', 'narrative_low', 'narrative_high', 'tcm_narrative_low',
                     'tcm_narrative_high', 'mechanism_low', 'mechanism_high', 'interp_note_low', 'interp_note_high')

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
    list_filter = ('panel', 'marker')
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


# @admin.register(SupplementScoreDef)
# class SupplementScoreDefAdmin(admin.ModelAdmin):
#     list_display = ('score', 'definition')


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
    search_fields = ('tcm_body_type', 'tcm_explanation',
                     'func_equivalent', 'func_explanation')
    list_filter = ('tcm_body_type',)

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
    list_filter = ('pathogen',)

    # --- EXISTING STRUCTURE PRESERVED ---
    list_display = ('pathogen', 'definition')
