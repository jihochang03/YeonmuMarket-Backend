from django.apps import AppConfig

class ConversationConfig(AppConfig):
    name = 'conversations'

    def ready(self):
        import conversations.signals  # 신호 연결