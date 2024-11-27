from django.urls import path
from .views import (
    TicketPostListView, 
    TicketPostDetailView, 
    TransferListView,
    ReceivedListView
)
from django.conf import settings
from django.conf.urls.static import static

from .views import process_image, post_tweet

app_name = 'tickets'

urlpatterns = [
    path('create/', TicketPostListView.as_view()),
    path('ticketpost/<int:ticket_post_id>/', TicketPostDetailView.as_view()),
    path('transferred/', TransferListView.as_view(), name='transferred-tickets'),
    path('purchased/', ReceivedListView.as_view(), name='received-tickets'),
    path('process_image/', process_image, name='process_image'),
    path('post-tweet/', post_tweet, name='post_tweet')]

# MEDIA_URL로 시작하는 요청을 MEDIA_ROOT에서 찾아 서빙
if settings.DEBUG:  # 개발 환경에서만 활성화
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)