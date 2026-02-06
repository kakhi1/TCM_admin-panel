
from django.contrib import messages
from django.http import HttpResponse
from django.utils.html import escape
from django.utils.html import escape  # Import this
from .models import Pattern
from django.utils.html import format_html
from django.forms.widgets import Widget
from django.utils.safestring import mark_safe
import json
from django.urls import reverse
from django.contrib import admin, messages
from django import forms
from .models import (
    # Import the Proxies
    BloodMarkersProxy, PatternProxy, TCMBodyTypeProxy, TCMPathogenProxy, FunctionalCategoryProxy,
    SymptomCategoryProxy, MedicalConditionProxy,
    MedicationListProxy, MedicationMappingProxy, MedicationScoreDefProxy,
    SupplementListProxy, SupplementMappingProxy, SupplementScoreDefProxy,
    WBCGlossaryProxy, WBCMatrixProxy,
    LifestyleQuestionnaireProxy,
    Analysis, Pattern, FunctionalCategory, SymptomCategory,
    MedicalCondition, WBCGlossary, WBCMatrix, MedicationList,
    MedicationMapping, MedicationScoreDef, SupplementList,
    SupplementMapping, SupplementScoreDef, LifestyleQuestionnaire,
    TCMBodyTypeMapping, TCMPathogenDefinition
)
from .models import AIAgentConfigProxy, AIAgentLogProxy

# --- GLOBAL CONFIGURATION & ASSETS ---
# # Common media config to ensure Select2 loads for all search-enabled forms
# SHARED_MEDIA = {
#     'css': {
#         'all': (
#             'https://cdnjs.cloudflare.com/ajax/libs/select2/4.0.13/css/select2.min.css',
#             'admin/css/admin_enhanced.css',
#         )
#     },
#     'js': (
#         'https://code.jquery.com/jquery-3.6.0.min.js',
#         'https://cdnjs.cloudflare.com/ajax/libs/select2/4.0.13/js/select2.full.min.js',
#         'admin/js/admin_select2_setup.js',

#     )
# }
SHARED_MEDIA = {
    'css': {
        'all': (
            'https://cdnjs.cloudflare.com/ajax/libs/select2/4.0.13/css/select2.min.css',
            'admin/css/admin_enhanced.css',
        )
    },
    'js': (
        # 1. LOAD JQUERY FIRST (Critical)
        'https://code.jquery.com/jquery-3.6.0.min.js',

        # 2. LOAD SELECT2 (Depends on jQuery)
        'https://cdnjs.cloudflare.com/ajax/libs/select2/4.0.13/js/select2.full.min.js',

        # 3. YOUR SETUP SCRIPT (Must run last)
        'admin/js/admin_select2_setup.js',

        # 4. Unsaved Changes Warning
        'admin/js/unsaved_changes.js',
    )
}

WIDGET_ATTRS = {
    'class': 'advanced-select',
    'style': 'width: 100%'
}

# --- HELPER FUNCTIONS FOR TEXT-BASED RELATIONS ---
# --- NEW HELPER FUNCTIONS & CUSTOM FIELD ---
# --- ADD THIS CLASS NEXT TO DynamicMultipleChoiceField ---


class DynamicChoiceField(forms.ChoiceField):
    """
    Allows valid choices OR new custom text values.
    Renders as a Select, but validates like a CharField.
    """

    def validate(self, value):
        # Skip the standard ChoiceField validation that forces value to be in self.choices
        if self.required and not value:
            raise forms.ValidationError(
                self.error_messages['required'], code='required')


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
    # --- ADD THIS PROPERTY ---

    @property
    def media(self):
        return forms.Media(**SHARED_MEDIA)


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


# class PairedSemicolonWidget(Widget):
#     """
#     A custom widget that renders a list of (Name + Magnitude) pairs.
#     Now supports dynamic 'data_choices' (for the Name) AND 'magnitude_choices' (for the Score).
#     """
#     template_name = 'django/forms/widgets/textarea.html'

#     def __init__(self, magnitude_field_name, label_text="Medication Type", data_choices=None, magnitude_choices=None, *args, **kwargs):
#         self.magnitude_field_name = magnitude_field_name
#         self.label_text = label_text
#         self.data_choices = data_choices if data_choices is not None else []
#         # Default to 1-3 if nothing is passed, but we will pass DB values later
#         self.magnitude_choices = magnitude_choices if magnitude_choices is not None else [
#             '1', '2', '3']
#         super().__init__(*args, **kwargs)

#     def render(self, name, value, attrs=None, renderer=None):
#         main_id = attrs.get('id', name)
#         mag_id = main_id.replace(name, self.magnitude_field_name)
#         current_types = value if value is not None else ''

#         datalist_id = f"list_{main_id}"

#         # 1. Build DataList options (for the Name input)
#         data_options_html = ""
#         for item in self.data_choices:
#             clean_item = str(item).replace('"', '&quot;')
#             data_options_html += f'<option value="{clean_item}">'

#         # 2. Build Magnitude Select Options (from DB values)
#         mag_options_html = ""
#         for score in self.magnitude_choices:
#             s_clean = str(score).strip()
#             mag_options_html += f'<option value="{s_clean}">{s_clean}</option>'

#         html = f"""
#         <div id="wrapper_{main_id}" class="paired-widget-wrapper"
#              data-main-id="{main_id}" data-mag-id="{mag_id}"
#              style="border: 1px solid #ccc; padding: 10px; border-radius: 4px; background: #f9f9f9;">

#             <datalist id="{datalist_id}">
#                 {data_options_html}
#             </datalist>

#             <table class="paired-table" style="width: 100%; text-align: left;">
#                 <thead>
#                     <tr>
#                         <th style="width: 70%">{self.label_text}</th>  <th style="width: 20%">Magnitude</th>
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

#                 // Store our dynamic options in a JS variable
#                 var magOptionsHTML = `{mag_options_html}`;

#                 magsInput.closest('.form-row').hide();
#                 if(magsInput.closest('.form-row').length === 0) {{
#                     magsInput.attr('type', 'hidden');
#                     $('label[for="{mag_id}"]').hide();
#                 }}

#                 function addRow(typeVal, magVal) {{
#                     typeVal = typeVal || '';
#                     magVal = magVal ? magVal.trim() : ''; // Don't default to '1' yet, let logic handle it later

#                     var rowId = 'row_' + Math.random().toString(36).substr(2, 9);

#                     var html = `
#                         <tr id="${{rowId}}">
#                             <td>
#                                 <input type="text" list="{datalist_id}" class="vTextField sync-input"
#                                        value="${{typeVal.replace(/"/g, '&quot;')}}"
#                                        style="width: 95%;" placeholder="Select or Type...">
#                             </td>
#                             <td>
#                                 <select class="sync-select" style="width: 100%;">
#                                     ${{magOptionsHTML}}
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

#                     var $row = $(html);
#                     tbody.append($row);

#                     // If we have a value (from DB), select it.
#                     // If it's a new row (empty magVal), select the first option by default.
#                     if (magVal) {{
#                         $row.find('.sync-select').val(magVal);
#                     }} else {{
#                          $row.find('.sync-select option:first').prop('selected', true);
#                     }}
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
#                             var m = (mags[i]) ? mags[i].trim() : '';
#                             addRow(t, m);
#                         }}
#                     }}
#                 }}

#                 addBtn.on('click', function() {{ addRow('', ''); }});
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
    FIXED: Robust JS loading to prevent "Add Row" button failure.
    """
    template_name = 'django/forms/widgets/textarea.html'

    def __init__(self, magnitude_field_name, label_text="Medication Type", data_choices=None, magnitude_choices=None, *args, **kwargs):
        self.magnitude_field_name = magnitude_field_name
        self.label_text = label_text
        self.data_choices = data_choices if data_choices is not None else []
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

        # 3. Create a SAFE JavaScript string for the options (avoids line break errors)
        safe_mag_options = mag_options_html.replace(
            '\n', '').replace('"', '\\"')

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
        (function() {{
            // Safe jQuery loader: Try django.jQuery, fall back to standard jQuery
            var $ = (typeof django !== 'undefined' && django.jQuery) ? django.jQuery : window.jQuery;
            
            if (!$) {{
                console.error("PairedSemicolonWidget: jQuery not found!");
                return;
            }}

            $(document).ready(function() {{
                try {{
                    var wrapper = $('#wrapper_{main_id}');
                    var typesInput = $('#{main_id}');
                    var magsInput = $('#{mag_id}');
                    var tbody = $('#tbody_{main_id}');
                    var addBtn = $('#btn_add_{main_id}');

                    // Use the pre-calculated safe string
                    var magOptionsHTML = "{safe_mag_options}";

                    // Hide the separate Magnitude field (since we sync to it)
                    magsInput.closest('.form-row').hide();
                    // Fallback for different admin themes
                    if(magsInput.closest('.form-row').length === 0) {{
                        magsInput.attr('type', 'hidden');
                        $('label[for="{mag_id}"]').hide();
                    }}

                    function addRow(typeVal, magVal) {{
                        typeVal = typeVal || '';
                        magVal = magVal ? magVal.trim() : ''; 

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
                                            style="color: red; cursor: pointer; border: none; background: none; font-weight: bold; font-size: 16px;">
                                        ✖
                                    </button>
                                </td>
                            </tr>
                        `;
                        
                        var $row = $(html);
                        tbody.append($row);

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

                    // --- Event Binding ---
                    addBtn.on('click', function(e) {{ 
                        e.preventDefault();
                        console.log("Add Row Clicked"); // Debug check
                        addRow('', ''); 
                    }});
                    
                    tbody.on('click', '.remove-btn', function() {{
                        $(this).closest('tr').remove();
                        updateHiddenInputs();
                    }});
                    
                    tbody.on('change keyup', '.sync-input, .sync-select', function() {{
                        updateHiddenInputs();
                    }});
                    
                    init();
                    
                }} catch (err) {{
                    console.error("PairedSemicolonWidget Error:", err);
                }}
            }});
        }})();
        </script>
        """
        return mark_safe(html)


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


# class RemindUpdateMixin:
#     """
#     SMART VALIDATION MIXIN:
#     1. Checks if specific fields contain values NOT present in the target tables.
#     2. If missing values are found, pauses save and shows "Verification Required".
#     3. If values exist, saves immediately.
#     """
#     # Structure: [ (['field_names'], 'TargetModel', 'target_field', 'url_name', 'Link Text', 'Message') ]
#     validation_map = []

#     def save_model(self, request, obj, form, change):
#         active_validations = []
#         triggered = False

#         if not self.validation_map:
#             super().save_model(request, obj, form, change)
#             return

#         for entry in self.validation_map:
#             # Unpack the rule. Support both old (4 arg) and new (6 arg) formats if necessary,
#             # but here we use the new 6-arg format for smart checking.
#             # Format: fields, model_class, lookup_field, url_name, link_text, msg
#             if len(entry) == 6:
#                 fields, target_model, lookup_field, url_name, display_name, message = entry

#                 for field in fields:
#                     value = form.cleaned_data.get(field)
#                     if value:
#                         # 1. Parse the values (handle lists or semicolon strings)
#                         if isinstance(value, list):
#                             items = value
#                         else:
#                             # Split by semicolon or comma to get individual tags
#                             items = [x.strip() for x in str(value).replace(
#                                 ';', ',').split(',') if x.strip()]

#                         # 2. Check database for missing items
#                         # Get all existing values from the target model
#                         existing_values = set(
#                             target_model.objects.values_list(lookup_field, flat=True))

#                         # Find items that are NOT in the database
#                         missing = [
#                             item for item in items if item not in existing_values]

#                         if missing:
#                             triggered = True
#                             # Add specific details to the message
#                             detailed_msg = f"{message}<br><strong>New/Missing Items:</strong> {', '.join(missing)}"

#                             try:
#                                 url = reverse(url_name)
#                                 active_validations.append({
#                                     'url': url,
#                                     'name': display_name,
#                                     'message': mark_safe(detailed_msg)
#                                 })
#                             except Exception:
#                                 pass
#                             # Break loop for this group (don't add same error twice)
#                             break
#             else:
#                 # Fallback for old simple logic (just checks if not empty)
#                 # You can remove this else block if you update all mappings
#                 pass

#         if not triggered:
#             # precise save
#             super().save_model(request, obj, form, change)
#         else:
#             # Flag request to be intercepted in response_add/change
#             request._needs_interception = True
#             request._active_validations = active_validations

#     # --- CRITICAL ADDITION: INTERCEPT RESPONSES ---
#     def response_add(self, request, obj, post_url_continue=None):
#         if getattr(request, '_needs_interception', False):
#             return self._build_interception_page(request)
#         return super().response_add(request, obj, post_url_continue)

#     def response_change(self, request, obj):
#         if getattr(request, '_needs_interception', False):
#             return self._build_interception_page(request)
#         return super().response_change(request, obj)

#     def _build_interception_page(self, request):
#         active_validations = getattr(request, '_active_validations', [])

#         validation_html = ""
#         for item in active_validations:
#             validation_html += f"""
#             <div class="validation-item">
#                 <div class="validation-msg">{item['message']}</div>
#                 <a href="{item['url']}" target="_blank" class="link-btn">
#                     🔗 Go to {item['name']}
#                 </a>
#             </div>
#             """

#         html = f"""
#         <!DOCTYPE html>
#         <html>
#         <head>
#             <title>Verification Required</title>
#             <style>
#                 body {{ font-family: -apple-system, system-ui, sans-serif; background: #f4f6f9; display: flex; justify-content: center; align-items: center; height: 100vh; margin: 0; }}
#                 .card {{ background: white; padding: 40px; border-radius: 8px; box-shadow: 0 10px 25px rgba(0,0,0,0.1); max-width: 600px; width: 100%; border-top: 6px solid #dc3545; }}
#                 h2 {{ color: #dc3545; margin-top: 0; }}
#                 .validation-item {{ background: #fff5f5; border: 1px solid #f5c6cb; border-radius: 6px; padding: 15px; margin-bottom: 15px; text-align: left; }}
#                 .validation-msg {{ color: #721c24; font-weight: 600; margin-bottom: 10px; }}
#                 .link-btn {{ display: inline-block; padding: 6px 12px; background: #fff; color: #dc3545; text-decoration: none; border: 1px solid #dc3545; border-radius: 4px; font-size: 13px; font-weight: bold; }}
#                 .link-btn:hover {{ background: #dc3545; color: white; }}
#                 .back-btn {{ width: 100%; padding: 15px; background: #6c757d; color: white; border: none; border-radius: 6px; font-size: 16px; font-weight: bold; cursor: pointer; margin-top: 20px; }}
#                 .back-btn:hover {{ background: #5a6268; }}
#             </style>
#         </head>
#         <body>
#             <div class="card">
#                 <h2>⚠️ Verification Required</h2>
#                 <p>You entered data that does not exist in the linked tables yet.</p>
#                 {validation_html}
#                 <button class="back-btn" onclick="window.history.back();">⬅ Go Back & Fix</button>
#                 <div style="margin-top: 15px; font-size: 12px; color: #999;">
#                     Note: The Blood Marker was NOT saved. Create the missing items in the linked tables first, then come back and Save.
#                 </div>
#             </div>
#         </body>
#         </html>
#         """
#         return HttpResponse(html)


# class RemindUpdateMixin:
#     """
#     SMART VALIDATION MIXIN (Universal):
#     1. Standard Check: Checks if value exists in target table.
#     2. Split Check: If a delimiter (e.g. ';') is provided, splits DB text before checking.
#     """
#     # Structure: [ (['fields'], TargetModel, 'lookup_field', 'url', 'Page Name', 'Message', 'OPTIONAL_DELIMITER') ]
#     validation_map = []

#     def save_model(self, request, obj, form, change):
#         active_validations = []
#         triggered = False

#         if not self.validation_map:
#             super().save_model(request, obj, form, change)
#             return

#         for entry in self.validation_map:
#             # Initialize defaults
#             target_delimiter = None

#             # 1. HANDLE NEW FORMAT (7 items - with delimiter)
#             if len(entry) == 7:
#                 fields, target_model, lookup_field, url_name, display_name, message, target_delimiter = entry

#             # 2. HANDLE OLD FORMAT (6 items - Standard) - SAFE FALLBACK
#             elif len(entry) == 6:
#                 fields, target_model, lookup_field, url_name, display_name, message = entry

#             # Skip invalid configurations
#             else:
#                 continue

#             for field in fields:
#                 value = form.cleaned_data.get(field)
#                 if value:
#                     # A. Parse the Form Input (what user typed)
#                     if isinstance(value, list):
#                         items = value
#                     else:
#                         # Split form input by semicolon or comma (Standardize input)
#                         items = [x.strip() for x in str(value).replace(
#                             ';', ',').split(',') if x.strip()]

#                     # B. Fetch Database Values
#                     raw_db_values = target_model.objects.values_list(
#                         lookup_field, flat=True)

#                     # C. Build Allowed List
#                     existing_values = set()

#                     if target_delimiter:
#                         # --- SPECIAL LOGIC: Split DB values (e.g. for Symptoms) ---
#                         for db_val in raw_db_values:
#                             if db_val:
#                                 parts = [x.strip() for x in str(db_val).split(
#                                     target_delimiter) if x.strip()]
#                                 existing_values.update(parts)
#                     else:
#                         # --- STANDARD LOGIC: Exact match (for everyone else) ---
#                         existing_values = set(raw_db_values)

#                     # D. Compare
#                     missing = [
#                         item for item in items if item not in existing_values]

#                     if missing:
#                         triggered = True
#                         detailed_msg = f"{message}<br><strong>New/Missing Items:</strong> {', '.join(missing)}"
#                         try:
#                             url = reverse(url_name)
#                             active_validations.append({
#                                 'url': url,
#                                 'name': display_name,
#                                 'message': mark_safe(detailed_msg)
#                             })
#                         except Exception:
#                             pass
#                         break

#         if not triggered:
#             super().save_model(request, obj, form, change)
#         else:
#             # Pause save and trigger interception page
#             request._needs_interception = True
#             request._active_validations = active_validations

#     def response_add(self, request, obj, post_url_continue=None):
#         if getattr(request, '_needs_interception', False):
#             return self._build_interception_page(request)
#         return super().response_add(request, obj, post_url_continue)

#     def response_change(self, request, obj):
#         if getattr(request, '_needs_interception', False):
#             return self._build_interception_page(request)
#         return super().response_change(request, obj)

#     def _build_interception_page(self, request):
#         active_validations = getattr(request, '_active_validations', [])
#         validation_html = ""
#         for item in active_validations:
#             validation_html += f"""
#             <div class="validation-item">
#                 <div class="validation-msg">{item['message']}</div>
#                 <a href="{item['url']}" target="_blank" class="link-btn">
#                     🔗 Go to {item['name']}
#                 </a>
#             </div>
#             """
#         html = f"""
#         <!DOCTYPE html>
#         <html>
#         <head>
#             <title>Verification Required</title>
#             <style>
#                 body {{ font-family: -apple-system, system-ui, sans-serif; background: #f4f6f9; display: flex; justify-content: center; align-items: center; height: 100vh; margin: 0; }}
#                 .card {{ background: white; padding: 40px; border-radius: 8px; box-shadow: 0 10px 25px rgba(0,0,0,0.1); max-width: 600px; width: 100%; border-top: 6px solid #dc3545; }}
#                 h2 {{ color: #dc3545; margin-top: 0; }}
#                 .validation-item {{ background: #fff5f5; border: 1px solid #f5c6cb; border-radius: 6px; padding: 15px; margin-bottom: 15px; text-align: left; }}
#                 .validation-msg {{ color: #721c24; font-weight: 600; margin-bottom: 10px; }}
#                 .link-btn {{ display: inline-block; padding: 6px 12px; background: #fff; color: #dc3545; text-decoration: none; border: 1px solid #dc3545; border-radius: 4px; font-size: 13px; font-weight: bold; }}
#                 .link-btn:hover {{ background: #dc3545; color: white; }}
#                 .back-btn {{ width: 100%; padding: 15px; background: #6c757d; color: white; border: none; border-radius: 6px; font-size: 16px; font-weight: bold; cursor: pointer; margin-top: 20px; }}
#                 .back-btn:hover {{ background: #5a6268; }}
#             </style>
#         </head>
#         <body>
#             <div class="card">
#                 <h2>⚠️ Verification Required</h2>
#                 <p>You entered data that does not exist in the linked tables yet.</p>
#                 {validation_html}
#                 <button class="back-btn" onclick="window.history.back();">⬅ Go Back & Fix</button>
#             </div>
#         </body>
#         </html>
#         """
#         return HttpResponse(html)


# class RemindUpdateMixin:
#     """
#     SMART VALIDATION MIXIN:
#     1. Universal Case: Shows a top banner reminder (warning) after Add/Edit/Delete.
#     2. Strict Case: Pauses save for a custom verification page if specific items are missing.
#     """
#     universal_reminders = []
#     validation_map = []

#     def show_universal_reminder(self, request):
#         # Debug
#         print(
#             f"DEBUG: show_universal_reminder triggered for {self.__class__.__name__}")
#         for url_name, display_name in self.universal_reminders:
#             try:
#                 url = reverse(url_name)
#                 print(f"DEBUG: Reverse URL found: {url}")  # Debug
#                 msg = format_html(
#                     "A record has been Added/Deleted/Edited. "
#                     "Please update the <strong><a href='{}' target='_blank'>{}</a></strong> "
#                     "to reflect these changes into the system.",
#                     url, display_name
#                 )
#                 messages.warning(request, msg)
#                 # Debug
#                 print("DEBUG: Message successfully added to Django Messages framework")
#             except Exception as e:
#                 # Debug
#                 print(
#                     f"DEBUG ERROR: Could not reverse URL {url_name}. Error: {e}")

#     def save_model(self, request, obj, form, change):
#         print(f"DEBUG: save_model called for {obj}")  # Debug

#         # 1. Trigger Universal Reminder (The Top Banner)
#         if self.universal_reminders:
#             self.show_universal_reminder(request)
#         else:
#             print("DEBUG: No universal_reminders defined for this class")  # Debug

#         # 2. YOUR EXISTING LOGIC (Preserved)
#         if not self.validation_map:
#             # Debug
#             print("DEBUG: No validation_map defined. Proceeding with standard save.")
#             super().save_model(request, obj, form, change)
#             return

#         # Debug
#         print(
#             f"DEBUG: validation_map found with {len(self.validation_map)} entries")
#         active_validations = []
#         triggered = False

#         for entry in self.validation_map:
#             target_delimiter = entry[6] if len(entry) == 7 else None
#             fields, target_model, lookup_field, url_name, display_name, message = entry[:6]

#             for field in fields:
#                 value = form.cleaned_data.get(field)
#                 if value:
#                     items = value if isinstance(value, list) else [x.strip() for x in str(
#                         value).replace(';', ',').split(',') if x.strip()]
#                     raw_db_values = target_model.objects.values_list(
#                         lookup_field, flat=True)
#                     existing_values = set()

#                     if target_delimiter:
#                         for db_val in raw_db_values:
#                             if db_val:
#                                 parts = [x.strip() for x in str(db_val).split(
#                                     target_delimiter) if x.strip()]
#                                 existing_values.update(parts)
#                     else:
#                         existing_values = set(raw_db_values)

#                     missing = [
#                         item for item in items if item not in existing_values]
#                     if missing:
#                         # Debug
#                         print(
#                             f"DEBUG: STRICT VALIDATION TRIGGERED. Missing items: {missing}")
#                         triggered = True
#                         detailed_msg = f"{message}<br><strong>New/Missing Items:</strong> {', '.join(missing)}"
#                         try:
#                             active_validations.append({
#                                 'url': reverse(url_name),
#                                 'name': display_name,
#                                 'message': mark_safe(detailed_msg)
#                             })
#                         except:
#                             pass
#                         break

#         if not triggered:
#             # Debug
#             print("DEBUG: No missing items found in strict validation. Saving model.")
#             super().save_model(request, obj, form, change)
#         else:
#             # Debug
#             print("DEBUG: Intercepting response to show Verification Required page.")
#             request._needs_interception = True
#             request._active_validations = active_validations

#     def delete_model(self, request, obj):
#         print(f"DEBUG: delete_model called for {obj}")  # Debug
#         if self.universal_reminders:
#             self.show_universal_reminder(request)
#         super().delete_model(request, obj)


class RemindUpdateMixin:
    """
    SMART VALIDATION MIXIN:
    1. Universal Case: Shows a top banner (Added/Updated/Deleted) after changes.
    2. Strict Case: Original logic for 'Verification Required' page remains untouched.
    """
    # For Universal Banner: [('url_name', 'Page Name')]
    universal_reminders = []

    # YOUR ORIGINAL LOGIC - DO NOT DELETE
    validation_map = []

    def _trigger_universal_banner(self, request, verb):
        """Helper to show the banner at the top of the table."""
        for url_name, display_name in self.universal_reminders:
            try:
                url = reverse(url_name)
                msg = format_html(
                    "A record has been <strong>{}</strong>. "
                    "Please update the <strong><a href='{}' target='_blank'>{}</a></strong> "
                    "to reflect these changes into the system.",
                    verb, url, display_name
                )
                messages.warning(request, msg)
            except Exception as e:
                # Debug print for terminal troubleshooting
                print(f"DEBUG ERROR: Could not reverse URL {url_name}: {e}")

    def save_model(self, request, obj, form, change):
        # 1. Trigger the Dynamic Universal Banner
        verb = "Updated" if change else "Added"
        if self.universal_reminders:
            self._trigger_universal_banner(request, verb)

        # 2. YOUR ORIGINAL STRICT VALIDATION LOGIC (Preserved Exactly)
        if not self.validation_map:
            super().save_model(request, obj, form, change)
            return

        active_validations = []
        triggered = False
        for entry in self.validation_map:
            # Supports both 6 and 7 item formats from original code
            target_delimiter = entry[6] if len(entry) == 7 else None
            fields, target_model, lookup_field, url_name, display_name, message = entry[:6]

            for field in fields:
                value = form.cleaned_data.get(field)
                if value:
                    # Parse input (handle lists or semicolon strings)
                    items = value if isinstance(value, list) else [x.strip() for x in str(
                        value).replace(';', ',').split(',') if x.strip()]
                    raw_db_values = target_model.objects.values_list(
                        lookup_field, flat=True)
                    existing_values = set()

                    if target_delimiter:
                        # Split DB values based on provided delimiter
                        for db_val in raw_db_values:
                            if db_val:
                                parts = [x.strip() for x in str(db_val).split(
                                    target_delimiter) if x.strip()]
                                existing_values.update(parts)
                    else:
                        existing_values = set(raw_db_values)

                    missing = [
                        item for item in items if item not in existing_values]
                    if missing:
                        triggered = True
                        detailed_msg = f"{message}<br><strong>New/Missing Items:</strong> {', '.join(missing)}"
                        try:
                            active_validations.append({
                                'url': reverse(url_name),
                                'name': display_name,
                                'message': mark_safe(detailed_msg)
                            })
                        except:
                            pass
                        break

        if not triggered:
            super().save_model(request, obj, form, change)
        else:
            # Pauses save and triggers your custom interception page
            request._needs_interception = True
            request._active_validations = active_validations

    def delete_model(self, request, obj):
        """Triggers the banner when a record is deleted."""
        if self.universal_reminders:
            self._trigger_universal_banner(request, "Deleted")
        super().delete_model(request, obj)

    # --- KEEP YOUR EXISTING RESPONSE INTERCEPTORS BELOW ---
    def response_add(self, request, obj, post_url_continue=None):
        if getattr(request, '_needs_interception', False):
            return self._build_interception_page(request)
        return super().response_add(request, obj, post_url_continue)

    def response_change(self, request, obj):
        if getattr(request, '_needs_interception', False):
            return self._build_interception_page(request)
        return super().response_change(request, obj)

    def response_delete(self, request, obj_display, obj_id):
        if getattr(request, '_needs_interception', False):
            return self._build_interception_page(request)
        return super().response_delete(request, obj_display, obj_id)

    def _build_interception_page(self, request):
        """Original custom HTML page logic for verification."""
        active_validations = getattr(request, '_active_validations', [])
        validation_html = ""
        for item in active_validations:
            validation_html += f"""
            <div class="validation-item">
                <div class="validation-msg">{item['message']}</div>
                <a href="{item['url']}" target="_blank" class="link-btn">
                    🔗 Go to {item['name']}
                </a>
            </div>
            """
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Verification Required</title>
            <style>
                body {{ font-family: -apple-system, system-ui, sans-serif; background: #f4f6f9; display: flex; justify-content: center; align-items: center; height: 100vh; margin: 0; }}
                .card {{ background: white; padding: 40px; border-radius: 8px; box-shadow: 0 10px 25px rgba(0,0,0,0.1); max-width: 600px; width: 100%; border-top: 6px solid #dc3545; }}
                h2 {{ color: #dc3545; margin-top: 0; }}
                .validation-item {{ background: #fff5f5; border: 1px solid #f5c6cb; border-radius: 6px; padding: 15px; margin-bottom: 15px; text-align: left; }}
                .validation-msg {{ color: #721c24; font-weight: 600; margin-bottom: 10px; }}
                .link-btn {{ display: inline-block; padding: 6px 12px; background: #fff; color: #dc3545; text-decoration: none; border: 1px solid #dc3545; border-radius: 4px; font-size: 13px; font-weight: bold; }}
                .link-btn:hover {{ background: #dc3545; color: white; }}
                .back-btn {{ width: 100%; padding: 15px; background: #6c757d; color: white; border: none; border-radius: 6px; font-size: 16px; font-weight: bold; cursor: pointer; margin-top: 20px; }}
                .back-btn:hover {{ background: #5a6268; }}
            </style>
        </head>
        <body>
            <div class="card">
                <h2>⚠️ Verification Required</h2>
                <p>You entered data that does not exist in the linked tables yet.</p>
                {validation_html}
                <button class="back-btn" onclick="window.history.back();">⬅ Go Back & Fix</button>
            </div>
        </body>
        </html>
        """
        return HttpResponse(html)
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
    # 1. TCM Diagnosis
    tcm_diag_low = DynamicMultipleChoiceField(
        required=False,
        label="TCM Diagnosis (Low)",
        widget=forms.SelectMultiple(attrs={
            'class': 'advanced-select',
            'style': 'width: 100%',
            'data-tags': 'true'  # <--- Allows typing new "Dummy" values
        })
    )
    tcm_diag_high = DynamicMultipleChoiceField(
        required=False,
        label="TCM Diagnosis (High)",
        widget=forms.SelectMultiple(attrs={
            'class': 'advanced-select',
            'style': 'width: 100%',
            'data-tags': 'true'
        })
    )

    # 2. Functional Med Diagnosis
    func_diag_low = DynamicMultipleChoiceField(
        required=False,
        label="Functional Med Diagnosis (Low)",
        widget=forms.SelectMultiple(attrs={
            'class': 'advanced-select',
            'style': 'width: 100%',
            'data-tags': 'true'
        })
    )
    func_diag_high = DynamicMultipleChoiceField(
        required=False,
        label="Functional Med Diagnosis (High)",
        widget=forms.SelectMultiple(attrs={
            'class': 'advanced-select',
            'style': 'width: 100%',
            'data-tags': 'true'
        })
    )

    # --- UPDATED: CharField + Select Widget + data-tags="true" ---
    # This combination allows selection from list OR typing a new value.
    func_panel_1 = forms.CharField(
        required=False,
        label="Functional Panel 1",
        widget=forms.Select(attrs={
            'class': 'advanced-select',
            'style': 'width: 100%',
            'data-tags': 'true'  # <--- Allows creation of new values
        })
    )
    func_panel_2 = forms.CharField(
        required=False,
        label="Functional Panel 2",
        widget=forms.Select(attrs={
            'class': 'advanced-select',
            'style': 'width: 100%',
            'data-tags': 'true'
        })
    )
    func_panel_3 = forms.CharField(
        required=False,
        label="Functional Panel 3",
        widget=forms.Select(attrs={
            'class': 'advanced-select',
            'style': 'width: 100%',
            'data-tags': 'true'
        })
    )

    class Meta:
        model = Analysis
        fields = '__all__'

    @property
    def media(self):
        return forms.Media(**SHARED_MEDIA)

    def __init__(self, *args, **kwargs):
        super(AnalysisAdminForm, self).__init__(*args, **kwargs)

        # 1. Fetch Source Data for Diagnoses
        patterns = list(Pattern.objects.values_list(
            'tcm_patterns', flat=True).distinct().order_by('tcm_patterns'))
        func_cats = list(FunctionalCategory.objects.values_list(
            'functional_medicine', flat=True).distinct().order_by('functional_medicine'))

        # 2. Populate Widget Choices for Diagnoses
        p_choices = [(p, p) for p in patterns if p]
        f_choices = [(f, f) for f in func_cats if f]

        self.fields['tcm_diag_low'].choices = p_choices
        self.fields['tcm_diag_high'].choices = p_choices
        self.fields['func_diag_low'].choices = f_choices
        self.fields['func_diag_high'].choices = f_choices

        # --- 3. UPDATED LOGIC: Populate Functional Panels ---
        # Fetch unique values from ALL three columns to build a master list
        p1 = list(Analysis.objects.values_list('func_panel_1', flat=True))
        p2 = list(Analysis.objects.values_list('func_panel_2', flat=True))
        p3 = list(Analysis.objects.values_list('func_panel_3', flat=True))

        # Combine and remove duplicates/empties
        all_panels = set(p1 + p2 + p3)
        panel_choices = [('', '')] + sorted([(p, p) for p in all_panels if p])

        # Assign choices to the WIDGET (since CharField doesn't have self.fields['x'].choices)
        self.fields['func_panel_1'].widget.choices = panel_choices
        self.fields['func_panel_2'].widget.choices = panel_choices
        self.fields['func_panel_3'].widget.choices = panel_choices

        # --- 4. Set Initial Values ---
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

            # Ensure the current value is in the choices list (otherwise it disappears)
            for field in ['func_panel_1', 'func_panel_2', 'func_panel_3']:
                val = getattr(instance, field)
                if val and val not in all_panels:
                    self.fields[field].widget.choices.append((val, val))

    # Save Logic: Convert List -> String
    def clean_tcm_diag_low(self): return list_to_semicolon_string(
        self.cleaned_data['tcm_diag_low'])

    def clean_tcm_diag_high(self): return list_to_semicolon_string(
        self.cleaned_data['tcm_diag_high'])

    def clean_func_diag_low(self): return list_to_semicolon_string(
        self.cleaned_data['func_diag_low'])
    def clean_func_diag_high(self): return list_to_semicolon_string(
        self.cleaned_data['func_diag_high'])
# --- MODAL VALIDATION MIXIN (CLIENT-SIDE) ---


# --- 1. CORE BLOOD MARKERS ---
@admin.register(BloodMarkersProxy)
class AnalysisAdmin(RemindUpdateMixin, admin.ModelAdmin):
    form = AnalysisAdminForm

    validation_map = [
        (
            ['tcm_diag_low', 'tcm_diag_high'],
            Pattern,             # Target Model
            'tcm_patterns',      # Column in Pattern model to check against
            'admin:ui_core_patternproxy_changelist',
            'TCM Patterns Page',
            "You referenced a TCM Pattern that does not exist."
        ),
        (
            ['func_diag_low', 'func_diag_high'],
            FunctionalCategory,  # Target Model
            'functional_medicine',  # Column to check
            'admin:ui_core_functionalcategoryproxy_changelist',
            'Functional Medicine Page',
            "You referenced a Functional Diagnosis that does not exist."
        ),
        # You can add the Medication/Supplement checks here too if needed,
        # but they are usually text fields in this form.
    ]
# --- DYNAMIC MAPPING CONFIGURATION ---
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
            # Moved 'severity' here
            'fields': ('panel', 'blood_test', 'blood_test_full', 'blood_test_acronym', 'vital_marker', 'severity')
        }),
        ('Units & Ranges', {  # Renamed from "Ranges & Severity"
            # Moved 'units' and 'units_interchangeable' here
            # Removed 'severity'
            'fields': (
                ('ideal_low', 'ideal_high'),
                ('absence_low', 'absence_high'),
                ('units', 'units_interchangeable')
            )
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
        # Removed the separate 'Units' fieldset as it is now merged above
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

    @property
    def media(self):
        return forms.Media(**SHARED_MEDIA)

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


class PatternAdminForm(forms.ModelForm):
    # 1. Body Types: Change to DynamicChoiceField
    body_type_primary = DynamicChoiceField(
        required=False, label="TCM Body Type - Primary", widget=forms.Select(attrs=WIDGET_ATTRS))
    body_type_secondary = DynamicChoiceField(
        required=False, label="TCM Body Type - Secondary", widget=forms.Select(attrs=WIDGET_ATTRS))
    body_type_tertiary = DynamicChoiceField(
        required=False, label="TCM Body Type - Tertiary", widget=forms.Select(attrs=WIDGET_ATTRS))

    # 2. Pathogen: Change to DynamicChoiceField
    pathogenic_factor = DynamicChoiceField(
        required=False, label="Pathogenic Factor", widget=forms.Select(attrs=WIDGET_ATTRS))

    # 3. Excess/Deficiency (Keep as strict ChoiceField, these are hardcoded)
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
            'symptoms': StrictSemicolonListWidget(),
        }

    @property
    def media(self): return forms.Media(**SHARED_MEDIA)

    def __init__(self, *args, **kwargs):
        super(PatternAdminForm, self).__init__(*args, **kwargs)

        # --- A. SYMPTOMS (Keep existing logic) ---
        symptom_pool = list(SymptomCategory.objects.exclude(symptoms__isnull=True)
                            .exclude(symptoms__exact='')
                            .values_list('symptoms', flat=True)
                            .distinct()
                            .order_by('symptoms'))

        if 'symptoms' in self.fields:
            self.fields['symptoms'].widget.data_choices = symptom_pool

        # --- B. DYNAMIC MAPPINGS (Body Types & Pathogens) ---
        body_types = list(TCMBodyTypeMapping.objects.values_list(
            'tcm_body_type', flat=True).distinct())
        pathogens = list(TCMPathogenDefinition.objects.values_list(
            'pathogen', flat=True).distinct())

        bt_choices = [('', 'Select Body Type...')] + [(b, b)
                                                      for b in body_types if b]
        p_choices = [('', 'Select Pathogen...')] + [(p, p)
                                                    for p in pathogens if p]

        # Assign choices
        self.fields['body_type_primary'].choices = bt_choices
        self.fields['body_type_secondary'].choices = bt_choices
        self.fields['body_type_tertiary'].choices = bt_choices
        self.fields['pathogenic_factor'].choices = p_choices

        # --- PRESERVE EXISTING DATA (If value is not in DB list, add it to choices so it shows up) ---
        instance = getattr(self, 'instance', None)
        if instance and instance.pk:
            # Check Pathogen
            if instance.pathogenic_factor and instance.pathogenic_factor not in pathogens:
                self.fields['pathogenic_factor'].choices.append(
                    (instance.pathogenic_factor, instance.pathogenic_factor))
            # Check Body Types
            for field in ['body_type_primary', 'body_type_secondary', 'body_type_tertiary']:
                val = getattr(instance, field)
                if val and val not in body_types:
                    self.fields[field].choices.append((val, val))

        # --- Middle vs Bottom Groups Logic (Keep existing) ---
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


@admin.register(PatternProxy)
class PatternAdmin(RemindUpdateMixin, admin.ModelAdmin):
    # --- SMART VALIDATION MAPPING ---
    # Format: ( [Fields], ModelClass, 'Lookup_Column', 'URL_Name', 'Page Name', 'Error Message' )
    universal_reminders = [
        ('admin:ui_core_bloodmarkersproxy_changelist', 'Blood Markers Page')]
    # --- 2. CONNECT THE FORM ---
    form = PatternAdminForm
# --- SMART VALIDATION MAPPING ---
    # Format: ([Fields], TargetModel, 'Lookup_Column', 'URL_Name', 'Link Text', 'Error Message')
    validation_map = [
        # 1. Check Pathogens
        (
            ['pathogenic_factor'],
            TCMPathogenDefinition,  # The model to check against
            'pathogen',             # The column in that model
            'admin:ui_core_tcmpathogenproxy_changelist',  # Link to the Proxy Admin
            'Pathogens Page',
            "You added a Pathogen that doesn't exist yet."
        ),
        # 2. Check Body Types (Primary, Secondary, Tertiary)
        (
            ['body_type_primary', 'body_type_secondary', 'body_type_tertiary'],
            TCMBodyTypeMapping,     # The model to check against
            'tcm_body_type',        # The column in that model
            'admin:ui_core_tcmbodytypeproxy_changelist',  # Link to the Proxy Admin
            'Body Types Page',
            "You added a Body Type that doesn't exist yet."
        )
    ]

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

# @admin.register(TCMBodyTypeMapping)


@admin.register(TCMBodyTypeProxy)
class TCMBodyTypeMappingAdmin(RemindUpdateMixin, admin.ModelAdmin):
    # --- REQUIREMENT C MAPPING: Body Type -> TCM Patterns ---
    universal_reminders = [
        ('admin:ui_core_patternproxy_changelist', 'TCM Patterns Page')]
    related_pages = [
        ('admin:ui_core_patternproxy_changelist', 'TCM Patterns Page')
    ]
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
    @property
    def media(self): return forms.Media(**SHARED_MEDIA)
    list_display_links = ('tcm_body_type',)
    list_per_page = 50


@admin.register(TCMPathogenProxy)
# @admin.register(TCMPathogenDefinition)
class TCMPathogenDefinitionAdmin(RemindUpdateMixin, admin.ModelAdmin):
    # --- REQUIREMENT C MAPPING: Pathogens -> TCM Patterns ---
    universal_reminders = [
        ('admin:ui_core_patternproxy_changelist', 'TCM Patterns Page')]
    related_pages = [
        ('admin:ui_core_patternproxy_changelist', 'TCM Patterns Page')
    ]
    # --- ADDED SEARCH FIELDS ---
    search_fields = ('pathogen', 'definition')
    list_filter = ('pathogen',)

    # --- EXISTING STRUCTURE PRESERVED ---
    list_display = ('pathogen', 'definition')
    @property
    def media(self): return forms.Media(**SHARED_MEDIA)

# ==============================================================================
# 3. FUNCTIONAL & SYMPTOMS (Formatting Enforced)
# ==============================================================================

# --- Helper to format string "A, B, C" into "A, B and C" ---


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


@admin.register(FunctionalCategoryProxy)
class FunctionalCategoryAdmin(RemindUpdateMixin, admin.ModelAdmin):
    form = FunctionalCategoryAdminForm  # <--- Connect the custom form here
# --- REQUIREMENT C MAPPING: Functional Med -> Blood Markers ---
# # FIX: Ensure there are exactly 6 items in the list inside the map
#     validation_map = [
#         (
#             ['functional_medicine'],             # 1. Fields to check
#             # 2. Target Model (Not a string)
#             BloodMarkersProxy,
#             'blood_test',                        # 3. Lookup column
#             'admin:ui_core_bloodmarkersproxy_changelist',  # 4. URL Name
#             'Blood Markers Page',                # 5. Page Name
#             "Validation Message Here"            # 6. Error Message
#         )
#     ]

    # Add your Universal Reminder separately as planned
    universal_reminders = [
        ('admin:ui_core_bloodmarkersproxy_changelist', 'Blood Markers Page')]
    # --- ADDED SEARCH FIELDS ---
    search_fields = ('functional_medicine',
                     'primary_category', 'secondary_category')
    list_filter = ('functional_medicine',
                   'primary_category', 'secondary_category')
    list_filter

    # --- EXISTING STRUCTURE PRESERVED ---
    list_display = ('functional_medicine',

                    'primary_category', 'secondary_category')

    @property
    def media(self): return forms.Media(**SHARED_MEDIA)


# class SymptomCategoryAdminForm(forms.ModelForm):
#     # 1. Symptoms: Allow typing (Source: Pattern model)
#     # symptoms = DynamicChoiceField(
#     #     required=False,
#     #     label="Symptom (from Patterns)",
#     #     widget=forms.Select(attrs=WIDGET_ATTRS)
#     # )

#     # 2. Primary Category: Allow typing
#     primary_category = DynamicChoiceField(
#         required=False,
#         label="Primary Category",
#         widget=forms.Select(attrs=WIDGET_ATTRS)
#     )

#     # 3. Secondary Category: Allow typing (NEW)
#     secondary_category = DynamicChoiceField(
#         required=False,
#         label="Secondary Category",
#         widget=forms.Select(attrs=WIDGET_ATTRS)
#     )

#     class Meta:
#         model = SymptomCategory
#         fields = '__all__'

#     @property
#     def media(self):
#         return forms.Media(**SHARED_MEDIA)

#     def __init__(self, *args, **kwargs):
#         super().__init__(*args, **kwargs)

#         # --- A. SYMPTOMS (From Pattern) ---
#         raw_pattern_data = Pattern.objects.values_list('symptoms', flat=True)
#         unique_symptoms = set()
#         for entry in raw_pattern_data:
#             if entry:
#                 # Split by semicolon to get individual symptoms
#                 parts = [x.strip() for x in entry.split(';') if x.strip()]
#                 unique_symptoms.update(parts)

#         sorted_symptoms = sorted(list(unique_symptoms))
#         symptom_choices = [('', 'Select Symptom...')] + [(s, s)
#                                                          for s in sorted_symptoms]
#         self.fields['symptoms'].choices = symptom_choices

#         # --- B. CATEGORIES (From FunctionalCategory) ---
#         cats = list(FunctionalCategory.objects.values_list(
#             'functional_medicine', flat=True).distinct().order_by('functional_medicine'))

#         cat_choices = [('', 'Select Category...')] + [(c, c)
#                                                       for c in cats if c]

#         # Apply choices to BOTH Primary and Secondary
#         self.fields['primary_category'].choices = cat_choices
#         self.fields['secondary_category'].choices = cat_choices

#         # --- C. PRESERVE DATA (If current value is custom) ---
#         instance = getattr(self, 'instance', None)
#         if instance and instance.pk:
#             # Preserve Symptom
#             current_sym = instance.symptoms
#             if current_sym and current_sym not in unique_symptoms:
#                 self.fields['symptoms'].choices.append(
#                     (current_sym, current_sym))

#             # Preserve Primary Category
#             current_cat = instance.primary_category
#             if current_cat and current_cat not in cats:
#                 self.fields['primary_category'].choices.append(
#                     (current_cat, current_cat))

#             # Preserve Secondary Category
#             current_sec = instance.secondary_category
#             if current_sec and current_sec not in cats:
#                 self.fields['secondary_category'].choices.append(
#                     (current_sec, current_sec))

class SymptomCategoryAdminForm(forms.ModelForm):
    # 1. UPDATED: Symptoms is now a simple Text Input (Not a selector)
    symptoms = forms.CharField(
        required=True,
        label="Symptom",
        widget=forms.TextInput(attrs={
            'style': 'width: 100%;',
            'class': 'vTextField',
            'placeholder': 'Type new symptom name...'
        })
    )

    # 2. Primary Category: Selector (Populated from DB)
    primary_category = DynamicChoiceField(
        required=False,
        label="Primary Category",
        widget=forms.Select(attrs={
            'class': 'advanced-select',
            'style': 'width: 100%',
            'data-tags': 'true',  # Allows adding a NEW category if needed
            'data-placeholder': 'Select Category...'
        })
    )

    # 3. Secondary Category: Selector (Populated from DB)
    secondary_category = DynamicChoiceField(
        required=False,
        label="Secondary Category",
        widget=forms.Select(attrs={
            'class': 'advanced-select',
            'style': 'width: 100%',
            'data-tags': 'true',
            'data-placeholder': 'Select Category...'
        })
    )

    class Meta:
        model = SymptomCategory
        fields = '__all__'

    @property
    def media(self):
        return forms.Media(**SHARED_MEDIA)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # --- POPULATE CATEGORIES (From SymptomCategory table only) ---
        # 1. Fetch values from both columns
        p_cats = list(SymptomCategory.objects.values_list(
            'primary_category', flat=True))
        s_cats = list(SymptomCategory.objects.values_list(
            'secondary_category', flat=True))

        # 2. Combine and sort
        all_existing_cats = set(p_cats + s_cats)
        cat_choices = [('', '')] + sorted([(c, c)
                                           for c in all_existing_cats if c])

        # 3. Assign to widgets
        self.fields['primary_category'].choices = cat_choices
        self.fields['secondary_category'].choices = cat_choices

        # --- PRESERVE CUSTOM DATA ---
        instance = getattr(self, 'instance', None)
        if instance and instance.pk:
            # If the saved category isn't in the list yet, add it so it displays correctly
            if instance.primary_category and instance.primary_category not in all_existing_cats:
                self.fields['primary_category'].choices.append(
                    (instance.primary_category, instance.primary_category))

            if instance.secondary_category and instance.secondary_category not in all_existing_cats:
                self.fields['secondary_category'].choices.append(
                    (instance.secondary_category, instance.secondary_category))


@admin.register(SymptomCategoryProxy)
class SymptomCategoryAdmin(RemindUpdateMixin, admin.ModelAdmin):

    form = SymptomCategoryAdminForm
    # --- REQUIREMENT C MAPPING: Symptoms -> TCM Patterns ---
# --- SMART VALIDATION MAPPING ---
    universal_reminders = [
        ('admin:ui_core_patternproxy_changelist', 'TCM Patterns Page')]
    # validation_map = [
    #     # 1. CHECK SYMPTOMS (Against TCM Patterns)
    #     (
    #         ['symptoms'],
    #         Pattern,                     # Target Model
    #         'symptoms',                  # Target Column ("Headache; Fever")
    #         'admin:ui_core_patternproxy_changelist',
    #         'TCM Patterns Page',
    #         "This symptom does not appear in any TCM Pattern yet.",
    #         ';'                          # <--- DELIMITER (Splits DB string)
    #     ),

    # ]

    # --- ADDED SEARCH FIELDS ---
    search_fields = ('symptoms', 'primary_category', 'secondary_category')

    # --- EXISTING STRUCTURE PRESERVED ---
    list_display = ('symptoms', 'primary_category', 'secondary_category')
    list_filter = ('symptoms', 'primary_category', 'secondary_category')
    @property
    def media(self): return forms.Media(**SHARED_MEDIA)


class MedicalConditionAdminForm(forms.ModelForm):
    # Standard Pattern Field (Existing)
    # tcm_patterns = forms.MultipleChoiceField(
    #     required=False,
    #     label="TCM Patterns",
    #     widget=forms.SelectMultiple(attrs=WIDGET_ATTRS)
    # )
    # Change to DynamicMultipleChoiceField to allow NEW Patterns
    tcm_patterns = DynamicMultipleChoiceField(
        required=False,
        label="TCM Patterns",
        widget=forms.SelectMultiple(attrs={
            'class': 'advanced-select', 'style': 'width: 100%', 'data-tags': 'true'
        })
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


@admin.register(MedicalConditionProxy)
class MedicalConditionAdmin(RemindUpdateMixin, admin.ModelAdmin):
    form = MedicalConditionAdminForm
# --- SMART VALIDATION MAPPING ---

    validation_map = [
        # 1. Check TCM Patterns
        (
            ['tcm_patterns'],
            Pattern,                # Target Model
            'tcm_patterns',         # Target Column
            'admin:ui_core_patternproxy_changelist',
            'TCM Patterns Page',
            "You referenced a TCM Pattern that doesn't exist."
        ),
    ]

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
    @property
    def media(self): return forms.Media(**SHARED_MEDIA)


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


@admin.register(MedicationListProxy)
class MedicationListAdmin(RemindUpdateMixin, admin.ModelAdmin):
    # --- REQUIREMENT C MAPPING: Med List -> Med Mapping ---
    universal_reminders = [
        ('admin:ui_pharma_medicationmappingproxy_changelist', 'Medications Mapping Page')]
    # validation_map = [
    #     (
    #         ['example_medications'],
    #         'admin:ui_pharma_medicationmappingproxy_changelist',
    #         'Medications Mapping Page',
    #         "You added/edited a Medication Name. Please update the Mapping table if this is a new type."
    #     )
    # ]
    related_pages = [
        ('admin:ui_pharma_medicationmappingproxy_changelist', 'Medications Mapping Page')
    ]
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
    @property
    def media(self): return forms.Media(**SHARED_MEDIA)


@admin.register(MedicationMappingProxy)
class MedicationMappingAdmin(RemindUpdateMixin, admin.ModelAdmin):
    form = MedicationMappingAdminForm
    validation_map = [
        # Check: Medication Types vs Medication List Sub-Categories
        (
            ['med_types_low', 'med_types_high'],
            MedicationList,              # Target Model
            'sub_category',              # Target Column
            'admin:ui_pharma_medicationlistproxy_changelist',
            'Medication List',
            "You added a Medication Type that doesn't exist in the Medication List."
        )
    ]

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

    @property
    def media(self): return forms.Media(**SHARED_MEDIA)

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

@admin.register(MedicationScoreDefProxy)
class MedicationScoreDefAdmin(admin.ModelAdmin):
    form = ScoreDefAdminForm
    # Display the score text and definition in the list
    list_display = ('score', 'definition')
    # Allow clicking the score text to edit
    list_display_links = ('score',)
    # Search by the text inside the score (e.g. search "Minor")
    search_fields = ('score', 'definition')
    ordering = ('score',)


@admin.register(SupplementListProxy)
class SupplementsListAdmin(RemindUpdateMixin, admin.ModelAdmin):
    # --- REQUIREMENT C MAPPING: Supp List -> Supp Mapping ---
    universal_reminders = [
        ('admin:ui_pharma_supplementmappingproxy_changelist', 'Supplements Mapping Page')]
    # validation_map = [
    #     (
    #         ['example_supplements'],
    #         'admin:ui_pharma_supplementmappingproxy_changelist',
    #         'Supplements Mapping Page',
    #         "You added/edited a Supplement Name. Please update the Mapping table if this is a new type."
    #     )
    # ]
    related_pages = [
        ('admin:ui_pharma_supplementmappingproxy_changelist', 'Supplements Mapping Page')
    ]
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
    @property
    def media(self): return forms.Media(**SHARED_MEDIA)


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


@admin.register(SupplementMappingProxy)
class SupplementsMappingAdmin(RemindUpdateMixin, admin.ModelAdmin):
    form = SupplementMappingAdminForm
    validation_map = [
        # Check: Supplement Types vs Supplement List Sub-Categories
        (
            ['supp_types_low', 'supp_types_high'],
            SupplementList,              # Target Model
            'sub_category',              # Target Column
            'admin:ui_pharma_supplementlistproxy_changelist',
            'Supplement List',
            "You added a Supplement Type that doesn't exist in the Supplement List."
        )
    ]

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
    @property
    def media(self): return forms.Media(**SHARED_MEDIA)
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


@admin.register(SupplementScoreDefProxy)
class SupplementScoreDefAdmin(admin.ModelAdmin):
    form = ScoreDefAdminForm
    list_display = ('score', 'definition')
    list_display_links = ('score',)
    search_fields = ('score', 'definition')
    ordering = ('score',)


# ==============================================================================
# 5. WBC GLOSSARY & MATRIX (Search Enabled)
# ==============================================================================


@admin.register(WBCGlossaryProxy)
class WBCGlossaryAdmin(RemindUpdateMixin, admin.ModelAdmin):
    # --- REQUIREMENT C MAPPING: WBC Glossary -> WBC Matrix ---
    universal_reminders = [
        ('admin:ui_wbc_wbcmatrixproxy_changelist', 'WBC Matrix Page')]
    related_pages = [
        ('admin:ui_wbc_wbcmatrixproxy_changelist', 'WBC Matrix Page')
    ]
    # --- ADDED SEARCH FIELDS ---
    search_fields = ('term', 'definition', 'next_steps')

    # --- EXISTING STRUCTURE PRESERVED ---
    list_display = ('term', 'definition', 'next_steps')
    fields = ('term', 'definition', 'next_steps')
    list_filter = ('term',)
    list_display_links = ('term',)
    list_per_page = 50
    @property
    def media(self): return forms.Media(**SHARED_MEDIA)


class WBCMatrixAdminForm(forms.ModelForm):
    # Change ALL to DynamicChoiceField
    primary_int = DynamicChoiceField(
        required=False, label="Primary Interpretation", widget=forms.Select(attrs=WIDGET_ATTRS))
    secondary = DynamicChoiceField(
        required=False, label="Secondary", widget=forms.Select(attrs=WIDGET_ATTRS))
    tertiary = DynamicChoiceField(
        required=False, label="Tertiary", widget=forms.Select(attrs=WIDGET_ATTRS))
    quaternary = DynamicChoiceField(
        required=False, label="Quaternary", widget=forms.Select(attrs=WIDGET_ATTRS))
    quinary = DynamicChoiceField(
        required=False, label="Quinary", widget=forms.Select(attrs=WIDGET_ATTRS))

    class Meta:
        model = WBCMatrix
        fields = '__all__'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        terms = list(WBCGlossary.objects.values_list(
            'term', flat=True).distinct().order_by('term'))
        term_choices = [('', 'Select Term...')] + [(t, t) for t in terms if t]

        self.fields['primary_int'].choices = term_choices
        self.fields['secondary'].choices = term_choices
        self.fields['tertiary'].choices = term_choices
        self.fields['quaternary'].choices = term_choices
        self.fields['quinary'].choices = term_choices

        # Check existing values and add them if missing
        instance = getattr(self, 'instance', None)
        if instance and instance.pk:
            for field in ['primary_int', 'secondary', 'tertiary', 'quaternary', 'quinary']:
                val = getattr(instance, field)
                if val and val not in terms:
                    self.fields[field].choices.append((val, val))

    @property
    def media(self): return forms.Media(**SHARED_MEDIA)


@admin.register(WBCMatrixProxy)
class WBCMatrixAdmin(RemindUpdateMixin, admin.ModelAdmin):
    form = WBCMatrixAdminForm
    validation_map = [
        # Check: WBC Glossary Terms
        (
            ['primary_int', 'secondary', 'tertiary', 'quaternary', 'quinary'],
            WBCGlossary,                 # Target Model
            'term',                      # Target Column
            'admin:ui_wbc_wbcglossaryproxy_changelist',
            'WBC Glossary',
            "You used a Term that is not defined in the WBC Glossary."
        )
    ]

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
        js = SHARED_MEDIA['js']
        # css = {
        #     'all': ('admin/css/admin_enhanced.css',)
        # }
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
# 7. LIFESTYLE & TCM DEFINITIONS (Search Enabled)
# ==============================================================================


@admin.register(LifestyleQuestionnaireProxy)
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
    @property
    def media(self): return forms.Media(**SHARED_MEDIA)

# AI AAGENT PROMPT AND RESULT


@admin.register(AIAgentLogProxy)
class AIAgentLogAdmin(admin.ModelAdmin):
    # Completely Read-Only Admin
    list_display = ('created_at', 'status', 'panel_name', 'user_identifier', 'result', "error_message",
                    'input_tokens', 'output_tokens', 'generation_time_ms')
    list_filter = ('status', 'panel_name', 'created_at')
    search_fields = ('user_identifier', 'error_message', 'panel_name')

    # Prevent adding, changing, or deleting
    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    # FIX: Use AIAgentLogProxy instead of AIAgentLog to avoid import errors
    readonly_fields = [field.name for field in AIAgentLogProxy._meta.fields]

    @property
    def media(self):
        return forms.Media(**SHARED_MEDIA)


# @admin.register(AIAgentConfigProxy)
# class AIAgentConfigAdmin(admin.ModelAdmin):
#     list_display = ('panel_name', 'model_id', 'temperature',
#                     'is_active', 'updated_at')
#     list_filter = ('is_active', 'model_id')
#     search_fields = ('panel_name', 'system_prompt')

#     # Make updated_at read-only
#     readonly_fields = ('updated_at',)

#     fieldsets = (
#         ('Configuration', {
#             'fields': ('panel_name', 'is_active', 'model_id', 'temperature')
#         }),
#         ('Prompts', {
#             'fields': ('system_prompt', 'user_prompt_template'),
#             'description': 'Ensure {json_data} is present in the User Prompt Template.'
#         }),
#         ('Metadata', {
#             'fields': ('updated_at',)
#         }),
#     )

#     @property
#     def media(self):
#         return forms.Media(**SHARED_MEDIA)


# --- 1. Custom Form to Handle Comma/Dot Logic ---
class AIAgentConfigForm(forms.ModelForm):
    # We use a CharField (Text) for input so the user CAN type a comma without an error immediately.
    # We will convert it to a Float in the clean_temperature method.
    # temperature = forms.CharField(
    #     label="Temperature",
    #     help_text="Range: 0.0 to 2.0. (Examples: 0.5, 1, 1,2)",
    #     widget=forms.TextInput(attrs={'placeholder': '0.5'})
    # )

    class Meta:
        model = AIAgentConfigProxy
        fields = '__all__'

    def clean_temperature(self):
        raw_value = self.cleaned_data['temperature']

        # 1. Convert input to string just in case
        value_str = str(raw_value)

        # 2. Replace comma with dot
        if ',' in value_str:
            value_str = value_str.replace(',', '.')

        # 3. Try to convert to float
        try:
            final_float = float(value_str)
        except ValueError:
            raise forms.ValidationError(
                "Invalid temperature. Please enter a number like 0.5 or 1.0")

        # 4. (Optional) Force 1 -> 1.0 logic is automatic with float(),
        # but the database stores it as float anyway.
        return final_float


# --- 2. Admin Configuration ---
@admin.register(AIAgentConfigProxy)
class AIAgentConfigAdmin(admin.ModelAdmin):
    # Connect the custom form we made above
    form = AIAgentConfigForm

    list_display = (
        'panel_name',
        'model_id',
        'is_active',
        'system_prompt',
        'user_prompt_template',
        'updated_at'
    )
    list_filter = ('is_active', 'model_id')
    search_fields = ('panel_name', 'system_prompt')

    # This logic locks the fields when you are Editing (obj exists),
    # but keeps them unlocked when you are Creating (obj is None).

    def get_readonly_fields(self, request, obj=None):
        if obj:  # If we are editing an existing row
            return ('panel_name', 'updated_at')
        # If we are creating a new row, only updated_at is locked (auto-date)
        return ('updated_at',)

    fieldsets = (
        ('Configuration', {
            'fields': ('panel_name', 'is_active', 'model_id'),
        }),
        ('Prompts', {
            'fields': ('system_prompt', 'user_prompt_template'),
            'description': 'Ensure {json_data} is present in the User Prompt Template.'
        }),
        ('Metadata', {
            'fields': ('updated_at',)
        }),
    )

    @property
    def media(self):
        # Keeps your existing styling if you have any
        return forms.Media()
