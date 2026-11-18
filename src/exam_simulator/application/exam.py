from random import sample
from time import perf_counter, sleep
from domain import Student, Examiner, Question
from multiprocessing import Queue
from infrastructure.exam_analytics_service import ExamAnalyticsService
from multiprocessing.synchronize import Event
from queue import Empty

_MAX_EXAM_QUESTIONS = 3
_MIN_TIME_WORK_FOR_LUNCH = 30

class Exam:
    def __init__(
            self,
            students_queue: Queue,
            examiner: Examiner,
            questions: list[Question],
            analytics_service: ExamAnalyticsService,
            start_exam_event : Event,
    ) -> None:
        self.students_queue = students_queue
        self.examiner = examiner
        self.questions = questions
        self.analytics_service = analytics_service
        self.start_exam_event = start_exam_event
        self.exam_questions: list[Question] = []

    def run_exam(self) -> None:
        self.wait_for_start()
        self.choose_questions()
        self.process_exam_students()
        self.finished_exam()

    def finished_exam(self) -> None:
        """
        Завершить экзамен, обновить статистику
        """
        this_time = self.analytics_service.get_this_time()
        self.analytics_service.finished_examiner(self.examiner.id)
        self.analytics_service.set_end_time_exam(this_time)
        self.analytics_service.change_exam_time_examiner(self.examiner.id, this_time)
        self.analytics_service.change_current_student_for_examiner(self.examiner.id)

    def wait_for_start(self) -> None:
        """Ожидаем старта экзамена из главного процесса"""
        self.start_exam_event.wait()

    def choose_questions(self) -> list[Question]:
        """
        Случайно выбираем 3 вопроса или меньше из списка вопросов
        """
        count_questions = min(_MAX_EXAM_QUESTIONS, len(self.questions))
        self.exam_questions = sample(self.questions, count_questions)
        return self.exam_questions

    def process_exam_students(self) -> None:
        """
        Функция обработки студентов из очереди
        """
        while True:
            student = self.get_next_student()
            if not student:
                break
            self.take_student_exam(student)
            self.process_exam_lunch()

    def process_exam_lunch(self) -> None:
        """
        Функция обработки обеда экзаменатора
        """
        if self.is_need_lunch():
            # для демонстрации обеда
            # self.analytics_service.change_current_student_for_examiner(self.examiner.id, "На обеде")
            self.analytics_service.change_current_student_for_examiner(self.examiner.id)
            self.examiner.is_had_lunch = True
            time_lunch = self.examiner.get_time_lunch()
            sleep(time_lunch)

    def is_need_lunch(self) -> bool:
        """
        Проверяет, нужно ли экзаменатору уходить на обед
        """
        time_exam = perf_counter() - self.analytics_service.get_time_start_exam()
        return (time_exam > _MIN_TIME_WORK_FOR_LUNCH
                and not self.examiner.is_had_lunch
                and self.analytics_service.get_count_students_in_queue() > 0)

    def take_student_exam(self, student: Student) -> None:
        """
        Функция обработки экзамена у студента
        """
        start_time_answer = perf_counter()
        self.analytics_service.add_count_served_student(self.examiner.id)
        self.analytics_service.change_current_student_for_examiner(self.examiner.id, student.name)
        count_correct_answers = 0
        count_fail_answers = 0
        for question in self.exam_questions:
            self.analytics_service.set_total_answer_question(question.id)
            if Exam._checking_answers_student_and_examiner(student, self.examiner, question):
                self.analytics_service.set_correct_answer_question(question.id)
                count_correct_answers += 1
            else:
                count_fail_answers += 1
        self.simulate()
        self.get_result_exam(student, count_correct_answers, count_fail_answers)
        end_time_answer = perf_counter()
        self.analytics_service.set_time_exam_student(student.id, start_time_answer, end_time_answer)


    @staticmethod
    def _checking_answers_student_and_examiner(
            student: Student,
            examiner: Examiner,
            question: Question,
    ) -> bool:
        """Сверяет, входит ли ответ студента в список ответов преподавателя"""
        answer_student = student.get_answer(question)
        answers_examiner = examiner.get_answers(question)
        return answer_student in answers_examiner

    def get_next_student(self) -> Student | None:
        """
        Получить студента из очереди. Если отсутствует - получить None
        """
        try:
            return self.students_queue.get(timeout=1)
        except Empty:
            return None

    def get_result_exam(
            self,
            student : Student,
            count_correct_answers : int,
            count_fail_answers : int,
    ) -> bool:
        """
        Принимает ответ студента в зависимости от настроения экзаменатора
        """
        if self.examiner.mood == self.examiner.Mood.GOOD:
            self.process_good_mood_examiner(student)
            return True
        elif self.examiner.mood == self.examiner.Mood.BAD:
            self.process_bad_mood_examiner(student)
            return False
        else:
            return self.process_neutral_mood_examiner(student, count_correct_answers, count_fail_answers)

    def process_good_mood_examiner(self, student : Student) -> None:
        """
        Принимаем результаты экзамена если у преподавателя хорошее настроение
        """
        self.analytics_service.change_status_student(student.id, Student.Status.PASSED)

    def process_bad_mood_examiner(self, student : Student) -> None:
        """
        Принимаем результаты экзамена если у преподавателя плохое настроение
        """
        self.analytics_service.change_status_student(student.id, Student.Status.FAILED)
        self.analytics_service.add_count_failed_student(self.examiner.id)

    def process_neutral_mood_examiner(
            self,
            student : Student,
            count_correct_answers : int,
            count_fail_answers : int,
    ) -> bool:
        """
        Принимаем результаты экзамена если у преподавателя нейтральное настроение
        Экзамен сдан, если правильных ответов больше, чем неправильных
        """
        if count_correct_answers > count_fail_answers:
            self.analytics_service.change_status_student(student.id, Student.Status.PASSED)
            return True
        else:
            self.analytics_service.change_status_student(student.id, Student.Status.FAILED)
            self.analytics_service.add_count_failed_student(self.examiner.id)
            return False

    def simulate(self) -> None:
        """Имитация сдачи экзамена"""
        sleep(self.examiner.get_time_exam())





