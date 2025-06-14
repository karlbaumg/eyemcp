from loguru import logger
from openai import OpenAI

logger.add("vision.log", encoding="utf-8", enqueue=True)


def describe_screen_interactions(screenshot_b64: str) -> str:
    data_url = f"data:image/png;base64,{screenshot_b64}"

    messages: list[dict[str, Any]] = [
        {
            "role": "user",
            "content": [
                {
                    "type": "text",
                    "text": "List every clickable element on the screen with a description and the coordinate of its center to tap on it using adb. The dimensions of the screen is 720 wide x1616 high. Top left is the origin. coordinates are in pixels, x then y",
                },
                {
                    "type": "image_url",
                    "image_url": {"url": data_url},
                },
            ],
        }
    ]
    try:
        logger.info("Connecting to client")
        client = OpenAI(base_url="http://127.0.0.1:1234/v1", api_key="abcd")
        logger.info("Client created")
        response = client.chat.completions.create(
            model="se-gui-7b",
            messages=messages,
        )
        logger.info(response)
        description = response.choices[0].message.content
    except Exception as e:
        logger.error(f"Error: {e}")

    return description.strip()
