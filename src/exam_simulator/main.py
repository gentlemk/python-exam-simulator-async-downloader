from pathlib import Path
from time import sleep
import traceback

from multiprocessing import Manager, Queue, Process, Event
from multiprocessing.managers import SyncManager

from domain import Student, Examiner, Question
from application.exam import Exam
from application.result_analyzer import ExamResultAnalyzer

from infrastructure.exam_analytics_service import ExamAnalyticsService
from infrastructure.exam_statistics_printer import ExamStatisticsPrinter
from infrastructure.exam_statistics_storage import ExamStatisticsStorage

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"


def main(manager: SyncManager) -> None:
    # достаем данные из файлов
    students, examiners, questions = get_data()

    # создаем очередь студентов
    students_queue = Queue()
    for student in students:
        students_queue.put(student)

    # создаем событие для одновременного старта экзамена
    start_exam = Event()

    # Хранение информации об объектах экзамена
    storage = ExamStatisticsStorage.create(students, examiners, questions, manager)

    # Обработка статистики через специальныe классы
    analytics_service = ExamAnalyticsService(storage)
    result_analyzer = ExamResultAnalyzer(storage)

    processes = []
    for examiner in examiners:
        worker = Exam(
            students_queue,
            examiner,
            questions,
            analytics_service,
            start_exam,
        )
        process = Process(
            target=worker.run_exam,
        )
        process.start()
        processes.append(process)

    printer = ExamStatisticsPrinter()
    ExamStatisticsPrinter.clear_terminal()

    try:
        time_start_exam()
        analytics_service.start_time_exam()
        start_exam.set()
        print("Экзамен начался")
        sleep(0.5)

        ExamStatisticsPrinter.clear_terminal()
        while any(p.is_alive() for p in processes):
            for p in processes:
                if not p.is_alive() and p.exitcode != 0:
                    raise RuntimeError(f"Процесс-экзаменатор завершился с ошибкой (код {p.exitcode}).")

            analytics_service.update_this_time()
            printer.print_state_exam(analytics_service, storage.student_statistics, storage.examination_statistics)

    except Exception as e:
        print(f"\n[КРИТИЧЕСКАЯ ОШИБКА В ГЛАВНОМ ПРОЦЕССЕ]: {e}")
        raise e
    finally:
        for p in processes:
            if p.is_alive():
                p.terminate()
                p.join()

    for process in processes:
        process.join()

    printer.print_finished_state(storage.student_statistics, result_analyzer)


def time_start_exam() -> None:
    for i in range(3, 0, -1):
        print(f"Экзамен начнется через {i}")
        sleep(1)


def get_data() -> tuple[list[Student], list[Examiner], list[Question]]:
    with open(DATA_DIR / "students.txt", "r", encoding="utf-8") as file:
        students = [Student(*line.strip().split()) for line in file if line.strip()]

    with open(DATA_DIR / "examiners.txt", "r", encoding="utf-8") as file:
        examiners = [Examiner(*line.strip().split()) for line in file if line.strip()]

    with open(DATA_DIR / "questions.txt", "r", encoding="utf-8") as file:
        questions = [Question(line.strip()) for line in file if line.strip()]

    return students, examiners, questions


if __name__ == '__main__':
    try:
        with Manager() as man:
            main(man)
    except Exception:
        print('\n--- ПРОГРАММА АВАРИЙНО ЗАВЕРШЕНА ---')
        traceback.print_exc()