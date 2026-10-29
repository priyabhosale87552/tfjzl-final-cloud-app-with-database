# Online Course Assessment

A Django project for a course application with lesson content, admin-managed exam questions and choices, and scored assessment attempts.

## Run locally

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

Open `/admin/` to add courses, lessons, questions, and answer choices. Open `/courses/<course-id>/` to view a course and take its assessment.

## Verify

```powershell
python manage.py test
```

## Assignment evidence

The requested source files are `onlinecourse/models.py`, `onlinecourse/admin.py`, `onlinecourse/templates/onlinecourse/course_details_bootstrap.html`, `onlinecourse/views.py`, and `onlinecourse/urls.py`. Publish this folder to GitHub to submit file URLs. Capture the admin homepage as `03-admin-site.png` and a passing assessment page as `07-final.png` after creating course content and completing the exam.

The project intentionally does not include fabricated screenshots or a GitHub URL; capture and publish those from your own running instance and repository.
