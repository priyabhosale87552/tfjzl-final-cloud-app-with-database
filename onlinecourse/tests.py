from django.test import TestCase
from django.urls import reverse

from .models import Choice, Course, Lesson, Question, Submission


class ExamFlowTests(TestCase):
    def setUp(self):
        self.course = Course.objects.create(name="Django fundamentals")
        lesson = Lesson.objects.create(course=self.course, title="Models")
        self.question = Question.objects.create(lesson=lesson, prompt="What does ORM mean?")
        self.correct = Choice.objects.create(
            question=self.question,
            text="Object-relational mapper",
            is_correct=True,
        )
        Choice.objects.create(question=self.question, text="Online reading mode")

    def test_submit_creates_attempt_and_displays_passing_result(self):
        response = self.client.post(
            reverse("submit", args=(self.course.pk,)),
            {f"question_{self.question.pk}": self.correct.pk},
        )

        self.assertRedirects(response, f"/exam-results/{Submission.objects.get().attempt_id}/")
        result = self.client.get(response.url)
        self.assertContains(result, "Congratulations!")
        self.assertContains(result, "Score:")
        self.assertContains(result, "100%")
        self.assertContains(result, "Object-relational mapper")

    def test_submit_rejects_a_choice_from_another_question(self):
        other_question = Question.objects.create(
            lesson=self.question.lesson,
            prompt="A different question?",
        )
        other_choice = Choice.objects.create(
            question=other_question,
            text="Unrelated answer",
            is_correct=True,
        )

        response = self.client.post(
            reverse("submit", args=(self.course.pk,)),
            {f"question_{self.question.pk}": other_choice.pk},
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(Submission.objects.count(), 0)

    def test_course_page_shows_course_lessons_and_exam(self):
        response = self.client.get(reverse("course_details", args=(self.course.pk,)))

        self.assertContains(response, "Django fundamentals")
        self.assertContains(response, "Models")
        self.assertContains(response, "What does ORM mean?")

    def test_submit_requires_post(self):
        response = self.client.get(reverse("submit", args=(self.course.pk,)))

        self.assertEqual(response.status_code, 405)

    def test_anonymous_attempt_does_not_require_a_user(self):
        response = self.client.post(
            reverse("submit", args=(self.course.pk,)),
            {f"question_{self.question.pk}": self.correct.pk},
        )

        self.assertEqual(response.status_code, 302)
        self.assertIsNone(Submission.objects.get().user)
