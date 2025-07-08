from httpx import Response


def get_message(response: Response):
    return response.json()["message"]
