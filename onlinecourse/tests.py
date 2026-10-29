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

        submission = Submission.objects.get()
        self.assertRedirects(
            response,
            f"/exam-results/{self.course.pk}/{submission.pk}/",
        )
        result = self.client.get(response.url)
        self.assertContains(result, "Congratulations!")
        self.assertContains(result, "Score:")
        self.assertContains(result, "100%")
        self.assertContains(result, "Object-relational mapper")
        self.assertEqual(submission.enrollment.course, self.course)
        self.assertIsNone(submission.question)
        self.assertEqual(list(submission.choices.all()), [self.correct])
        self.assertEqual(result.context["q_results"], {self.question.pk: self.question.grade})
        self.assertEqual(result.context["c_submits"][self.correct.pk], True)
        self.assertEqual(result.context["c_results"][self.correct.pk], True)

    def test_result_rejects_submission_from_another_course(self):
        response = self.client.post(
            reverse("submit", args=(self.course.pk,)),
            {f"question_{self.question.pk}": [str(self.correct.pk)]},
        )
        submission = Submission.objects.get()
        other_course = Course.objects.create(name="Different course")

        result = self.client.get(
            reverse("show_exam_result", args=(other_course.pk, submission.pk))
        )

        self.assertEqual(result.status_code, 404)

    def test_result_context_scores_all_course_questions(self):
        second_question = Question.objects.create(
            course=self.course,
            lesson=self.question.lesson,
            question_text="How many points is this question worth?",
            grade=2,
            order=2,
        )
        Choice.objects.create(
            question=second_question,
            choice_text="Two points",
            is_correct=True,
        )
        response = self.client.post(
            reverse("submit", args=(self.course.pk,)),
            {f"question_{self.question.pk}": [str(self.correct.pk)]},
        )

        result = self.client.get(response.url)

        self.assertEqual(result.context["total"], 3)
        self.assertEqual(result.context["total_user"], 1)
        self.assertEqual(result.context["grade"], 33)
        self.assertEqual(result.context["q_results"], {self.question.pk: 1, second_question.pk: 0})

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
        self.assertEqual(list(self.course.lesson_set.all()), [self.question.lesson])

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
