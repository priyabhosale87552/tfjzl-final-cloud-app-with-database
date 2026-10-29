import uuid

from django.db import transaction
from django.http import Http404, HttpResponseBadRequest
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from .models import Choice, Course, Question, Submission


def course_details(request, course_id):
    course = get_object_or_404(
        Course.objects.prefetch_related("lessons__questions__choices"),
        pk=course_id,
    )
    questions = [
        question
        for lesson in course.lessons.all()
        for question in lesson.questions.all()
    ]
    return render(
        request,
        "onlinecourse/course_details_bootstrap.html",
        {"course": course, "questions": questions},
    )


@require_POST
def submit(request, course_id):
    course = get_object_or_404(Course, pk=course_id)
    questions = list(
        Question.objects.filter(lesson__course=course).order_by("lesson__order", "order", "id")
    )
    if not questions:
        return HttpResponseBadRequest("This course does not have any exam questions.")

    answers = {}
    for question in questions:
        choice_id = request.POST.get(f"question_{question.pk}")
        if not choice_id:
            answers[question.pk] = None
            continue
        try:
            choice = Choice.objects.get(pk=choice_id, question=question)
        except (Choice.DoesNotExist, ValueError):
            return HttpResponseBadRequest("One or more selected answers are invalid.")
        answers[question.pk] = choice

    attempt_id = uuid.uuid4()
    with transaction.atomic():
        Submission.objects.bulk_create(
            [
                Submission(
                    attempt_id=attempt_id,
                    user=request.user if request.user.is_authenticated else None,
                    question=question,
                    selected_choice=answers[question.pk],
                )
                for question in questions
            ]
        )
    return redirect("show_exam_result", attempt_id=attempt_id)


def show_exam_result(request, attempt_id):
    try:
        attempt_id = uuid.UUID(str(attempt_id))
    except ValueError as exc:
        raise Http404("Exam attempt not found.") from exc

    submissions = list(
        Submission.objects.filter(attempt_id=attempt_id)
        .select_related("question__lesson", "selected_choice")
        .order_by("question__lesson__order", "question__order", "question_id")
    )
    if not submissions:
        raise Http404("Exam attempt not found.")

    total = len(submissions)
    correct = sum(
        1
        for submission in submissions
        if submission.selected_choice and submission.selected_choice.is_correct
    )
    score = round(correct * 100 / total)
    return render(
        request,
        "onlinecourse/exam_result.html",
        {
            "submissions": submissions,
            "correct": correct,
            "total": total,
            "score": score,
            "passed": score >= 70,
        },
    )
