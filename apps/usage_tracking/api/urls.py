from django.urls import path

from .views import APIUsageListView, LLMCallLogListView

urlpatterns = [
    path("usage/", APIUsageListView.as_view(), name="usage-list"),
    path("usage/llm-calls/", LLMCallLogListView.as_view(), name="llm-call-logs"),
]
