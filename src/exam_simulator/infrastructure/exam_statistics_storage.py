from __future__ import annotations
from domain import Student, Question, Examiner
from multiprocessing.managers import SyncManager, DictProxy, ValueProxy


class ExamStatisticsStorage:
    def __init__(
            self,
            student_statistics: DictProxy,
            examination_statistics: DictProxy,
            question_statistics: DictProxy,
            this_time_ms: ValueProxy,
            exam_start_time_ms: ValueProxy,
            exam_end_time_ms: ValueProxy,
            count_students_in_queue,
            lock,
    ):
        self.student_statistics = student_statistics
        self.examination_statistics = examination_statistics
        self.question_statistics = question_statistics
        self.this_time_ms = this_time_ms
        self.exam_start_time_ms = exam_start_time_ms
        self.exam_end_time_ms = exam_end_time_ms
        self.lock = lock
        self.count_students_in_queue = count_students_in_queue

    @classmethod
    def create(
            cls,
            students: list[Student],
            examiners: list[Examiner],
            questions: list[Question],
            manager: SyncManager,
    ) -> ExamStatisticsStorage:
        lock = manager.Lock()
        student_statistics = cls._init_student_statistics(students, manager)
        examination_statistics = cls._init_examination_statistics(examiners, manager)
        question_statistics = cls._init_questions_statistics(questions, manager)
        count_students_in_queue = manager.Value('i', cls._get_count_students_in_queue(student_statistics))
        this_time_ms = manager.Value('d', 0)
        exam_start_time_ms = manager.Value('d', 0)
        exam_end_time_ms = manager.Value('d', 0)
        return cls(
            student_statistics,
            examination_statistics,
            question_statistics,
            this_time_ms,
            exam_start_time_ms,
            exam_end_time_ms,
            count_students_in_queue,
            lock,
        )


    @staticmethod
    def _init_student_statistics(
            students: list[Student],
            manager: SyncManager,
    ) -> DictProxy:
        """Инициализируем словарь для каждого студента с хранением статистики по каждому студенту"""
        result = manager.dict()
        for student in students:
            result[student.id] = manager.dict(
                {
                    "name" : student.name,
                    "status" : student.status.value,
                    "time_exam" : None,
                    "examiner" : "-",
                }
            )
        return result


    @staticmethod
    def _init_examination_statistics(
            examiners: list[Examiner],
            manager: SyncManager,
    ) -> DictProxy:
        """Инициализируем словарь для каждого экзаменатора с хранением статистики по каждому экзаменатору"""
        result = manager.dict()
        for examiner in examiners:
            result[examiner.id] = manager.dict(
                {
                    "name" : examiner.name,
                    "current_student" : "-",
                    "total_students" : 0,
                    "fail_students" : 0,
                    "time_exam" : 0.0,
                    "is_finished" : False,
                }
            )
        return result


    @staticmethod
    def _init_questions_statistics(
            questions: list[Question],
            manager: SyncManager,
    )-> DictProxy:
        """Инициализируем словарь для каждого вопроса для хранения статистики для каждого вопроса"""
        result = manager.dict()
        for question in questions:
            result[question.id] = manager.dict(
                {
                    "question" : question.text,
                    "total_answers" : 0,
                    "correct_answers" : 0,
                }
            )

        return result

    @staticmethod
    def _get_count_students_in_queue(student_statistics: DictProxy) -> int:
        return sum(1 for student in student_statistics.values() if student["status"] == Student.Status.WAITING.value)
