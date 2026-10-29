from django.urls import path

from . import views


urlpatterns = [
    path("courses/<int:course_id>/", views.course_details, name="course_details"),
    path("courses/<int:course_id>/submit/", views.submit, name="submit"),
    path("exam-results/<uuid:attempt_id>/", views.show_exam_result, name="show_exam_result"),
]
