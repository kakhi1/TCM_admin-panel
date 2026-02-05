from django.apps import AppConfig


class AiAgentConfig(AppConfig):
    name = 'ui_apps.ai_agent'

    # Internal label (keeps DB tables grouped)
    label = 'zz_ai_agent'

    # TRICK: We add a special "Ideographic Space" (　) at the start.
    # This character (U+3000) sorts AFTER standard letters like 'Z'.
    # This forces "AI Agent" to appear at the bottom of the sidebar.
    verbose_name = '　AI Agent'
