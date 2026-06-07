from django.urls import path

from .views import TenderExtractorView

urlpatterns = [
    path("tender-extractor/", TenderExtractorView.as_view(), name="tender-extractor"),
]
