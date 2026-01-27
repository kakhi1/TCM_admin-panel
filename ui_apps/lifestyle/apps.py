# from django.apps import AppConfig


# class LifestyleConfig(AppConfig):
#     name = 'ui_apps.lifestyle'
#     label = 'ui_lifestyle'
#     verbose_name = 'Lifestyle & Dietary Questionnaire'
from django.apps import AppConfig


class LifestyleConfig(AppConfig):
    name = 'ui_apps.lifestyle'
    label = 'ui_lifestyle'
    # Adding an invisible space (\u200b) forces this to sort AFTER standard text (A-Z)
    verbose_name = '\u200bLifestyle & Dietary Questionnaire'
