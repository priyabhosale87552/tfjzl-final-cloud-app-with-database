import uuid

from django.db import transaction
from django.http import Http404, HttpResponseBadRequest
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from .models import Choice, Course, Enrollment, Question, Submission


def course_details(request, course_id):
    course = get_object_or_404(
        Course.objects.prefetch_related("lessons__questions__choices"),
        pk=course_id,
    )
    questions = list(course.questions.prefetch_related("choices").order_by("lesson__order", "order", "id"))
    return render(
        request,
        "onlinecourse/course_details_bootstrap.html",
        {"course": course, "questions": questions},
    )


@require_POST
def submit(request, course_id):
    course = get_object_or_404(Course, pk=course_id)
    questions = list(
        Question.objects.filter(course=course).order_by("lesson__order", "order", "id")
    )
    if not questions:
        return HttpResponseBadRequest("This course does not have any exam questions.")

    answers = {}
    for question in questions:
        choice_ids = request.POST.getlist(f"question_{question.pk}")
        if not choice_ids:
            answers[question.pk] = []
            continue
        try:
            choices = list(Choice.objects.filter(question=question, pk__in=choice_ids))
        except ValueError:
            return HttpResponseBadRequest("One or more selected answers are invalid.")
        if len(choices) != len(set(choice_ids)):
            return HttpResponseBadRequest("One or more selected answers are invalid.")
        answers[question.pk] = choices

    attempt_id = uuid.uuid4()
    with transaction.atomic():
        user = request.user if request.user.is_authenticated else None
        enrollment, _ = Enrollment.objects.get_or_create(user=user, course=course)
        for question in questions:
            submission = Submission.objects.create(
                attempt_id=attempt_id,
                user=user,
                enrollment=enrollment,
                question=question,
                selected_choice=answers[question.pk][0] if answers[question.pk] else None,
            )
            submission.choices.set(answers[question.pk])
    return redirect("show_exam_result", attempt_id=attempt_id)


def show_exam_result(request, attempt_id):
    try:
        attempt_id = uuid.UUID(str(attempt_id))
    except ValueError as exc:
        raise Http404("Exam attempt not found.") from exc

    submissions = list(
        Submission.objects.filter(attempt_id=attempt_id)
        .select_related("question__lesson", "selected_choice", "enrollment__course")
        .prefetch_related("choices")
        .order_by("question__lesson__order", "question__order", "question_id")
    )
    if not submissions:
        raise Http404("Exam attempt not found.")

    submission_by_question = {submission.question_id: submission for submission in submissions}
    questions = Question.objects.filter(
        course=submissions[0].enrollment.course
    ).prefetch_related("choices").order_by("lesson__order", "order", "id")
    results = []
    for question in questions:
        submission = submission_by_question.get(question.pk)
        selected_choices = list(submission.choices.all()) if submission else []
        if not selected_choices and submission and submission.selected_choice_id:
            selected_choices = [submission.selected_choice]
        selected_ids = [choice.pk for choice in selected_choices]
        results.append(
            {
                "question": question,
                "selected_choices": selected_choices,
                "correct_choices": [choice for choice in question.choices.all() if choice.is_correct],
                "is_correct": question.is_get_score(selected_ids),
            }
        )

    total = sum(result["question"].grade for result in results)
    correct = sum(1 for result in results if result["is_correct"])
    earned = sum(
        result["question"].grade
        for result in results
        if result["is_correct"]
    )
    score = round(earned * 100 / total) if total else 0
    return render(
        request,
        "onlinecourse/exam_result.html",
        {
            "results": results,
            "correct": correct,
            "total": total,
            "score": score,
            "passed": score >= 70,
        },
    )
