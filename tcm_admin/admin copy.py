
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
import django
# --- GLOBAL CONFIGURATION & ASSETS ---
# Common media config to ensure Select2 loads for all search-enabled forms
# --- GLOBAL CONFIGURATION & ASSETS ---
# --- GLOBAL CONFIGURATION & ASSETS ---
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

# --- 2. NOTIFICATION MIXIN ---


WIDGET_ATTRS = {
    'class': 'advanced-select',
    'style': 'width: 100%'
}


# class RemindUpdateMixin:
#     """
#     DYNAMIC VALIDATION MIXIN (SERVER-SIDE):
#     1. Intercepts 'save_model'.
#     2. Checks specific fields against 'validation_map'.
#     3. If triggered -> Pauses Save -> Renders HTML Interception Page.
#     4. Page offers "Go Back (Edit)" or "Confirm & Save".
#     """

#     # Configuration Structure:
#     # [ (['field_name_1', 'field_name_2'], 'admin_url_name', 'Display Link Text') ]
#     validation_map = []

#     def save_model(self, request, obj, form, change):
#         # 1. Check if "Confirm & Save" was already clicked
#         if request.POST.get('_validation_confirmed') == 'true':
#             super().save_model(request, obj, form, change)
#             return

#         # 2. Check Triggers: Determine which links to show based on data entered
#         active_links = []
#         triggered = False

#         if not self.validation_map:
#             # Fallback: Save immediately if no map is defined
#             super().save_model(request, obj, form, change)
#             return

#         for fields, url_name, display_name in self.validation_map:
#             # Check if ANY of the fields in this group have data in the form
#             group_triggered = False
#             for field in fields:
#                 value = form.cleaned_data.get(field)
#                 # We trigger if there is ANY value (works for lists or strings)
#                 if value:
#                     group_triggered = True
#                     triggered = True
#                     break

#             # If data exists in these fields, add this specific link to the list
#             if group_triggered:
#                 try:
#                     url = reverse(url_name)
#                     active_links.append((url, display_name))
#                 except Exception:
#                     # Safely ignore invalid URLs to prevent crashes
#                     pass

#         # 3. Decision Time
#         if not triggered:
#             # No sensitive fields were touched -> Save immediately
#             super().save_model(request, obj, form, change)
#         else:
#             # Sensitive data found -> PAUSE SAVE.
#             # Set flags so response_add/change knows to render the HTML page.
#             request._needs_interception = True
#             request._active_links = active_links

#     def _build_interception_page(self, request):
#         active_links = getattr(request, '_active_links', [])

#         # Build Link List
#         links_html = ""
#         for url, name in active_links:
#             links_html += (
#                 f'<a href="{url}" target="_blank" class="link-btn">'
#                 f'🔗 Go to {name}'
#                 f'</a>'
#             )

#         html = f"""
#         <!DOCTYPE html>
#         <html>
#         <head>
#             <title>Value Not Found</title>
#             <style>
#                 body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif; background-color: #f4f6f9; display: flex; justify-content: center; align-items: center; height: 100vh; margin: 0; }}
#                 .card {{ background: white; padding: 40px; border-radius: 8px; box-shadow: 0 4px 20px rgba(0,0,0,0.1); max-width: 550px; width: 100%; text-align: center; border-top: 6px solid #dc3545; }}
#                 h2 {{ color: #dc3545; margin-top: 0; font-size: 24px; margin-bottom: 15px; }}

#                 .message-box {{ color: #555; font-size: 16px; line-height: 1.6; margin-bottom: 25px; text-align: left; background: #fff5f5; padding: 20px; border-radius: 6px; border-left: 5px solid #dc3545; }}
#                 .strong {{ font-weight: bold; color: #333; }}

#                 .links-container {{ display: flex; flex-direction: column; gap: 12px; margin-bottom: 30px; text-align: left; }}
#                 .link-btn {{ display: block; padding: 14px; background-color: #fff; color: #dc3545; text-decoration: none; border-radius: 6px; font-weight: 600; border: 2px solid #dc3545; transition: 0.2s; box-shadow: 0 2px 4px rgba(0,0,0,0.05); text-align: center; }}
#                 .link-btn:hover {{ background-color: #dc3545; color: white; transform: translateY(-2px); }}

#                 .btn-row {{ margin-top: 20px; }}
#                 .back-btn {{ width: 100%; padding: 15px; background-color: #6c757d; color: white; border: none; border-radius: 6px; font-size: 16px; font-weight: bold; cursor: pointer; text-decoration: none; transition: 0.2s; }}
#                 .back-btn:hover {{ background-color: #5a6268; }}
#             </style>
#         </head>
#         <body>
#             <div class="card">
#                 <h2>⚠️ Value Not Found</h2>

#                 <div class="message-box">
#                     <span class="strong">This TCM or Medicine value does not exist in the system yet.</span><br><br>
#                     Please click the link below to add it to the relevant table <b>first</b>.<br>
#                     After adding it, you can go back to continue.
#                 </div>

#                 <div class="links-container">
#                     {links_html}
#                 </div>

#                 <p style="font-size: 13px; color: #888; margin-bottom: 15px;">
#                     (Link opens in a new tab so you don't lose your work)
#                 </p>

#                 <div class="btn-row">
#                     <button type="button" class="back-btn" onclick="window.history.back();">
#                         ⬅ Go Back to Continue Editing
#                     </button>
#                 </div>
#             </div>
#         </body>
#         </html>
#         """
#         return HttpResponse(html)

#     def response_add(self, request, obj, post_url_continue=None):
#         if getattr(request, '_needs_interception', False):
#             return self._build_interception_page(request)
#         return super().response_add(request, obj, post_url_continue)

#     def response_change(self, request, obj):
#         if getattr(request, '_needs_interception', False):
#             return self._build_interception_page(request)
#         return super().response_change(request, obj)

# ==============================================================================
#  SERVER-SIDE DYNAMIC VALIDATION MIXIN
# ==============================================================================
class RemindUpdateMixin:
    """
    DYNAMIC VALIDATION MIXIN:
    1. Checks if specific fields were edited.
    2. Generates specific warning text based on the field triggered.
    3. Renders a page with "Go Back" options.
    """
    # Structure:
    # [ (['field_list'], 'url_name', 'Link Text', 'Custom Warning Message') ]
    validation_map = []

    def save_model(self, request, obj, form, change):
        # 1. Check if "Confirm & Save" was clicked (if we ever need to bring it back)
        if request.POST.get('_validation_confirmed') == 'true':
            super().save_model(request, obj, form, change)
            return

        # 2. Determine which links/messages to show
        active_validations = []
        triggered = False

        if not self.validation_map:
            super().save_model(request, obj, form, change)
            return

        for fields, url_name, display_name, message in self.validation_map:
            # Check if ANY of the fields in this group have data
            group_triggered = False
            for field in fields:
                value = form.cleaned_data.get(field)
                if value:
                    group_triggered = True
                    triggered = True
                    break

            # If data exists, store the link AND the specific message
            if group_triggered:
                try:
                    url = reverse(url_name)
                    active_validations.append({
                        'url': url,
                        'name': display_name,
                        'message': message
                    })
                except Exception:
                    pass

        # 3. If no validation fields were touched, Save immediately
        if not triggered:
            super().save_model(request, obj, form, change)
        else:
            # 4. Triggered: Pause Save and Render Page
            request._needs_interception = True
            request._active_validations = active_validations

    def _build_interception_page(self, request):
        active_validations = getattr(request, '_active_validations', [])

        # Build the dynamic HTML list
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
                body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif; background-color: #f4f6f9; display: flex; justify-content: center; align-items: center; height: 100vh; margin: 0; }}
                .card {{ background: white; padding: 40px; border-radius: 8px; box-shadow: 0 4px 20px rgba(0,0,0,0.1); max-width: 600px; width: 100%; text-align: center; border-top: 6px solid #dc3545; }}
                h2 {{ color: #dc3545; margin-top: 0; font-size: 24px; margin-bottom: 20px; }}
                
                .validation-container {{ text-align: left; margin-bottom: 30px; display: flex; flex-direction: column; gap: 15px; }}
                
                .validation-item {{ background: #fff5f5; border: 1px solid #f5c6cb; border-radius: 6px; padding: 15px; }}
                .validation-msg {{ color: #721c24; font-weight: 600; margin-bottom: 10px; font-size: 15px; line-height: 1.4; }}
                
                .link-btn {{ display: inline-block; padding: 8px 15px; background-color: #fff; color: #dc3545; text-decoration: none; border-radius: 4px; font-weight: bold; border: 1px solid #dc3545; transition: 0.2s; font-size: 14px; }}
                .link-btn:hover {{ background-color: #dc3545; color: white; }}

                .back-btn {{ width: 100%; padding: 15px; background-color: #6c757d; color: white; border: none; border-radius: 6px; font-size: 16px; font-weight: bold; cursor: pointer; text-decoration: none; transition: 0.2s; }}
                .back-btn:hover {{ background-color: #5a6268; }}
                
                .sub-text {{ font-size: 13px; color: #888; margin-top: 15px; }}
            </style>
        </head>
        <body>
            <div class="card">
                <h2>⚠️ Data Verification Required</h2>
                
                <p style="color: #555; margin-bottom: 20px;">
                    The system detected new data that may require updates in other tables.
                </p>

                <div class="validation-container">
                    {validation_html}
                </div>

                <div class="btn-row">
                    <button type="button" class="back-btn" onclick="window.history.back();">
                        ⬅ Go Back to Continue Editing
                    </button>
                </div>
                <div class="sub-text">(Links open in a new tab so you don't lose your work)</div>
            </div>
        </body>
        </html>
        """
        return HttpResponse(html)


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


class StrictSemicolonListWidget(Widget):
    """
    Robust Widget that waits for jQuery to load before initializing.
    Works with Jazzmin (footer scripts) and Standard Admin (header scripts).
    """
    template_name = 'django/forms/widgets/textarea.html'

    def __init__(self, data_choices=None, *args, **kwargs):
        self.data_choices = data_choices if data_choices is not None else []
        super().__init__(*args, **kwargs)

    def render(self, name, value, attrs=None, renderer=None):
        # Force standard Django ID format
        main_id = attrs.get('id', 'id_' + name)
        current_val = value if value is not None else ''

        # 1. Build Options
        options_html = '<option value="">-- Select Symptom --</option>'
        for item in self.data_choices:
            safe_item = str(item).replace('"', '&quot;')
            options_html += f'<option value="{safe_item}">{safe_item}</option>'

        options_json = json.dumps(options_html)

        html = f"""
        <div id="wrapper_{main_id}" class="strict-list-wrapper" 
             style="border: 1px solid #ccc; padding: 10px; border-radius: 4px; background: #f9f9f9;">
            
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
                <button type="button" id="btn_add_{main_id}" class="button" 
                        style="font-weight: bold; cursor: pointer;">+ Add Symptom</button>
            </div>
            
            <input type="hidden" name="{name}" id="{main_id}" value="{current_val}">
        </div>

        <script>
        (function() {{
            // --- WAITER FUNCTION ---
            // This waits for jQuery to load in the footer before running our code
            function waitForJQuery(callback) {{
                var maxChecks = 100; // Wait up to 5 seconds (100 * 50ms)
                var currentCheck = 0;
                
                var interval = setInterval(function() {{
                    var $ = window.jQuery || (window.django && window.django.jQuery);
                    if ($) {{
                        clearInterval(interval);
                        callback($); // Pass jQuery to the callback
                    }} else {{
                        currentCheck++;
                        if (currentCheck >= maxChecks) {{
                            clearInterval(interval);
                            console.error("StrictSemicolonListWidget: jQuery timed out (never loaded).");
                        }}
                    }}
                }}, 50); // Check every 50ms
            }}

            // --- MAIN WIDGET LOGIC ---
            waitForJQuery(function($) {{
                // This code only runs AFTER jQuery is definitely loaded
                
                console.log("Widget initialized for: {main_id}");
                
                var tbody = $('#tbody_{main_id}');
                var input = $('#{main_id}');
                var btn = $('#btn_add_{main_id}');
                var allOptions = {options_json};

                function addRow(selectedValue) {{
                    selectedValue = selectedValue || '';
                    var rowId = 'row_' + Math.random().toString(36).substr(2, 9);
                    
                    var rowHtml = `
                        <tr id="${{rowId}}">
                            <td style="padding: 4px 0;">
                                <select class="sync-select" style="width: 98%;">
                                    ${{allOptions}}
                                </select>
                            </td>
                            <td style="text-align: center;">
                                <button type="button" class="remove-btn" 
                                        style="color: red; cursor: pointer; border: none; background: none; font-weight: bold; font-size: 1.2em;">
                                    &times;
                                </button>
                            </td>
                        </tr>
                    `;
                    var $row = $(rowHtml);
                    tbody.append($row);

                    if (selectedValue) {{
                        $row.find('select').val(selectedValue);
                    }}

                    // Auto-enable Select2 if Jazzmin provides it
                    if ($.fn.select2) {{
                        $row.find('select').select2({{ width: '100%' }});
                    }}
                }}

                function updateHiddenInput() {{
                    var arr = [];
                    tbody.find('.sync-select').each(function() {{
                        var v = $(this).val();
                        if (v && v.trim()) arr.push(v);
                    }});
                    input.val(arr.join('; '));
                }}

                // --- EVENTS ---
                // Remove any old events to prevent duplicates
                btn.off('click').on('click', function(e) {{
                    e.preventDefault();
                    addRow('');
                }});

                tbody.on('click', '.remove-btn', function() {{
                    $(this).closest('tr').remove();
                    updateHiddenInput();
                }});

                tbody.on('change', '.sync-select', function() {{
                    updateHiddenInput();
                }});

                // --- INITIAL LOAD ---
                var raw = input.val() || '';
                if (raw) {{
                    var items = raw.split(';');
                    items.forEach(function(item) {{
                        if (item.trim()) addRow(item.trim());
                    }});
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
# --- DYNAMIC MAPPING CONFIGURATION ---
    # Format: ( [List of Fields], 'URL Name', 'Link Label' )
    validation_map = [
        (
            ['tcm_diag_low', 'tcm_diag_high'],
            'admin:ui_core_patternproxy_changelist',
            'TCM Patterns Page',
            "You referenced a TCM Diagnosis. Please ensure this Pattern exists in the system."
        ),
        (
            ['func_diag_low', 'func_diag_high'],
            'admin:ui_core_functionalcategoryproxy_changelist',
            'Functional Medicine Page',
            "You referenced a Functional Diagnosis. Please ensure this Category exists in the system."
        ),
        (
            ['med_types_low', 'med_types_high'],
            'admin:ui_pharma_medicationmappingproxy_changelist',
            'Medication Mapping Page',
            "You added a Medication Type. Please check the Medication Mapping table."
        ),
        (
            ['supp_types_low', 'supp_types_high'],
            'admin:ui_pharma_supplementmappingproxy_changelist',
            'Supplement Mapping Page',
            "You added a Supplement Type. Please check the Supplement Mapping table."
        )
    ]

    # 2. LINKS TO SHOW (Always show ALL of them if triggered)
    related_pages = [
        ('admin:ui_core_patternproxy_changelist', 'TCM Patterns Page'),
        ('admin:ui_core_functionalcategoryproxy_changelist',
         'Functional Medicine Indications'),
        ('admin:ui_pharma_medicationmappingproxy_changelist', 'Medication Mapping Page'),
        ('admin:ui_pharma_supplementmappingproxy_changelist', 'Supplement Mapping Page')
    ]

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
            # Attach the FIXED Strict Widget
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

        # --- B. BODY TYPES & PATHOGENS ---
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

        # --- C. DYNAMIC MIDDLE / BOTTOM GROUPS ---
        # Logic: Allow selecting existing values or typing new ones (via Select2 tags)

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

        # Apply widget logic for Middle Group
        for f_name in middle_group:
            if f_name in self.fields:
                self.fields[f_name].widget = forms.Select(
                    choices=middle_choices,
                    attrs={'class': 'advanced-select', 'style': 'width: 100%',
                           'data-tags': 'true', 'data-placeholder': 'Select Middle Category...'}
                )

        # Apply widget logic for Bottom Group
        for f_name in bottom_group:
            if f_name in self.fields:
                self.fields[f_name].widget = forms.Select(
                    choices=bottom_choices,
                    attrs={'class': 'advanced-select', 'style': 'width: 100%',
                           'data-tags': 'true', 'data-placeholder': 'Select Bottom Category...'}
                )

        # Safety Check: If the DB has a value not in the pool, add it so it displays correctly
        instance = getattr(self, 'instance', None)
        if instance and instance.pk:
            all_target_fields = middle_group + bottom_group
            for f_name in all_target_fields:
                val = getattr(instance, f_name, None)
                if val:
                    # Access the widget we just assigned
                    current_widget = self.fields[f_name].widget
                    existing_keys = [k for k, v in current_widget.choices]
                    if val not in existing_keys:
                        current_widget.choices.append((val, val))


@admin.register(PatternProxy)
class PatternAdmin(RemindUpdateMixin, admin.ModelAdmin):

    validation_map = [
        (
            ['pathogenic_factor', 'body_type_primary'],
            'admin:ui_core_bloodmarkersproxy_changelist',
            'Blood Markers Page',
            "You modified the Pathogen or Body Type definition. Please verify if Blood Marker mappings need updates."
        )
    ]
    # Validation Mapping: TCM Patterns -> Blood Markers
    related_pages = [
        ('admin:ui_core_bloodmarkersproxy_changelist', 'Blood Markers Page')
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

    @property
    def media(self):
        return forms.Media(**SHARED_MEDIA)

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
    validation_map = [
        (
            ['functional_medicine'],
            'admin:ui_core_bloodmarkersproxy_changelist',
            'Blood Markers Page',
            "You modified a Functional Category Name. Please ensure Blood Markers referencing this are updated."
        )
    ]
    related_pages = [
        ('admin:ui_core_bloodmarkersproxy_changelist', 'Blood Markers Page')
    ]
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


@admin.register(SymptomCategoryProxy)
class SymptomCategoryAdmin(RemindUpdateMixin, admin.ModelAdmin):

    form = SymptomCategoryAdminForm
    # --- REQUIREMENT C MAPPING: Symptoms -> TCM Patterns ---
    related_pages = [
        ('admin:ui_core_patternproxy_changelist', 'TCM Patterns Page')
    ]

    # --- ADDED SEARCH FIELDS ---
    search_fields = ('symptoms', 'primary_category', 'secondary_category')

    # --- EXISTING STRUCTURE PRESERVED ---
    list_display = ('symptoms', 'primary_category', 'secondary_category')
    list_filter = ('symptoms', 'primary_category', 'secondary_category')
    @property
    def media(self): return forms.Media(**SHARED_MEDIA)


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


@admin.register(MedicalConditionProxy)
class MedicalConditionAdmin(RemindUpdateMixin, admin.ModelAdmin):
    form = MedicalConditionAdminForm
    validation_map = [
        (
            ['tcm_patterns'],
            'admin:ui_core_patternproxy_changelist',
            'TCM Patterns Page',
            "You linked this Condition to a TCM Pattern. Please verify the Pattern definition if it is new."
        )
    ]
    # Screenshot didn't explicitly show this one, but based on logic:
    related_pages = [
        ('admin:ui_core_patternproxy_changelist', 'TCM Patterns Page')
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
# 5. WBC GLOSSARY & MATRIX (Search Enabled)
# ==============================================================================
@admin.register(WBCGlossaryProxy)
class WBCGlossaryAdmin(RemindUpdateMixin, admin.ModelAdmin):
    # --- REQUIREMENT C MAPPING: WBC Glossary -> WBC Matrix ---
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

    @property
    def media(self): return forms.Media(**SHARED_MEDIA)


@admin.register(WBCMatrixProxy)
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
    validation_map = [
        (
            ['example_medications'],
            'admin:ui_pharma_medicationmappingproxy_changelist',
            'Medications Mapping Page',
            "You added/edited a Medication Name. Please update the Mapping table if this is a new type."
        )
    ]
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


@admin.register(SupplementScoreDefProxy)
class SupplementScoreDefAdmin(admin.ModelAdmin):
    form = ScoreDefAdminForm
    list_display = ('score', 'definition')
    list_display_links = ('score',)
    search_fields = ('score', 'definition')
    ordering = ('score',)


@admin.register(SupplementListProxy)
class SupplementsListAdmin(RemindUpdateMixin, admin.ModelAdmin):
    # --- REQUIREMENT C MAPPING: Supp List -> Supp Mapping ---
    validation_map = [
        (
            ['example_supplements'],
            'admin:ui_pharma_supplementmappingproxy_changelist',
            'Supplements Mapping Page',
            "You added/edited a Supplement Name. Please update the Mapping table if this is a new type."
        )
    ]
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


# @admin.register(TCMBodyTypeMapping)
@admin.register(TCMBodyTypeProxy)
class TCMBodyTypeMappingAdmin(RemindUpdateMixin, admin.ModelAdmin):
    # --- REQUIREMENT C MAPPING: Body Type -> TCM Patterns ---
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
