from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status

import time
import math
import requests
from concurrent import futures

# Куда шлём результат в Go
GO_SERVICE_URL = "http://localhost:8080/api/readindxs/update-calc"

AUTH_TOKEN = "secret12"

executor = futures.ThreadPoolExecutor(max_workers=4)


def calc_readability(words: int, sentences: int, syllables: int) -> int:
    """
    Полный аналог твоей calcFlesch на Go.
    """
    if words <= 0 or sentences <= 0:
        return 0

    fre = 206.835 - 1.015 * (words / sentences) - 84.6 * (syllables / words)
    if fre < 0:
        fre = 0
    if fre > 206.835:
        fre = 206.835

    return int(round(fre))


def calculate_logic(data: dict) -> None:
    """
    Асинхронная часть: ждём, считаем индекс, отправляем в Go.
    Ожидаемый data:
    {
      "read_indxs_id": 10,
      "text_id": 5,
      "count_words": 180,
      "count_sentences": 12,
      "count_syllables": 260
    }
    """
    try:
        print(f"[TxtMetricAsync] received data: {data}")

        # имитация долгой операции
        time.sleep(7)

        words = int(data.get("count_words", 0) or 0)
        sentences = int(data.get("count_sentences", 0) or 0)
        syllables = int(data.get("count_syllables", 0) or 0)

        calculation = calc_readability(words, sentences, syllables)
        print(f"[TxtMetricAsync] calculation data: {calculation}")

        result_payload = {
            "read_indxs_id": data.get("read_indxs_id"),
            "text_id": data.get("text_id"),
            "calculation": calculation,
        }

        headers = {
            "Content-Type": "application/json",
            "Authorization": AUTH_TOKEN,
        }

        print(f"[TxtMetricAsync] sending to Go: {result_payload}")
        resp = requests.put(
            GO_SERVICE_URL,
            json=result_payload,
            headers=headers,
            timeout=5,
        )
        print(f"[TxtMetricAsync] Go response: {resp.status_code} {resp.text}")

    except Exception as e:
        print(f"[TxtMetricAsync] error in calculate_logic: {e}")


@api_view(["POST"])
def perform_calculation(request):
    """
    Входной метод для Go: запускает асинхронный расчёт и сразу возвращает 200.
    """
    try:
        data = request.data

        required = [
            "read_indxs_id",
            "text_id",
            "count_words",
            "count_sentences",
            "count_syllables",
        ]
        missing = [f for f in required if f not in data]
        if missing:
            return Response(
                {"error": f"Missing fields: {', '.join(missing)}"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # передаём копию словаря в пул
        executor.submit(calculate_logic, dict(data))

        return Response({"message": "TxtMetric calculation started"}, status=status.HTTP_200_OK)

    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
