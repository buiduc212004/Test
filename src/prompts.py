# src/prompts.py
QA_PROMPT = """<|im_start|>system
Sử dụng thông tin sau để trả lời câu hỏi. Nếu không biết, hãy nói không biết, đừng tạo câu trả lời.
{context}<|im_end|>
<|im_start|>user
{question}<|im_end|>
<|im_start|>assistant"""

SIMPLE_PROMPT = """<|im_start|>system
Bạn là một trợ lý AI tâm lý học. Hãy trả lời chính xác và đồng cảm.
<|im_end|>
<|im_start|>user
{question}<|im_end|>
<|im_start|>assistant"""