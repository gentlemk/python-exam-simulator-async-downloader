from domain import Student
from infrastructure.exam_statistics_storage import ExamStatisticsStorage

class ExamResultAnalyzer:
    def __init__(self, storage: ExamStatisticsStorage):
        self.storage = storage

    def get_best_questions(self) -> list[str]:
        with self.storage.lock:
            questions = [dict(q) for q in self.storage.question_statistics.values()]
        if not questions:
            return ["Нет вопросов"]
        answers_count = [(x["question"], x["correct_answers"]) for x in questions]
        max_count_answers = max(q for _, q in answers_count)
        best_questions = [question[0] for question in answers_count if question[1] == max_count_answers]
        return best_questions

    def get_result_exam(self) -> bool:
        with self.storage.lock:
            students = [dict(s) for s in self.storage.student_statistics.values()]
        if not students:
            return False
        passed = sum([1 for s in students if s["status"] == Student.Status.PASSED.value])
        return passed / len(students) * 100 > 85

    def get_name_best_examiner(self) -> list[str]:
        with self.storage.lock:
            examiners = [dict(e) for e in self.storage.examination_statistics.values()]
        percent_fail_students = []
        for examiner in examiners:
            try:
                percent_fail_students.append((examiner["name"], examiner["fail_students"] / examiner["total_students"] * 100))
            except ZeroDivisionError:
                continue
        if not percent_fail_students:
            return ["Нет лучших экзаменаторов"]
        min_p = min(t for _, t in percent_fail_students)
        return [name for name, p in percent_fail_students if p == min_p]

    def get_names_students_who_expelled(self) -> list[str]:
        with self.storage.lock:
            students = [dict(s) for s in self.storage.student_statistics.values()]
        failed_students = [s for s in students if s["status"] == Student.Status.FAILED.value]
        if not failed_students:
            return ["Нет студентов, не сдавших экзамен"]
        rounded_times = [(s["name"], round(s["time_exam"], 1)) for s in failed_students]
        min_time = min(t for _, t in rounded_times)
        expelled_students = [name for name, time in rounded_times if time == min_time]
        return expelled_students

    def get_name_best_students(self) -> list[str]:
        with self.storage.lock:
            students = [dict(s) for s in self.storage.student_statistics.values()]
        passed_students = [s for s in students if s["status"] == Student.Status.PASSED.value]
        if not passed_students:
            return ["Нет студентов, сдавших экзамен"]
        rounded_times = [(s["name"], round(s["time_exam"], 1)) for s in passed_students]
        min_time = min(t for _, t in rounded_times)
        return [name for name, time in rounded_times if time == min_time]

    def get_max_time_work_examiner(self) -> float:
        with self.storage.lock:
            stats = self.storage.examination_statistics.values()
        if not stats:
            return 0.0
        return max(stat["time_exam"] for stat in stats)