from django.test import TestCase
from django.urls import reverse

from django.contrib import admin

from .models import Choice, Course, Learner, Lesson, Question, Submission


class ExamFlowTests(TestCase):
    def setUp(self):
        self.course = Course.objects.create(name="Django fundamentals")
        lesson = Lesson.objects.create(course=self.course, title="Models")
        self.question = Question.objects.create(
            course=self.course,
            lesson=lesson,
            question_text="What does ORM mean?",
        )
        self.correct = Choice.objects.create(
            question=self.question,
            choice_text="Object-relational mapper",
            is_correct=True,
        )
        Choice.objects.create(question=self.question, choice_text="Online reading mode")

    def test_submit_creates_attempt_and_displays_passing_result(self):
        response = self.client.post(
            reverse("submit", args=(self.course.pk,)),
            {f"question_{self.question.pk}": [str(self.correct.pk)]},
        )

        self.assertRedirects(response, f"/exam-results/{Submission.objects.get().attempt_id}/")
        result = self.client.get(response.url)
        self.assertContains(result, "Congratulations!")
        self.assertContains(result, "Score:")
        self.assertContains(result, "100%")
        self.assertContains(result, "Object-relational mapper")
        submission = Submission.objects.get()
        self.assertEqual(submission.enrollment.course, self.course)
        self.assertEqual(list(submission.choices.all()), [self.correct])

    def test_submit_rejects_a_choice_from_another_question(self):
        other_question = Question.objects.create(
            course=self.course,
            lesson=self.question.lesson,
            question_text="A different question?",
        )
        other_choice = Choice.objects.create(
            question=other_question,
            choice_text="Unrelated answer",
            is_correct=True,
        )

        response = self.client.post(
            reverse("submit", args=(self.course.pk,)),
            {f"question_{self.question.pk}": [str(other_choice.pk)]},
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
            {f"question_{self.question.pk}": [str(self.correct.pk)]},
        )

        self.assertEqual(response.status_code, 302)
        self.assertIsNone(Submission.objects.get().user)

    def test_question_scoring_requires_exact_correct_choices(self):
        self.assertTrue(self.question.is_get_score([self.correct.pk]))
        self.assertFalse(self.question.is_get_score([]))
        self.assertFalse(
            self.question.is_get_score(
                [self.correct.pk, self.question.choices.get(choice_text="Online reading mode").pk]
            )
        )
        self.assertEqual(str(self.question), "What does ORM mean?")
        self.assertEqual(str(self.correct), "Object-relational mapper")

    def test_multiple_correct_choices_are_scored_as_a_set(self):
        second_correct = Choice.objects.create(
            question=self.question,
            choice_text="A related database mapper",
            is_correct=True,
        )

        self.assertTrue(self.question.is_get_score([self.correct.pk, second_correct.pk]))

    def test_submission_string_includes_its_enrollment(self):
        response = self.client.post(
            reverse("submit", args=(self.course.pk,)),
            {f"question_{self.question.pk}": [str(self.correct.pk)]},
        )
        self.assertEqual(response.status_code, 302)
        submission = Submission.objects.get()

        self.assertEqual(
            str(submission),
            f"Submission {submission.pk} for enrollment {submission.enrollment_id}",
        )


class AdminRegistrationTests(TestCase):
    def test_rubric_models_are_registered(self):
        for model in (Choice, Course, Learner, Lesson, Question, Submission):
            with self.subTest(model=model.__name__):
                self.assertIn(model, admin.site._registry)
