from pathlib import Path
import aiofiles
import aiohttp
import asyncio
from urllib.parse import urlparse
import prettytable
import os

class ImageDownloader():
    def __init__(self,
            save_dir : Path,
            max_connections : int = 10,
    ):
        self.save_dir = save_dir
        self.semaphore = asyncio.Semaphore(max_connections)

    def validate_url(self,
            url : str
    ) -> str:
        parsed = urlparse(url)

        # проверка на корректный протокол
        if parsed.scheme not in ("http", "https"):
            raise ValueError("Некорректный url")

        # проверка на корректный домен
        if not parsed.netloc:
            raise ValueError("В url отсутствует домен")

        name_file = Path(parsed.path).name

        # проверка на корректное имя файла
        if not name_file:
            raise ValueError("В url отсутствует имя файла")

        # проверка на корректное расширение
        if not Path(name_file).suffix:
            raise ValueError("Нет расширения файла")

        return name_file

    def _get_file_path(self, url : str) -> Path:
        file_name = self.validate_url(url)
        return self.save_dir / file_name

    def _validate_response(self, response : aiohttp.ClientResponse):
        content_type = response.headers.get("content-type", "")
        if not content_type.startswith("image/"):
            raise ValueError("url не указывает на изображение")

    async def _save_file(self,
            response : aiohttp.ClientResponse,
            file_path : Path,
    ):
        async with aiofiles.open(file_path, "wb") as file:
            async for chunk in response.content.iter_chunked(1024):
                await file.write(chunk)


    async def download(self,
            session : aiohttp.ClientSession,
            url : str,
    ):
        try:
            async with self.semaphore:
                result_path_image = self._get_file_path(url)
                async with session.get(url) as response:
                    if response.status != 200:
                        raise ConnectionError(f"Ошибка соединения {response.status}")
                    self._validate_response(response)
                    await self._save_file(response, result_path_image)
            return (url, "Успех")
        except Exception as e:
            print(e)
            return (url, "Ошибка")


async def run_downloader(save_dir : Path):
    downloader = ImageDownloader(save_dir)
    async with aiohttp.ClientSession(timeout = aiohttp.ClientTimeout(10)) as session:
        tasks = []

        while True:
            url = await asyncio.to_thread(input, "Введите ссылку на изображение: ")
            url = url.strip()
            if not url:
                break

            task = asyncio.create_task(downloader.download(session, url))
            tasks.append(task)

        results = await asyncio.gather(*tasks, return_exceptions=True)

        if not results:
            print("\n\nНет загрузок для отображения.\n\n")
            return

        table = prettytable.PrettyTable(["Ссылка", "Статус"])
        for result in results:
            table.add_row([result[0], result[1]])
        table.align = "l"
        table.max_width = 100
        print(table)


def get_path_images_save(prompt = "Введите путь для сохранения изображений: ") -> Path:
    while True:
        try:
            user_path = input(prompt).strip()
            if not user_path:
                raise ValueError("Путь не может быть пустым")
            base_path = Path(user_path)
            if base_path.suffix:
                raise ValueError("Путь не может быть с файловым расширением")
            # parents - создаст родительские директории
            # exist_ok - не будет ошибки если директория уже создана
            base_path.mkdir(parents=True, exist_ok=True)
            if not base_path.is_dir():
                raise ValueError("Это не директория")

            if not os.access(base_path, os.W_OK):
                raise PermissionError("Нет прав на запись в эту директорию")
            return base_path
        except PermissionError:
            print("Ошибка: Недостаточно прав для создания директории")
        except ValueError as e:
            print(f"Ошибка ввода: {e}")
        except Exception as e:
            print(e)

async def main():
    save_dir = get_path_images_save()
    await run_downloader(save_dir)


if __name__ == '__main__':
    asyncio.run(main())