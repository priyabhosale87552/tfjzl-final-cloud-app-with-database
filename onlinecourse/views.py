from django.http import HttpResponseBadRequest
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from .models import Choice, Course, Enrollment, Question, Submission


def course_details(request, course_id):
    course = get_object_or_404(
        Course.objects.prefetch_related("lesson_set__questions__choices"),
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

    selected_choices = []
    for question in questions:
        choice_ids = request.POST.getlist(f"question_{question.pk}")
        if not choice_ids:
            continue
        try:
            choices = list(Choice.objects.filter(question=question, pk__in=choice_ids))
        except ValueError:
            return HttpResponseBadRequest("One or more selected answers are invalid.")
        if len(choices) != len(set(choice_ids)):
            return HttpResponseBadRequest("One or more selected answers are invalid.")
        selected_choices.extend(choices)

    user = request.user if request.user.is_authenticated else None
    enrollment, _ = Enrollment.objects.get_or_create(user=user, course=course)
    submission = Submission.objects.create(
        enrollment=enrollment,
        user=user,
    )
    submission.choices.set(selected_choices)
    return redirect("show_exam_result", course_id=course.pk, submission_id=submission.pk)


def show_exam_result(request, course_id, submission_id):
    course = get_object_or_404(Course, pk=course_id)
    submission = get_object_or_404(
        Submission.objects.select_related("enrollment__course").prefetch_related("choices"),
        pk=submission_id,
        enrollment__course=course,
    )
    questions = list(
        course.questions.prefetch_related("choices").order_by("lesson__order", "order", "id")
    )
    selected_ids = set(submission.choices.values_list("id", flat=True))
    results = []
    total = 0
    total_user = 0
    q_results = {}
    c_submits = {}
    c_results = {}
    for question in questions:
        question_choices = list(question.choices.all())
        question_selected_ids = selected_ids.intersection(
            choice.pk for choice in question_choices
        )
        is_correct = question.is_get_score(question_selected_ids)
        question_score = question.grade if is_correct else 0
        q_results[question.pk] = question_score
        total += question.grade
        total_user += question_score
        for choice in question_choices:
            is_selected = choice.pk in question_selected_ids
            c_submits[choice.pk] = is_selected
            c_results[choice.pk] = is_selected == choice.is_correct
        results.append(
            {
                "question": question,
                "selected_choices": [
                    choice for choice in question_choices if choice.pk in question_selected_ids
                ],
                "correct_choices": [choice for choice in question_choices if choice.is_correct],
                "is_correct": is_correct,
            }
        )

    score = int(total_user * 100 / total) if total else 0
    return render(
        request,
        "onlinecourse/exam_result_bootstrap.html",
        {
            "course": course,
            "submission": submission,
            "total": total,
            "total_user": total_user,
            "q_results": q_results,
            "c_submits": c_submits,
            "c_results": c_results,
            "grade": score,
            "results": results,
            "correct": sum(1 for result in results if result["is_correct"]),
            "score": score,
            "passed": score >= 70,
        },
    )
