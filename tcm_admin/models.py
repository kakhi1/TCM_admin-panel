from django.db import models
import uuid

from django.core.validators import MinValueValidator, MaxValueValidator


class Analysis(models.Model):
    id = models.BigAutoField(primary_key=True)

    panel = models.CharField(
        max_length=255, db_column='Panel', verbose_name="Panel", blank=False, null=False)
    blood_test = models.CharField(
        max_length=255, db_column='Blood Test', verbose_name="Blood Test", blank=False, null=False)
    blood_test_full = models.CharField(max_length=255, db_column='Blood Test (Full Name)',
                                       verbose_name="Blood Test (Full Name)", blank=True, null=True)
    blood_test_acronym = models.CharField(
        max_length=100, db_column='Blood Test (Acronym)', verbose_name="Blood Test (Acronym)", blank=True, null=True)

    units = models.CharField(
        max_length=100, db_column='Units', verbose_name="Units", blank=False, null=False)
    units_interchangeable = models.CharField(
        max_length=100, db_column='Units (Interchangeable)', verbose_name="Units (Interchangeable)", blank=True, null=True)

    ideal_low = models.FloatField(
        db_column='Ideal (Range Low)', verbose_name="Ideal (Range Low)", blank=True, null=True)
    ideal_high = models.FloatField(
        db_column='Ideal (Range High)', verbose_name="Ideal (Range High)", blank=True, null=True)
    absence_low = models.FloatField(db_column='Absence of Disease (Range Low)',
                                    verbose_name="Absence of Disease (Range Low)", blank=True, null=True)
    absence_high = models.FloatField(db_column='Absence of Disease (Range High)',
                                     verbose_name="Absence of Disease (Range High)", blank=True, null=True)

    conv_diag_low = models.TextField(db_column='Conventional Medicine Diagnosis - low',
                                     verbose_name="Conventional Med Diagnosis (Low)", blank=True, null=True)
    conv_diag_high = models.TextField(db_column='Conventional Medicine Diagnosis - High',
                                      verbose_name="Conventional Med Diagnosis (High)", blank=True, null=True)

    # --- LOGIC CONNECTION FIELDS (Mapped via Admin Form) ---
    func_diag_low = models.TextField(db_column='Functional Medicine Diagnosis - Low',
                                     verbose_name="Functional Med Diagnosis (Low)", blank=True, null=True)
    func_diag_high = models.TextField(db_column='Functional Medicine Diagnosis - High',
                                      verbose_name="Functional Med Diagnosis (High)", blank=True, null=True)
    tcm_diag_low = models.TextField(
        db_column='TCM Diagnosis - Low', verbose_name="TCM Diagnosis (Low)", blank=True, null=True)
    tcm_diag_high = models.TextField(
        db_column='TCM Diagnosis - High', verbose_name="TCM Diagnosis (High)", blank=True, null=True)
    # -----------------------------------------------------

    organs_conv_func = models.TextField(
        db_column='Governing Organs (Conventional & Functional)', verbose_name="Organs (Conv & Func)", blank=True, null=True)
    organs_tcm = models.TextField(
        db_column='Governing Organs (TCM)', verbose_name="Organs (TCM)", blank=True, null=True)

    possible_assoc_pathogens = models.TextField(
        db_column='Possible associated pathogens', verbose_name="Possible Assoc Pathogens", blank=True, null=True)

    # 2. Severity: Custom "Select" text
    severity = models.IntegerField(
        db_column='Deviation Severity (1-5)',
        verbose_name="Severity (1-5)",
        blank=True,
        null=True,
        # We add a custom empty label here
        choices=[(None, 'Select Severity Score')] + [(i, str(i))
                                                     for i in range(1, 6)],
        validators=[MinValueValidator(1), MaxValueValidator(5)]
    )
    # severity = models.IntegerField(
    #     db_column='Deviation Severity (1-5)', verbose_name="Severity (1-5)", blank=True, null=True)

    pathogens_low = models.TextField(db_column='Possible Pathogens (Low Result)',
                                     verbose_name="Pathogens (Low Result)", blank=True, null=True)
    pathogens_high = models.TextField(db_column='Possible Pathogens (High Result)',
                                      verbose_name="Pathogens (High Result)", blank=True, null=True)

# 1. Vital Marker: Strictly Yes/No, Default No
    vital_marker = models.CharField(
        max_length=3,
        db_column='Vital Marker',
        verbose_name="Vital Marker",
        choices=[('No', 'No'), ('Yes', 'Yes')],
        default='No',
        blank=False,  # Changed to False to ensure a value is always picked
        null=False   # Removed Null to favor the default 'No'
    )

    # ----------------------------------
    func_panel_1 = models.CharField(max_length=255, db_column='Functional Panel 1',
                                    verbose_name="Functional Panel 1", blank=True, null=True)
    func_panel_2 = models.CharField(max_length=255, db_column='Functional Panel 2',
                                    verbose_name="Functional Panel 2", blank=True, null=True)
    func_panel_3 = models.CharField(max_length=255, db_column='Functional Panel 3',
                                    verbose_name="Functional Panel 3", blank=True, null=True)

    class Meta:
        managed = True  # <--- CHANGED: Allows you to add/edit rows
        db_table = 'analysis'
        verbose_name = "Blood Marker"

    def __str__(self):
        return self.blood_test


class Pattern(models.Model):
    # id = models.BigAutoField(primary_key=True)
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    # 1. TCM patterns
    tcm_patterns = models.CharField(
        max_length=255, db_column='TCM patterns', verbose_name="TCM patterns")

    # 2. Excess/Deficiency/General
    excess_deficiency = models.CharField(max_length=100, db_column='Excess/Deficiency/General',
                                         verbose_name="Excess/Deficiency/General", blank=True, null=True)

    # 3. Modern Description
    modern_description = models.TextField(
        db_column='Modern Description', verbose_name="Modern Description", blank=True, null=True)

    # 4-7. Middle Level Categories
    middle_primary = models.CharField(max_length=255, db_column='Middle Level - Primary Category',
                                      verbose_name="Middle Level - Primary Category", blank=True, null=True)
    middle_secondary = models.CharField(max_length=255, db_column='Middle Level - Secondary Category',
                                        verbose_name="Middle Level - Secondary Category", blank=True, null=True)
    middle_tertiary = models.CharField(max_length=255, db_column='Middle Level - Tertiary Category',
                                       verbose_name="Middle Level - Tertiary Category", blank=True, null=True)
    middle_quantery = models.CharField(max_length=255, db_column='Middle Level - Quantery Category',
                                       verbose_name="Middle Level - Quantery Category", blank=True, null=True)

    # 8-9. Bottom Level Categories
    bottom_primary = models.CharField(max_length=255, db_column='Bottom Level - Primary Category',
                                      verbose_name="Bottom Level - Primary Category", blank=True, null=True)
    bottom_secondary = models.CharField(max_length=255, db_column='Bottom Level - Secondary Category',
                                        verbose_name="Bottom Level - Secondary Category", blank=True, null=True)

    # 10. Symptoms
    symptoms = models.TextField(
        db_column='Symptoms', verbose_name="Symptoms", blank=True, null=True)

    # 11-13. Body Types
    body_type_primary = models.CharField(
        max_length=255, db_column='TCM Body Type - Primary', verbose_name="TCM Body Type - Primary", blank=True, null=True)
    body_type_secondary = models.CharField(
        max_length=255, db_column='TCM Body Type - Secondary', verbose_name="TCM Body Type - Secondary", blank=True, null=True)
    body_type_tertiary = models.CharField(
        max_length=255, db_column='TCM Body Type - Tertiary', verbose_name="TCM Body Type - Tertiary", blank=True, null=True)

    # 14-15. Impacts
    positive_impacts = models.TextField(db_column='Medication/Suppliments - Positive Impacts',
                                        verbose_name="Medication/Suppliments - Positive Impacts", blank=True, null=True)
    negative_impacts = models.TextField(db_column='Medication/Suppliments - Negative Impacts',
                                        verbose_name="Medication/Suppliments - Negative Impacts", blank=True, null=True)

    # 16. Rationale
    rationale = models.TextField(
        db_column='Rationale', verbose_name="Rationale", blank=True, null=True)

    # 17. Pathogenci factor (Original DB spelling)
    pathogenic_factor = models.CharField(
        max_length=255, db_column='Pathogenci factor', verbose_name="Pathogenci factor", blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'patterns'
        verbose_name = "Patterns Definition"
        verbose_name_plural = "Patterns Definitions"

    def __str__(self):
        return self.tcm_patterns


class FunctionalCategory(models.Model):
    # id = models.BigAutoField(primary_key=True)
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    functional_medicine = models.CharField(
        max_length=255, db_column='Functional Medicine')
    primary_category = models.CharField(
        max_length=255, db_column='Primary Category')
    secondary_category = models.CharField(
        max_length=255, db_column='Secondary Category', blank=True, null=True)
    tertiary_category = models.CharField(
        max_length=255, db_column='Tertiary Category', blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'functional'
        verbose_name_plural = 'Functional Med Category Mapping'
    # ADD THIS:

    def __str__(self):
        return self.functional_medicine


class SymptomCategory(models.Model):
    # id = models.BigAutoField(primary_key=True)
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    symptoms = models.CharField(max_length=255, db_column='Symptoms')
    primary_category = models.CharField(
        max_length=255, db_column='Primary Category')
    secondary_category = models.CharField(
        max_length=255, db_column='Secondary Category', blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'symptoms'
        verbose_name_plural = 'Symptoms Category Mapping'

    def __str__(self):
        return self.symptoms


class MedicalCondition(models.Model):
    id = models.BigAutoField(primary_key=True)

    condition = models.CharField(
        max_length=255,
        db_column='Medical Conditions',
        verbose_name="Medical Conditions",
        # blank=True,
        # null=True
    )
    tcm_patterns = models.TextField(
        db_column='TCM Patterns',
        verbose_name="TCM Patterns",
        # blank=True,
        # null=True
    )
    rationale = models.TextField(
        db_column='Rationale',
        verbose_name="Rationale",
        # blank=True,
        # null=True
    )
    primary_category = models.CharField(
        max_length=255,
        db_column='Primary Category',
        verbose_name="Primary Category",
        blank=True,
        null=True
    )
    secondary_category = models.CharField(
        max_length=255,
        db_column='Secondary Category',
        verbose_name="Secondary Category",
        blank=True,
        null=True
    )
    tertiary_category = models.CharField(
        max_length=255,
        db_column='Tertiary Category',
        verbose_name="Tertiary Category",
        blank=True,
        null=True
    )

    class Meta:
        managed = False
        db_table = 'conditions'
        verbose_name = "Medical Conditions Mapping"
        verbose_name_plural = "Medical Conditions Mapping"

    def __str__(self):
        return self.condition


class WBCGlossary(models.Model):
    id = models.BigAutoField(primary_key=True)

    term = models.CharField(
        max_length=255,
        db_column='Term',
        verbose_name="Term",
        # blank=True,
        # null=True
    )
    definition = models.TextField(
        db_column='Definition',
        verbose_name="Definition",
        blank=True,
        null=True
    )
    next_steps = models.TextField(
        db_column='Next Steps',
        verbose_name="Next Steps",
        blank=True,
        null=True
    )

    class Meta:
        managed = False
        db_table = 'wbc_glossary'
        verbose_name = "WBC Glossary"
        verbose_name_plural = "WBC Glossary"

    def __str__(self):
        return self.term


class WBCMatrix(models.Model):
    id = models.BigAutoField(primary_key=True)

    # --- CHOICES DEFINITIONS (With Custom "Select" Placeholders) ---

    LEVEL_CHOICES = [
        (None, 'Select Level'),  # <--- Replaces "--------"
        ('Low', 'Low'),
        ('High', 'High'),
        ('Normal', 'Normal'),
        ('Below Optimal', 'Below Optimal'),
        ('Above Optimal', 'Above Optimal'),
    ]

    RISK_LEVEL_CHOICES = [
        (None, 'Select Risk Level'),  # <--- Replaces "--------"
        ('Very High', 'Very High'),
        ('High', 'High'),
        ('Moderate–High', 'Moderate–High'),
        ('Moderate', 'Moderate'),
        ('Low', 'Low'),
    ]

    CONFIDENCE_CHOICES = [
        (None, 'Select Confidence'),  # <--- Replaces "--------"
        ('High', 'High'),
        ('Moderate–High', 'Moderate–High'),
        ('Moderate', 'Moderate'),
        ('Low', 'Low'),
        ('Conditional', 'Conditional'),
    ]

    # --- FIELDS ---

    # Blood Marker Levels
    wbc = models.CharField(
        max_length=50,
        db_column='WBC',
        verbose_name="WBC",
        choices=LEVEL_CHOICES,
        blank=True,
        null=True
    )
    neutrophils = models.CharField(
        max_length=50,
        db_column='Neutrophils',
        verbose_name="Neutrophils",
        choices=LEVEL_CHOICES,
        blank=True,
        null=True
    )
    lymphocytes = models.CharField(
        max_length=50,
        db_column='Lymphocytes',
        verbose_name="Lymphocytes",
        choices=LEVEL_CHOICES,
        blank=True,
        null=True
    )
    monocytes = models.CharField(
        max_length=50,
        db_column='Monocytes',
        verbose_name="Monocytes",
        choices=LEVEL_CHOICES,
        blank=True,
        null=True
    )
    eosinophils = models.CharField(
        max_length=50,
        db_column='Eosinophils',
        verbose_name="Eosinophils",
        choices=LEVEL_CHOICES,
        blank=True,
        null=True
    )
    basophils = models.CharField(
        max_length=50,
        db_column='Basophils',
        verbose_name="Basophils",
        choices=LEVEL_CHOICES,
        blank=True,
        null=True
    )

    # Interpretations & Levels
    primary_int = models.TextField(
        db_column='Primary_Int', verbose_name="Primary Interpretation", blank=True, null=True)
    secondary = models.TextField(
        db_column='Secondary', verbose_name="Secondary", blank=True, null=True)
    tertiary = models.TextField(
        db_column='Tertiary', verbose_name="Tertiary", blank=True, null=True)
    quaternary = models.TextField(
        db_column='Quaternary', verbose_name="Quaternary", blank=True, null=True)
    quinary = models.TextField(
        db_column='Quinary', verbose_name="Quinary", blank=True, null=True)

    # Analysis Details
    other_considerations = models.TextField(
        db_column='Other Considerations', verbose_name="Other Considerations", blank=True, null=True)

    risk_score = models.IntegerField(
        db_column='Risk Score', verbose_name="Risk Score", blank=True, null=True)

    risk_level = models.CharField(
        max_length=100,
        db_column='Risk Level',
        verbose_name="Risk Level",
        choices=RISK_LEVEL_CHOICES,  # <--- Added Selector
        blank=True,
        null=True
    )

    risk_definition = models.TextField(
        db_column='Risk Definition', verbose_name="Risk Definition", blank=True, null=True)

    confidence = models.CharField(
        max_length=50,
        db_column='Confidence',
        verbose_name="Confidence",
        choices=CONFIDENCE_CHOICES,  # <--- Added Selector
        blank=True,
        null=True
    )

    rationale = models.TextField(
        db_column='Rationale', verbose_name="Rationale", blank=True, null=True)
    clinical_guidance = models.TextField(
        db_column='Clinical Guidance', verbose_name="Clinical Guidance", blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'wbc_matrix'
        verbose_name = "WBC Matrix"
        verbose_name_plural = "WBC Matrix"

    def __str__(self):
        return self.wbc or "WBC Matrix Entry"


class MedicationList(models.Model):
    id = models.BigAutoField(primary_key=True)

    category = models.CharField(
        max_length=255,
        db_column='Category',
        verbose_name="Category",
        # blank=True,
        # null=True
    )
    sub_category = models.CharField(
        max_length=255,
        db_column='Sub category',
        verbose_name="Sub category",
        blank=True,
        null=True
    )
    example_medications = models.TextField(
        db_column='Example Medications',
        verbose_name="Example Medications",
        blank=True,
        null=True
    )
    do_not_effect = models.TextField(
        db_column='Do not effect blood markers',
        verbose_name="Do not effect blood markers",
        blank=True,
        null=True
    )
    tcm_narrative_no_effect = models.TextField(
        db_column='TCM Narrative - Do not effect blood markers',
        verbose_name="TCM Narrative - Do not effect blood markers",
        blank=True,
        null=True
    )

    class Meta:
        managed = False
        db_table = 'medications_list'
        verbose_name = "Medications List"
        verbose_name_plural = "Medications List"
    # ADD THIS:

    def __str__(self):
        return self.category


class MedicationMapping(models.Model):
    id = models.BigAutoField(primary_key=True)

    panel = models.CharField(
        max_length=255,
        db_column='Panel (A)',
        verbose_name="Panel (A)",
        # blank=True,
        # null=True
    )
    marker = models.CharField(
        max_length=255,
        db_column='Marker (B)',
        verbose_name="Marker (B)",
        blank=True,
        null=True
    )
    med_types_low = models.TextField(
        db_column='↓ Medication types (C)',
        verbose_name="↓ Medication types (C)",
        blank=True,
        null=True
    )
    # magnitude_low = models.IntegerField(
    #     db_column='Magnitude for ↓ types (1–3)',
    #     verbose_name="Magnitude for ↓ types (1–3)",
    #     blank=True,
    #     null=True
    # )

    med_types_high = models.TextField(
        db_column='↑ Medication types (D)',
        verbose_name="↑ Medication types (D)",
        blank=True,
        null=True
    )

# 1. Add db_column to map 'magnitude_low' to the actual DB column 'Magnitude for ↓ types (1–3)'
    magnitude_low = models.CharField(
        max_length=50,
        db_column='Magnitude for ↓ types (1–3)',  # <--- CRITICAL RESTORATION
        verbose_name="Magnitude for ↓ types (1–3)",
        blank=True,
        null=True
    )

    # 2. Add db_column to map 'magnitude_high' to the actual DB column 'Magnitude for ↑ types (1–3)'
    magnitude_high = models.CharField(
        max_length=50,
        db_column='Magnitude for ↑ types (1–3)',  # <--- CRITICAL RESTORATION
        verbose_name="Magnitude for ↑ types (1–3)",
        blank=True,
        null=True
    )

    # magnitude_high = models.IntegerField(
    #     db_column='Magnitude for ↑ types (1–3)',
    #     verbose_name="Magnitude for ↑ types (1–3)",
    #     blank=True,
    #     null=True
    # )
    narrative_low = models.TextField(
        db_column='Narrative – how ↓ meds lower/mask (E)',
        verbose_name="Narrative – how ↓ meds lower/mask (E)",
        blank=True,
        null=True
    )
    narrative_high = models.TextField(
        db_column='Narrative – how ↑ meds raise/mask (F)',
        verbose_name="Narrative – how ↑ meds raise/mask (F)",
        blank=True,
        null=True
    )
    tcm_narrative_low = models.TextField(
        db_column='TCM narrative – for ↓ meds (from C)',
        verbose_name="TCM narrative – for ↓ meds (from C)",
        blank=True,
        null=True
    )
    tcm_narrative_high = models.TextField(
        db_column='TCM narrative – for ↑ meds (from E)',
        verbose_name="TCM narrative – for ↑ meds (from E)",
        blank=True,
        null=True
    )

    class Meta:
        managed = False
        db_table = 'medications_mapping'
        verbose_name = "Medications Mapping"
        verbose_name_plural = "Medications Mapping"
    # ADD THIS:

    def __str__(self):
        return self.panel or "Unnamed Mapping"


class MedicationScoreDef(models.Model):
    id = models.BigAutoField(primary_key=True)
    score = models.IntegerField(db_column='Score')
    definition = models.TextField(
        db_column='Working definition', blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'medications_score_definitions'
        verbose_name_plural = 'Medications Score Definitions'
    # ADD THIS:

    def __str__(self):
        return str(self.score)  # <--- Added str()


class SupplementList(models.Model):
    id = models.BigAutoField(primary_key=True)

    category = models.CharField(
        max_length=255,
        db_column='Category',
        verbose_name="Category",
        # blank=True,
        # null=True
    )
    sub_category = models.CharField(
        max_length=255,
        db_column='Sub category',
        verbose_name="Sub category",
        blank=True,
        null=True
    )
    example_supplements = models.TextField(
        db_column='Example Supplements',
        verbose_name="Example Supplements",
        blank=True,
        null=True
    )
    normal_narrative = models.TextField(
        db_column='Normal Narrative - Do not mask/skew blood markers',
        verbose_name="Normal Narrative - Do not mask/skew blood markers",
        blank=True,
        null=True
    )
    tcm_narrative = models.TextField(
        db_column='TCM Narrative - Do not mask/skew blood markers',
        verbose_name="TCM Narrative - Do not mask/skew blood markers",
        blank=True,
        null=True
    )

    class Meta:
        managed = False
        db_table = 'supplements_list'
        verbose_name = "Supplements List"
        verbose_name_plural = "Supplements List"
    # ADD THIS:

    def __str__(self):
        return self.category


class SupplementMapping(models.Model):
    id = models.BigAutoField(primary_key=True)

    panel = models.CharField(
        max_length=255,
        db_column='Panel',
        verbose_name="Panel",
        # blank=True, null=True
    )
    marker = models.CharField(
        max_length=255,
        db_column='Marker',
        verbose_name="Marker",
        blank=True, null=True
    )

# --- Low Types & Magnitude ---
    supp_types_low = models.TextField(
        db_column='↓ Supplement types',
        verbose_name="↓ Supplement types",
        blank=True, null=True
    )
    # CHANGED: IntegerField -> CharField to support "1; 2; 3" string format
    magnitude_low = models.CharField(
        max_length=50,
        db_column='Magnitude for ↓ types (1–3)',
        verbose_name="Magnitude for ↓ types (1–3)",
        blank=True, null=True
    )

    # --- High Types & Magnitude ---
    supp_types_high = models.TextField(
        db_column='↑ Supplement types',
        verbose_name="↑ Supplement types",
        blank=True, null=True
    )
    # CHANGED: IntegerField -> CharField to support "1; 2; 3" string format
    magnitude_high = models.CharField(
        max_length=50,
        db_column='Magnitude for ↑ types (1–3)',
        verbose_name="Magnitude for ↑ types (1–3)",
        blank=True, null=True
    )

    # Narratives (Low/High)
    narrative_low = models.TextField(
        db_column='Narrative – how ↓ supplements lower/mask',
        verbose_name="Narrative – how ↓ supplements lower/mask",
        blank=True, null=True
    )
    narrative_high = models.TextField(
        db_column='Narrative – how ↑ supplements raise/mask',
        verbose_name="Narrative – how ↑ supplements raise/mask",
        blank=True, null=True
    )

    # TCM Narratives
    tcm_narrative_low = models.TextField(
        db_column='TCM narrative – for ↓ supplements',
        verbose_name="TCM narrative – for ↓ supplements",
        blank=True, null=True
    )
    tcm_narrative_high = models.TextField(
        db_column='TCM narrative – for ↑ supplements',
        verbose_name="TCM narrative – for ↑ supplements",
        blank=True, null=True
    )

    # Mechanisms & Notes
    mechanism_low = models.TextField(
        db_column='Mechanism Type ↓',
        verbose_name="Mechanism Type ↓",
        blank=True, null=True
    )
    mechanism_high = models.TextField(
        db_column='Mechanism Type ↑',
        verbose_name="Mechanism Type ↑",
        blank=True, null=True
    )
    interp_note_low = models.TextField(
        db_column='Interpretation Note ↓',
        verbose_name="Interpretation Note ↓",
        blank=True, null=True
    )
    interp_note_high = models.TextField(
        db_column='Interpretation Note ↑',
        verbose_name="Interpretation Note ↑",
        blank=True, null=True
    )

    class Meta:
        managed = False
        db_table = 'supplements_mapping'
        verbose_name = "Supplements Mapping"
        verbose_name_plural = "Supplements Mapping"
    # ADD THIS:

    def __str__(self):
        return self.panel


class SupplementScoreDef(models.Model):
    id = models.BigAutoField(primary_key=True)
    score = models.IntegerField(db_column='Score')
    definition = models.TextField(
        db_column='Working definition', blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'supplements_score_definitions'
        verbose_name_plural = 'Supplement Score Definitions'
    # ADD THIS:

    def __str__(self):
        return str(self.score)


class LifestyleQuestionnaire(models.Model):
    id = models.BigAutoField(primary_key=True)

    question_number = models.CharField(
        max_length=50,
        db_column='Question Number',
        verbose_name="Question Number",
        # blank=True,
        # null=True
    )
    question = models.TextField(
        db_column='Question',
        verbose_name="Question",
        blank=True,
        null=True
    )
    answer_option = models.CharField(
        max_length=255,
        db_column='Answer Option',
        verbose_name="Answer Option",
        blank=True,
        null=True
    )
    sub_answer = models.CharField(
        max_length=255,
        db_column='Sub Answer',
        verbose_name="Sub Answer",
        blank=True,
        null=True
    )
    func_perspective = models.TextField(
        db_column='Functional Medicine Perspective',
        verbose_name="Functional Medicine Perspective",
        blank=True,
        null=True
    )
    tcm_perspective = models.TextField(
        db_column='TCM Perspective',
        verbose_name="TCM Perspective",
        blank=True,
        null=True
    )

    class Meta:
        managed = False
        db_table = 'lifestyle_questionnaire'
        verbose_name = "Lifestyle & Dietary Questionnaire"
        verbose_name_plural = "Lifestyle & Dietary Questionnaire"
    # ADD THIS:

# REPLACE THE OLD __str__ WITH THIS:
    def __str__(self):
        if self.question_number:
            return str(self.question_number)
        return "No Question Number"


class TCMBodyTypeMapping(models.Model):
    id = models.BigAutoField(primary_key=True)

    tcm_body_type = models.CharField(
        max_length=255,
        db_column='TCM Body Type',
        verbose_name="TCM Body Type",
        # blank=True,
        # null=True
    )
    tcm_explanation = models.TextField(
        db_column='TCM Body Type Explanation',
        verbose_name="TCM Body Type Explanation",
        blank=True,
        null=True
    )
    func_equivalent = models.CharField(
        max_length=255,
        db_column='Functional Medicine Equivalent',
        verbose_name="Functional Medicine Equivalent",
        blank=True,
        null=True
    )
    func_explanation = models.TextField(
        db_column='Functional Medicine Equivalent Explanation',
        verbose_name="Functional Medicine Equivalent Explanation",
        blank=True,
        null=True
    )

    class Meta:
        managed = False
        db_table = 'tcm_body_type_mapping'
        verbose_name = "TCM Body Type Mapping"
        verbose_name_plural = "TCM Body Type Mapping"
    # ADD THIS:

    def __str__(self):
        return self.tcm_body_type or "Unnamed Body Type"


class TCMPathogenDefinition(models.Model):
    id = models.BigAutoField(primary_key=True)
    pathogen = models.CharField(max_length=255, db_column='TCM Pathogen')
    definition = models.TextField(
        db_column='Functional Modern Definition & Explanation', blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'tcm_pathogen_definitions'
        verbose_name_plural = 'TCM Pathogen Definitions'
    # ADD THIS:

    def __str__(self):
        return self.pathogen
