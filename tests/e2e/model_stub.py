"""Local OpenAI-compatible model stub. Used only by docker-compose.smoke.yml."""
import json
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer


class Handler(BaseHTTPRequestHandler):
    def do_POST(self):
        payload = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
        assert payload["messages"]
        result = json.dumps({"summary": "推荐番茄炒蛋，符合家庭口味。", "recognized_ingredients": [], "recommendations": [{"dish_name": "番茄炒蛋", "rating": 5, "required_ingredients": ["番茄", "鸡蛋"], "matched_ingredients": [], "steps": [], "reason": "结合家庭菜品、偏好和历史用餐。"}]}, ensure_ascii=False)
        self.send_response(200)
        self.send_header("Content-Type", "text/event-stream")
        self.end_headers()
        for index in range(0, len(result), 8):
            chunk = {"id": "test-completion", "object": "chat.completion.chunk", "created": int(time.time()), "model": "test-model", "choices": [{"index": 0, "delta": {"content": result[index:index+8]}, "finish_reason": None}]}
            self.wfile.write(("data: " + json.dumps(chunk, ensure_ascii=False) + "\n\n").encode())
            self.wfile.flush()
        self.wfile.write(b"data: [DONE]\n\n")
        self.wfile.flush()


ThreadingHTTPServer(("0.0.0.0", 8080), Handler).serve_forever()
