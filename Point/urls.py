from django.urls import path
# from .views import ReadAllPostView, CreatePostView
from .views import PointListView

app_name = 'point'
urlpatterns = [
    path("", PointListView.as_view()),
]