# src/conversation_engine.py
import os
import re
from dotenv import load_dotenv
from langchain_community.vectorstores import FAISS
from langchain_community.embeddings import GPT4AllEmbeddings
from langchain.chains import RetrievalQA
from langchain.prompts import PromptTemplate
from langchain_groq import ChatGroq
from typing import Optional, List, Mapping, Any
from src.prompts import QA_PROMPT, SIMPLE_PROMPT
from src.global_settings import VECTOR_DB_PATH, EMBEDDING_MODEL_FILE

# Load biến môi trường từ file .env
load_dotenv()

class ConversationEngine:
    def __init__(self):
        print("Đang khởi tạo ConversationEngine...")
        api_key = os.getenv("GROQ_API_KEY")
        if not api_key:
            raise ValueError("GROQ_API_KEY không được tìm thấy. Kiểm tra tệp .env.")
        print("GROQ_API_KEY:", api_key[:10] + "..." if api_key else "None")
        self.llm = ChatGroq(
            api_key=api_key,
            model="llama3-8b-8192",
            temperature=0.01,
            max_tokens=1024
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

    def clean_response(self, text: str) -> str:
        """Làm sạch phản hồi, loại bỏ ký tự không mong muốn."""
        text = re.sub(r'<\|im_(start|end)\|>', '', text)
        text = text.strip()
        return text

    def process_direct_query(self, user_input):
        """Xử lý câu hỏi trực tiếp từ người dùng dựa trên tài liệu PDF."""
        try:
            response = self.qa_chain.invoke({"query": user_input})
            answer = self.clean_response(response.get("result", "Không tìm thấy thông tin phù hợp trong tài liệu."))
            disclaimer = "*(Lưu ý: Tôi là chatbot hỗ trợ tâm lý, không phải bác sĩ. Nếu cần, hãy liên hệ chuyên gia tâm lý.)*"
            return {
                "response": f"{answer}\n\n{disclaimer}",
                "question": None,
                "options": []
            }
        except Exception as e:
            print(f"Lỗi khi xử lý câu hỏi trực tiếp: {str(e)}")
            return {
                "response": f"Lỗi khi xử lý câu hỏi: {str(e)}\n\n*(Lưu ý: Tôi là chatbot hỗ trợ tâm lý, không phải bác sĩ. Nếu cần, hãy liên hệ chuyên gia tâm lý.)*",
                "question": None,
                "options": []
            }

    def generate_question(self, user_input):
        """Sinh câu hỏi trắc nghiệm tâm lý dựa trên đầu vào của người dùng."""
        question_template = (
            "Dựa trên tài liệu tâm lý học, hãy tạo một câu hỏi trắc nghiệm CHÍNH XÁC về chủ đề '{user_input}' với 5 lựa chọn từ 'Không bao giờ' đến 'Luôn luôn'. "
            "Yêu cầu:\n"
            "1. Câu hỏi phải trực tiếp liên quan đến từ khóa '{user_input}'\n"
            "2. Câu hỏi phải có cấu trúc rõ ràng, ngắn gọn (dưới 25 từ), và mang tính chuyên môn tâm lý học\n"
            "3. Sử dụng thuật ngữ chuyên ngành tâm lý nếu phù hợp\n"
            "4. Câu hỏi PHẢI kết thúc bằng dấu '?'\n"
            "5. Câu hỏi phải giúp đánh giá trạng thái tâm lý người dùng\n"
            "Nếu không tìm thấy thông tin liên quan, hãy tạo câu hỏi dựa trên kiến thức tâm lý học cơ bản về '{user_input}'."
        )
        try:
            response = self.qa_chain.invoke({"query": question_template.format(user_input=user_input)})
            question_text = self.clean_response(response.get("result", "Bạn có cảm thấy thoải mái với trạng thái tâm lý hiện tại?"))
            
            # Đảm bảo câu hỏi kết thúc bằng dấu hỏi
            if not question_text.endswith("?"):
                question_text += "?"
                
            # Kiểm tra và cắt bớt nếu câu hỏi quá dài
            if len(question_text.split()) > 30:
                sentences = question_text.split(".")
                question_text = sentences[0] + "?"
            
            # Đảm bảo câu hỏi có chứa từ khóa hoặc liên quan đến input
            keywords = user_input.lower().split()
            if not any(keyword in question_text.lower() for keyword in keywords):
                question_text = f"Mức độ bạn cảm thấy {user_input} trong cuộc sống hàng ngày?"
                
            return {
                "question": question_text,
                "options": ["1 - Không bao giờ", "2 - Hiếm khi", "3 - Đôi khi", "4 - Thường xuyên", "5 - Luôn luôn"],
                "response": "Hãy chọn mức độ phù hợp với bạn!"
            }
        except Exception as e:
            print(f"Lỗi khi sinh câu hỏi: {str(e)}")
            return {
                "question": f"Mức độ bạn cảm thấy {user_input} trong cuộc sống hàng ngày?",
                "options": ["1 - Không bao giờ", "2 - Hiếm khi", "3 - Đôi khi", "4 - Thường xuyên", "5 - Luôn luôn"],
                "response": "Hãy chọn mức độ phù hợp với bạn!"
            }

    def process_answer(self, user_input, question, answer):
        """Xử lý câu trả lời trắc nghiệm và tạo phản hồi chuyên sâu dựa trên tài liệu."""
        emotion = self.detect_emotion(user_input)
        answer_value = answer.split(" - ")[0]  # Lấy giá trị số
        
        try:
            response_template = (
                f"Bạn là một chuyên gia tâm lý. Một người đã trả lời '{answer}' cho câu hỏi '{question}'. "
                f"Hãy phân tích câu trả lời này một cách chuyên sâu dựa trên tài liệu tâm lý học. "
                f"Phản hồi phải:"
                f"\n1. Giải thích ý nghĩa của việc chọn mức {answer_value} (từ 1-5)"
                f"\n2. Đưa ra nhận định tâm lý dựa trên sự lựa chọn này"
                f"\n3. Đề xuất 2-3 phương pháp hoặc hoạt động cụ thể để cải thiện tình trạng"
                f"\n4. Phù hợp với cảm xúc '{emotion}' của người dùng"
                f"\n5. Sử dụng ngôn ngữ đồng cảm, tôn trọng nhưng chuyên nghiệp"
                f"\nPhản hồi phải ngắn gọn, có cấu trúc rõ ràng và có giá trị thực tiễn."
            )
            response = self.qa_chain.invoke({"query": response_template})
            response_text = self.clean_response(response.get("result", "Cảm ơn bạn đã chia sẻ! Tôi ở đây để hỗ trợ bạn."))
            
            # Kiểm tra và đảm bảo phản hồi chất lượng
            if len(response_text) < 50 or "không tìm thấy thông tin" in response_text.lower():
                # Sử dụng phản hồi dự phòng nếu phản hồi không đạt yêu cầu
                response_text = self.generate_fallback_response(question, answer, emotion)
                
            greeting = self.get_emotion_greeting(emotion)
            disclaimer = "*(Lưu ý: Tôi là chatbot hỗ trợ tâm lý, không phải bác sĩ. Nếu cần, hãy liên hệ chuyên gia tâm lý.)*"
            return f"{greeting}\n\n{response_text}\n\n{disclaimer}"
        except Exception as e:
            print(f"Lỗi khi xử lý câu trả lời: {str(e)}")
            return self.generate_response(emotion, question, answer)
            
    def generate_fallback_response(self, question, answer, emotion):
        """Tạo phản hồi dự phòng chất lượng khi phản hồi API không đạt yêu cầu."""
        answer_value = int(answer.split(" - ")[0])
        response = ""
        
        if answer_value <= 2:  # Mức thấp (1-2)
            response = f"Với mức {answer_value}, có thể bạn ít khi trải qua vấn đề được đề cập trong câu hỏi. "
            response += "Đây có thể là dấu hiệu tích cực về sức khỏe tâm lý của bạn trong khía cạnh này. "
            response += "Để duy trì, bạn có thể tập trung vào: (1) Ghi nhận và trân trọng những điểm mạnh này, "
            response += "(2) Tiếp tục các hoạt động tích cực hiện tại, và (3) Chia sẻ kinh nghiệm với những người xung quanh."
        elif answer_value == 3:  # Mức trung bình
            response = f"Với mức {answer_value}, bạn đôi khi gặp phải vấn đề được đề cập. "
            response += "Đây là mức độ phổ biến và có thể cải thiện thông qua một số phương pháp đơn giản. "
            response += "Gợi ý cho bạn: (1) Xác định các yếu tố kích hoạt cụ thể, (2) Thực hành các kỹ thuật thư giãn như hít thở sâu, "
            response += "và (3) Dành thời gian cho các hoạt động bạn yêu thích để cân bằng cảm xúc."
        else:  # Mức cao (4-5)
            response = f"Với mức {answer_value}, bạn khá thường xuyên trải qua vấn đề được đề cập. "
            response += "Điều này có thể gây ảnh hưởng đến cuộc sống hàng ngày và đáng được quan tâm. "
            response += "Một số gợi ý: (1) Thử thiết lập thói quen ghi nhật ký cảm xúc để theo dõi, "
            response += "(2) Học và thực hành các kỹ thuật quản lý cảm xúc như thiền mindfulness, "
            response += "và (3) Cân nhắc tham khảo ý kiến chuyên gia nếu tình trạng kéo dài."
            
        return response

    def detect_emotion(self, user_input):
        """Phát hiện cảm xúc nâng cao từ đầu vào người dùng."""
        user_input = user_input.lower()
        
        # Danh sách từ khóa cảm xúc chi tiết hơn cho tiếng Việt
        emotions = {
            "sad": ["buồn", "chán", "mệt mỏi", "khó chịu", "tuyệt vọng", "thất vọng", "cô đơn", "trống rỗng", 
                    "đau khổ", "chán nản", "bế tắc", "không vui", "sầu", "nhớ nhung", "trầm cảm"],
                    
            "happy": ["vui", "hạnh phúc", "phấn khởi", "hài lòng", "tích cực", "phấn chấn", "thoải mái", 
                     "hứng thú", "hào hứng", "vui vẻ", "yêu đời", "thích thú", "mãn nguyện", "tự tin"],
                     
            "anxious": ["lo âu", "lo lắng", "sợ", "hồi hộp", "hoảng sợ", "bồn chồn", "bất an", "hoang mang", 
                       "nghi ngờ", "dao động", "phiền muộn", "lo nghĩ", "băn khoăn", "sợ hãi", "hồi hộp"],
                       
            "stressed": ["stress", "áp lực", "căng thẳng", "quá tải", "bức xúc", "căng thẳng", "mệt mỏi", 
                        "kiệt sức", "bực bội", "khó chịu", "ngột ngạt", "quá độ", "ngột ngạt", "nghẹt thở"],
                        
            "angry": ["tức giận", "bực tức", "cáu", "giận dữ", "nổi nóng", "phẫn nộ", "tức tối", 
                     "khó chịu", "cau có", "bực mình", "gắt gỏng", "khó chịu", "cáu kỉnh"],
                     
            "confused": ["bối rối", "lúng túng", "phân vân", "không hiểu", "mơ hồ", "rối trí", "mông lung", 
                        "rối rắm", "không rõ", "không chắc", "nghi ngờ", "khó hiểu"]
        }
        
        # Đếm số từ khóa khớp cho mỗi cảm xúc
        emotion_scores = {}
        for emotion, keywords in emotions.items():
            score = sum(1 for word in keywords if word in user_input)
            if score > 0:
                emotion_scores[emotion] = score
        
        # Nếu có khớp, chọn cảm xúc có nhiều từ khóa phù hợp nhất
        if emotion_scores:
            return max(emotion_scores, key=emotion_scores.get)
            
        # Thử phân tích cấu trúc câu nếu không có từ khóa rõ ràng
        if "tôi không" in user_input or "tôi chẳng" in user_input:
            return "sad"  # Phủ định thường gắn với cảm xúc tiêu cực
        
        if "?" in user_input and ("làm sao" in user_input or "tại sao" in user_input):
            return "confused"  # Câu hỏi có thể chỉ sự bối rối
            
        if "!" in user_input:
            return "stressed"  # Dấu chấm than có thể chỉ cảm xúc mạnh
            
        # Mặc định nếu không phát hiện được
        return "neutral"

    def get_emotion_greeting(self, emotion):
        """Tạo lời chào dựa trên cảm xúc."""
        if emotion == "sad":
            return "Tôi hiểu cảm giác buồn có thể khó khăn, nhưng bạn thật mạnh mẽ khi chia sẻ!"
        elif emotion == "happy":
            return "Năng lượng tích cực của bạn thật tuyệt! Hãy cùng tìm hiểu thêm nhé."
        elif emotion == "anxious":
            return "Cảm ơn bạn đã mở lòng. Chúng ta sẽ cùng làm mọi thứ nhẹ nhàng hơn."
        elif emotion == "stressed":
            return "Áp lực là bình thường, và bạn đang làm rất tốt khi đối mặt!"
        else:
            return "Cảm ơn bạn đã chia sẻ! Tôi ở đây để hỗ trợ bạn."

    def generate_response(self, emotion, question, answer):
        """Tạo phản hồi dự phòng khi truy vấn tài liệu thất bại."""
        greeting = self.get_emotion_greeting(emotion)
        problem = f"**Vấn đề**: Câu hỏi '{question}' cho thấy bạn đang suy ngẫm về cảm xúc ở mức độ {answer.lower()}. Mỗi người có trải nghiệm riêng, và điều này rất bình thường."
        agitate = f"**Cảm nhận**: Khi chọn '{answer}', có thể bạn đang chú ý đến một khía cạnh tâm lý cần quan tâm. Những cảm xúc này đôi khi khiến ta tự hỏi liệu mình có ổn không, và điều đó hoàn toàn dễ hiểu."
        solution = f"**Gợi ý**: Hãy thử dành thời gian suy ngẫm hoặc chia sẻ với ai đó bạn tin tưởng. Các hoạt động như viết nhật ký, thiền, hoặc đi bộ có thể giúp. Nếu muốn, tôi có thể đưa ra thêm câu hỏi để khám phá sâu hơn."
        disclaimer = "*(Lưu ý: Tôi là chatbot hỗ trợ tâm lý, không phải bác sĩ. Nếu cần, hãy liên hệ chuyên gia tâm lý.)*"
        return f"{greeting}\n\n{problem}\n\n{agitate}\n\n{solution}\n\n{disclaimer}"