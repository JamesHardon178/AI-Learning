def get_weather(city: str):
    return f"{city}今天晴，27℃"


weather_tool = {
    "name": "get_weather",
    "description": "查询指定城市的天气",
    "parameters": {
        "type": "object",
        "properties": {
            "city": {
                "type": "string"
            }
        },
        "required": ["city"]
    }
}

print(weather_tool)