# src/conversation_engine.py
import os
from dotenv import load_dotenv
from langchain_community.vectorstores import FAISS
from langchain_community.embeddings import GPT4AllEmbeddings
from langchain.chains import RetrievalQA
from langchain.prompts import PromptTemplate
from langchain_groq import ChatGroq  # Sử dụng ChatGroq từ langchain_groq
from typing import Optional, List, Mapping, Any
from src.prompts import QA_PROMPT, SIMPLE_PROMPT
from src.global_settings import VECTOR_DB_PATH, EMBEDDING_MODEL_FILE

# Load biến môi trường từ file .env
load_dotenv()

class ConversationEngine:
    def __init__(self):
        print("Đang khởi tạo ConversationEngine...")
        # Khởi tạo ChatGroq với API Key từ biến môi trường
        self.llm = ChatGroq(
            api_key=os.getenv("GROQ_API_KEY"),
            model="llama3-8b-8192",  # Chọn mô hình của Groq
            temperature=0.01,
            max_tokens=512
        )
        print("Đã khởi tạo LLM với Groq API")
        self.db = self.load_vector_db()
        print("Đã tải Vector DB")
        self.qa_chain = self.create_qa_chain()
        self.simple_chain = self.create_simple_chain()

    def load_vector_db(self):
        try:
            embedding_model = GPT4AllEmbeddings(model_file=EMBEDDING_MODEL_FILE)
            return FAISS.load_local(VECTOR_DB_PATH, embedding_model, allow_dangerous_deserialization=True)
        except Exception as e:
            raise RuntimeError(f"Lỗi khi tải Vector DB: {str(e)}. Kiểm tra thư mục {VECTOR_DB_PATH} và file mô hình {EMBEDDING_MODEL_FILE}.")

    def create_qa_chain(self):
        prompt = PromptTemplate(template=QA_PROMPT, input_variables=["context", "question"])
        return RetrievalQA.from_chain_type(
            llm=self.llm,
            chain_type="stuff",
            retriever=self.db.as_retriever(search_kwargs={"k": 3}, max_token_limit=1024),
            return_source_documents=False,
            chain_type_kwargs={'prompt': prompt}
        )

    def create_simple_chain(self):
        prompt = PromptTemplate(template=SIMPLE_PROMPT, input_variables=["question"])
        return prompt | self.llm

    def generate_question(self, user_input):
        question_template = (
            "Dựa trên tài liệu, tạo một câu hỏi trắc nghiệm về tâm lý với 5 lựa chọn mức độ từ 'Không bao giờ' đến 'Luôn luôn' liên quan đến '{user_input}'. "
            "Câu hỏi phải cụ thể, đồng cảm, và phù hợp với vai trò bác sĩ tâm lý học. Nếu không tìm thấy thông tin liên quan, trả về câu hỏi chung về trạng thái tâm lý."
        )
        try:
            response = self.qa_chain.invoke({"query": question_template.format(user_input=user_input)})
            question_text = response.get("result", "Bạn có cảm thấy thoải mái với trạng thái tâm lý hiện tại?").strip()
            if not question_text.endswith("?"):
                question_text += "?"
            return {
                "question": question_text,
                "options": ["1 - Không bao giờ", "2 - Hiếm khi", "3 - Đôi khi", "4 - Thường xuyên", "5 - Luôn luôn"]
            }
        except Exception as e:
            print(f"Lỗi khi sinh câu hỏi: {str(e)}")
            return {
                "question": "Bạn có cảm thấy thoải mái với trạng thái tâm lý hiện tại?",
                "options": ["1 - Không bao giờ", "2 - Hiếm khi", "3 - Đôi khi", "4 - Thường xuyên", "5 - Luôn luôn"]
            }

    def process_answer(self, user_input, question, answer):
        emotion = self.detect_emotion(user_input)
        return self.generate_response(emotion, question, answer)

    def detect_emotion(self, user_input):
        user_input = user_input.lower()
        if any(word in user_input for word in ["buồn", "chán", "mệt mỏi", "khó chịu"]):
            return "sad"
        elif any(word in user_input for word in ["vui", "hạnh phúc", "phấn khởi"]):
            return "happy"
        elif any(word in user_input for word in ["lo âu", "lo lắng", "sợ", "hồi hộp"]):
            return "anxious"
        elif any(word in user_input for word in ["stress", "áp lực", "căng thẳng"]):
            return "stressed"
        return "neutral"

    def generate_response(self, emotion, question, answer):
        if emotion == "sad":
            greeting = "Tôi hiểu cảm giác buồn có thể khó khăn, nhưng bạn thật mạnh mẽ khi chia sẻ!"
        elif emotion == "happy":
            greeting = "Năng lượng tích cực của bạn thật tuyệt! Hãy cùng tìm hiểu thêm nhé."
        elif emotion == "anxious":
            greeting = "Cảm ơn bạn đã mở lòng. Chúng ta sẽ cùng làm mọi thứ nhẹ nhàng hơn."
        elif emotion == "stressed":
            greeting = "Áp lực là bình thường, và bạn đang làm rất tốt khi đối mặt!"
        else:
            greeting = "Cảm ơn bạn đã chia sẻ! Tôi ở đây để hỗ trợ bạn."

        problem = f"**Vấn đề**: Câu hỏi '{question}' cho thấy bạn đang suy ngẫm về cảm xúc ở mức độ {answer.lower()}. Mỗi người có trải nghiệm riêng, và điều này rất bình thường."
        agitate = f"**Cảm nhận**: Khi chọn '{answer}', có thể bạn đang chú ý đến một khía cạnh tâm lý cần quan tâm. Những cảm xúc này đôi khi khiến ta tự hỏi liệu mình có ổn không, và điều đó hoàn toàn dễ hiểu."
        solution = f"**Gợi ý**: Hãy thử dành thời gian suy ngẫm hoặc chia sẻ với ai đó bạn tin tưởng. Các hoạt động như viết nhật ký, thiền, hoặc đi bộ có thể giúp. Nếu muốn, tôi có thể đưa ra thêm câu hỏi để khám phá sâu hơn."
        disclaimer = "*(Lưu ý: Tôi là chatbot hỗ trợ tâm lý, không phải bác sĩ. Nếu cần, hãy liên hệ chuyên gia tâm lý.)*"

        return f"{greeting}\n\n{problem}\n\n{agitate}\n\n{solution}\n\n{disclaimer}"